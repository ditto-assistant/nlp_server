import json
import shutil
import requests as requests_lib
from ditto_memory import DittoMemory
import platform
from flask import Flask
from flask import request
from flask_cors import CORS
import logging

from PIL import Image
from io import BytesIO
import base64

# set up logging for server
log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO)

# load intent model
from intent import IntentRecognition

# import ditto database handler
from database.db import DittoDB

# import ditto image rag agent
from modules.image_rag import DittoImageRAG

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
    for user in USERS["users"]:
        if user["user_id"] == user_id:
            return user
    return None


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
        log.error(e)
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


def send_prompt_to_llm(user_id, prompt):
    log.info(f"sending user: {user_id} prompt to memory agent: {prompt}")
    response = ditto.prompt(prompt, user_id)

    return json.dumps({"response": response})


# Makes requests to the ditto image rag agent
### TODO: finish implementing this endpoint...
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
        prompt = requests["prompt"]

        response = send_prompt_to_llm(user_id, prompt)

        return response

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route(
    "/users/<user_id>/conversations/<conv_idx>/prompt",
    methods=["POST"],
)
def post_prompt(user_id: int, conv_idx: int):
    try:
        user_id = int(user_id)
        conv_idx = int(conv_idx)
        target = request.args["target"].lower()
        if target is None:
            target = "cloud"
        if target not in ["cloud", "ditto"]:
            return ErrInvalidQuery("target", target)
        body = request.get_json()
        prompt = body["prompt"]
        if prompt is None or prompt == "":
            return ErrMissingBody("prompt")
        ditto_db.save_prompt(user_id, conv_idx, prompt)

        # if ditto unit is on, send prompt to ditto unit
        if target == "ditto" and get_ditto_unit_on_bool(user_id):
            return prompt_ditto(user_id, conv_idx, prompt)
        else:
            return prompt_cloud(user_id, conv_idx, prompt)

    except BaseException as e:
        log.error(e)
        return ErrException(e)


def prompt_cloud(user_id: int, conv_idx: int, prompt: str):
    log.debug(f"ditto unit is off. sending prompt to memory agent: {prompt}")
    response = json.loads(send_prompt_to_llm(user_id, prompt))["response"]
    ditto_db.save_response(user_id, conv_idx, response)
    return ditto_db.get_chats(
        user_id,
        ditto_db.get_conv_id(user_id, conv_idx),
        0,
        1,
        False,
    )


def prompt_ditto(user_id: int, conv_idx: int, prompt: str):
    log.debug(f"sending prompt to ditto unit: {prompt}")
    # ditto unit will write prompt and response to database
    send_prompt_to_ditto_unit(user_id, prompt)
    # return '{"response": "success"}'
    return ditto_db.get_chats(
        user_id,
        ditto_db.get_conv_id(user_id, conv_idx),
        0,
        1,
        False,
    )


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
        res = requests_lib.post(
            f"http://{ditto_unit_ip}:{ditto_unit_port}/ditto/?toggleMic=1",
            timeout=30,
        )
        return str(res.content.decode().strip())

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


@app.route("/users/<user_id>/conversations/<conv_id>/chats", methods=["GET"])
def get_chats(user_id: int, conv_id: int):
    offset = request.args.get("offset", default=0)
    limit = request.args.get("limit", default=5)
    order = request.args.get("order", default="DESC")
    if order.upper() not in ["ASC", "DESC"]:
        return ErrInvalidQuery("order", order)
    is_asc = True if order.upper() == "ASC" else False
    try:
        conv = ditto_db.get_chats(user_id, conv_id, offset, limit, is_asc)
        log.info(f"conversation: {conv}")
        return conv
    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/get_prompt_response_count", methods=["GET"])
def get_prompt_response_count(user_id: str):
    try:
        count = ditto_db.get_prompt_response_count(user_id)
        return '{"historyCount": %d}' % count
    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/get_conversation_history", methods=["GET"])
def get_conversation_history(user_id: str):
    try:
        prompts, responses = ditto_db.get_conversation_history(user_id)
        return '{"prompts": %s, "responses": %s}' % (prompts, responses)
    except BaseException as e:
        log.error(e)
        return ErrException(e)


# endpoint to get ditto unit status
@app.route("/users/<user_id>/get_ditto_unit_status", methods=["GET"])
def get_ditto_unit_status(user_id: str):
    try:
        ditto_unit_on = get_ditto_unit_on_bool(user_id)
        status = "on" if ditto_unit_on else "off"
        return '{"status": "%s"}' % status
    except BaseException as e:
        log.error(e)
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
        log.error(e)
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
