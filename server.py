import json
import shutil
import requests as requests_lib
import platform
from flask import Flask
from flask import request
from flask_cors import CORS
from datetime import datetime
import time
import logging
import query_params

from PIL import Image
from io import BytesIO
import base64

# set up logging for server
log = logging.getLogger("server")
log.setLevel(logging.INFO)

# load intent model
from intent import IntentRecognition

# import ditto database handler
from database.db import DittoDB

# import ditto image rag agent
from modules.image_rag import DittoImageRAG

# import ditto memory agent
from ditto_memory import DittoMemory


import os

# load intent model
intent_model = IntentRecognition(train=False)

# load ditto memory langchain agent
log.info("[Loading Ditto Memory...]")
ditto = DittoMemory()

# load ditto database handler
log.info("[Loading Ditto Database Handler...]")
ditto_db = DittoDB()

# load ditto image rag agent
log.info("[Loading Ditto Image RAG Agent...]")
ditto_image_rag = DittoImageRAG()


# set Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# set OS variable
OS = "Windows"
if platform.system() == "Linux":
    OS = "Linux"
elif platform.system() == "Darwin":
    OS = "Darwin"

# load users.json and copy example_users.json if users.json does not exist
USERS = None

if not os.path.exists("users.json"):
    log.info("users.json does not exist. Copying example_users.json...")
    shutil.copyfile("example_users.json", "users.json")
    log.info(
        "Please fill out users.json with your user information and restart the server."
    )
    exit()
else:  # load users.json
    log.info("Loading users.json...")
    with open("users.json") as f:
        USERS = json.load(f)
        log.info("users.json loaded.")


def get_user_obj(user_id):
    with open("users.json") as f:
        USERS = json.load(f)
    for user in USERS["users"]:
        if user["user_id"] == user_id:
            return user
    return None


def update_user_obj_ditto_ip(user_id, new_ditto_unit_ip):
    global USERS
    for user_ndx, user in enumerate(USERS["users"]):
        if user["user_id"] == user_id:
            USERS["users"][user_ndx]["ditto_unit_ip"] = new_ditto_unit_ip
            return USERS
    return None


def update_and_write_user_obj(new_user_obj):
    with open("users.json", "w") as f:
        json.dump(new_user_obj, f, indent=4)


def get_ditto_unit_on_bool(user_id="ditto"):
    try:
        user_obj = get_user_obj(user_id)
        ditto_unit_ip = user_obj["ditto_unit_ip"]
        ditto_unit_port = user_obj["ditto_unit_port"]
        res = requests_lib.get(
            f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto/?status=1",
            timeout=30,
        )
        res = json.loads(str(res.content.decode().strip()))
        status = res["status"]
        # log.info(f"Ditto unit status: {status}")
    except BaseException as e:
        # log.error(e)
        # log.info("Ditto unit is off")
        status = "off"
    ditto_unit_off = True if status == "off" else False
    ditto_unit_on = True if not ditto_unit_off else False
    return ditto_unit_on


def send_prompt_to_ditto_unit(user_id, prompt):
    try:
        user_obj = get_user_obj(user_id)
        ditto_unit_ip = user_obj["ditto_unit_ip"]
        ditto_unit_port = user_obj["ditto_unit_port"]
        requests_lib.post(
            f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto/?prompt={prompt}",
            timeout=30,
        )
        log.info(f"sent prompt to ditto unit: {prompt}")
    except BaseException as e:
        log.error(e)
        log.info("Ditto unit is off")


def send_prompt_to_llm(user_id, prompt, face_name="none"):
    log.info(f"sending user: {user_id} prompt to memory agent: {prompt}")
    response = ditto.prompt(prompt, user_id, face_name)
    return json.dumps({"response": response})


# Makes requests to the ditto image rag agent
@app.route("/users/<user_id>/image_rag", methods=["POST"])
def image_rag(user_id: str):
    requests = request.args
    if "prompt" not in requests:
        return ErrMissingQuery("prompt")
    if "mode" not in requests:
        return ErrMissingQuery("mode")
    if "image" not in request.files:
        return ErrMissingFile("image")
    try:
        prompt = requests["prompt"]
        mode = requests["mode"]
        image = request.files["image"].read()
        if mode == "caption":
            image_rag_response = ditto_image_rag.prompt(
                prompt, image, caption_image=True
            )
        elif mode == "qa":
            image_rag_response = ditto_image_rag.prompt(
                prompt, image, caption_image=False
            )
        else:
            return ErrException(f"Invalid mode: {mode}")

        # get stamp for memory stores
        stamp = str(datetime.utcfromtimestamp(time.time()))
        mem_query = f"Timestamp: {stamp}\n{prompt}"

        # save prompt and response to long term memory vector store
        ditto.save_new_memory(
            prompt=mem_query,
            response=image_rag_response,
            user_id=user_id,
        )

        # save prompt and response to short term memory vector store
        ditto.short_term_mem_store.save_response_to_stmem(
            user_id=user_id, query=mem_query, response=image_rag_response
        )

        return json.dumps({"response": image_rag_response})

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# Makes requests to the ditto memory langchain agent
@app.route("/users/<user_id>/prompt_llm", methods=["POST", "GET"])
def prompt_llm(user_id: str):
    requests = request.args
    try:
        if "prompt" not in requests:
            return ErrMissingQuery("prompt")
        if "face_name" not in requests:
            face_name = "none"
        else:
            face_name = requests["face_name"]
        prompt = requests["prompt"]

        response = send_prompt_to_llm(user_id, prompt, face_name)

        return response

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route(
    "/users/<email>/conversations/<conv_idx>/prompt",
    methods=["POST"],
)
def post_prompt(email: str, conv_idx: int):
    try:
        user_id = ditto_db.get_create_user_id(email)
        conv_idx = int(conv_idx)
        conv_id = ditto_db.get_create_conv_id(user_id, conv_idx)
        target = request.args["target"].lower()
        if target is None:
            target = "cloud"
        if target not in ["cloud", "ditto"]:
            return ErrInvalidQuery("target", target)
        log.debug(f"prompt email: {email}, conv_id: {conv_id} target: {target}")
        body = request.get_json()
        prompt = body["prompt"]
        if prompt is None or prompt == "":
            return ErrMissingBody("prompt")
        ditto_db.save_prompt(user_id, conv_id, prompt)

        # if ditto unit is on, send prompt to ditto unit
        if target == "ditto" and get_ditto_unit_on_bool(user_id):
            return prompt_ditto(user_id, conv_id, prompt)
        else:
            return prompt_cloud(user_id, conv_id, prompt)

    except BaseException as e:
        log.error(e)
        return ErrException(e)


def prompt_cloud(user_id: int, conv_id: int, prompt: str):
    log.debug(f"ditto unit is off. sending prompt to memory agent: {prompt}")
    response = json.loads(send_prompt_to_llm(user_id, prompt))["response"]
    ditto_db.save_response(user_id, conv_id, response)
    return ditto_db.get_chat_latest(user_id, conv_id)


def prompt_ditto(user_id: int, conv_id: int, prompt: str):
    log.debug(f"sending prompt to ditto unit: {prompt}")
    # ditto unit will write prompt and response to database
    send_prompt_to_ditto_unit(user_id, prompt)
    # return '{"response": "success"}'
    return ditto_db.get_chat_latest(user_id, conv_id)


@app.route("/users/<user_id>/reset_memory", methods=["POST", "GET"])
def reset_memory(user_id: str):
    try:
        log.info(f"resetting ditto's long and short-term memory for user: {user_id}")
        ditto.reset_memory(user_id)
        ditto.short_term_mem_store.reset_stmem(user_id)
        log.info(f"resetting prompt and response history for user: {user_id}")
        ditto_db.new_conversation(user_id)
        return '{"action": "reset_memory", "status": "ok"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# endpoint to mute ditto unit's mic
@app.route("/users/<user_id>/mute_ditto_mic", methods=["POST", "GET"])
def mute_ditto_mic(user_id: str):
    try:
        user_obj = get_user_obj(user_id)
        ditto_unit_ip = user_obj["ditto_unit_ip"]
        ditto_unit_port = user_obj["ditto_unit_port"]
        log.info(f"toggling ditto unit's mic for user: {user_id}")
        res1 = requests_lib.post(
            f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto/?toggleMic=1",
            timeout=30,
        )
        time.sleep(0.3)
        # toggle ditto eyes too
        res2 = requests_lib.post(
            f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto/?prompt=toggleEyes",
            timeout=30,
        )
        return str(res1.content.decode().strip())

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# endpoint to change user's ditto unit ip
@app.route("/users/<user_id>/update_ditto_unit_ip", methods=["POST", "GET"])
def update_ditto_unit_ip(user_id: str):
    requests = request.args
    try:
        if "ditto_unit_ip" not in requests:
            return ErrMissingQuery("ditto_unit_ip")

        # get user's ditto unit ip from request
        ditto_unit_ip = requests["ditto_unit_ip"]

        log.info(f"updating ditto unit ip for user: {user_id}")

        # update user's ditto unit ip in users.json
        new_user_obj = update_user_obj_ditto_ip(user_id, ditto_unit_ip)
        update_and_write_user_obj(new_user_obj)

        return '{"response": "success"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/write_prompt", methods=["POST", "GET"])
def write_prompt(user_id: str):
    requests = request.args
    try:
        if "prompt" not in requests:
            return ErrMissingQuery("prompt")

        # get user's prompt from request
        prompt = requests["prompt"]

        log.info(f"saving ditto unit prompt to database.")

        # save prompt to database
        ditto_db.save_prompt(user_id, prompt)

        return '{"response": "success"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/write_response", methods=["POST", "GET"])
def write_response(user_id: str):
    requests = request.args
    try:
        if "response" not in requests:
            return ErrMissingQuery("response")

        # get user's prompt from request
        response = requests["response"]

        log.info(f"saving ditto unit response to database.")

        # save prompt to database
        ditto_db.save_response(user_id, response)

        return '{"response": "success"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<email>/conversations", methods=["GET"])
def get_conversations(email: str):
    try:
        user_id = ditto_db.get_create_user_id(email)
        args = query_params.ReqQuery(request.args)
        offset = args.offset()
        limit = args.limit()
        is_asc = args.is_asc_order()
        log.debug(
            f"getting conversations for user: {user_id} offset: {offset}, limit: {limit}, is_asc: {is_asc}"
        )
        return ditto_db.get_conversations(user_id, offset, limit, is_asc)
    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<email>/conversations/<conv_idx>", methods=["GET"])
def get_chats(email: str, conv_idx: int):
    try:
        user_id = ditto_db.get_create_user_id(email)
        conv_idx = int(conv_idx)
        conv_id = ditto_db.get_create_conv_id(user_id, conv_idx)
        args = query_params.ReqQuery(request.args)
        offset = args.offset()
        limit = args.limit()
        is_asc = args.is_asc_order()
        log.debug(
            f"getting chats for user: {user_id}, conv_id: {conv_id} offset: {offset}, limit: {limit}, is_asc: {is_asc}"
        )
        return ditto_db.get_chats(user_id, conv_id, offset, limit, is_asc)
    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/get_prompt_response_count", methods=["GET"])
def get_prompt_response_count(user_id: str):
    try:
        count = ditto_db.get_prompt_response_count(user_id)
        return '{"historyCount": %d}' % count
    except BaseException as e:
        # log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/get_conversation_history", methods=["GET"])
def get_conversation_history(user_id: str):
    try:
        prompts, responses = ditto_db.get_conversation_history(user_id)
        return '{"prompts": %s, "responses": %s}' % (prompts, responses)
    except BaseException as e:
        # log.error(e)
        return ErrException(e)


# endpoint to get ditto unit status
@app.route("/users/<user_id>/get_ditto_unit_status", methods=["GET"])
def get_ditto_unit_status(user_id: str):
    try:
        ditto_unit_on = get_ditto_unit_on_bool(user_id)
        status = "on" if ditto_unit_on else "off"
        return '{"status": "%s"}' % status
    except BaseException as e:
        # log.error(e)
        return ErrException(e)


# endpoint to get ditto unit's mic status
@app.route("/users/<user_id>/get_ditto_mic_status", methods=["GET"])
def get_ditto_mic_status(user_id: str):
    try:
        user_obj = get_user_obj(user_id)
        ditto_unit_ip = user_obj["ditto_unit_ip"]
        ditto_unit_port = user_obj["ditto_unit_port"]
        ditto_unit_on = get_ditto_unit_on_bool(user_id)
        if ditto_unit_on:
            res = requests_lib.get(
                f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto?dittoMicStatus=1",
                timeout=30,
            )
            res = json.loads(str(res.content.decode().strip()))
            status = res["ditto_mic_status"]
            # log.info(f"Ditto unit mic status: {status}")
        else:
            status = "off"
            # log.info("Ditto unit is off")
    except BaseException as e:
        # log.error(e)
        # log.info("Ditto unit is off")
        status = "off"
    return '{"ditto_mic_status": "%s"}' % status


# Makes requests to the intent model
@app.route("/intent", methods=["POST"])
def intent_handler():
    requests = request.args
    try:
        # Request to send prompt to ditto
        if "prompt" not in requests:
            return ErrMissingQuery("prompt")
        prompt = requests["prompt"]
        log.info(f"sending prompt to intent model: {prompt}")
        intent = intent_model.prompt(prompt)
        return intent

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# making requests to a NER model
# TODO: remove entity_id and break into separate endpoints
@app.route("/ner/<entity_id>", methods=["POST"])
def ner_handler(entity_id: str):
    requests = request.args
    if "prompt" not in requests:
        return ErrMissingQuery("prompt")
    prompt = requests["prompt"]
    ner_response = '{"response:" "None"}'
    try:
        match entity_id:
            case "timer":
                log.info("sending request to ner-timer")
                ner_response = intent_model.prompt_ner_timer(prompt)

            case "light":
                log.info("sending request to ner_light")
                ner_response = intent_model.prompt_ner_light(prompt)

            case "numeric":
                log.info("sending request to ner_numeric")
                ner_response = intent_model.prompt_ner_numeric(prompt)

            case "play":
                log.info("sending request to ner_play")
                ner_response = intent_model.prompt_ner_play(prompt)

            case "name":
                log.info("sending request to ner_name")
                ner_response = intent_model.prompt_ner_name(prompt)

        log.info(ner_response)
        return ner_response

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/status", methods=["GET"])
def status_handler():
    return '{"status": "on"}'


class Server:
    def __init__(self):
        self.app = app


if __name__ == "__main__":
    server = Server()
    # app.run(port='32032', host='0.0.0.0')


# def ErrWrongMethod(method: str, should_be="POST"):
#     return '{"error": "request method is %s but should be %s"}' % method, should_be


def ErrMissingFile(file: str):
    return '{"error": "missing file %s"}' % file


def ErrMissingQuery(key: str):
    return '{"error": "missing query param %s"}' % key


def ErrMissingBody(key: str):
    return '{"error": "missing body param %s"}' % key


def ErrInvalidQuery(key: str, val: str):
    return '{"error": "invalid query param %s: %s"}' % (key, val)


def ErrException(e: BaseException):
    return '{"error": "%s"}' % e
