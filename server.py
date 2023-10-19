import json
import shutil
import requests as requests_lib
from ditto_memory import DittoMemory
import platform
from flask import Flask
from flask import request
from flask_cors import CORS
import logging

# set up logging for server
log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO)

# load intent model
from intent import IntentRecognition

# import short term memory store
from ditto_stmem import ShortTermMemoryStore

# import ditto database handler
from database.db import DittoDB

import os

# load intent model
intent_model = IntentRecognition(train=False)

# load ditto memory langchain agent
log.info("[Loading Ditto Memory...]")
ditto = DittoMemory()

# load ditto short term memory store
log.info("[Loading Ditto Short Term Memory Store...]")
ditto_stmem = ShortTermMemoryStore()

# load ditto database handler
log.info("[Loading Ditto Database Handler...]")
ditto_db = DittoDB()


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
    log.info("Please fill out users.json with your user information and restart the server.")
    exit()
else: # load users.json
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
    # add short term memory to prompt
    prompt_with_stmem = ditto_stmem.get_prompt_with_stmem(user_id, prompt)

    log.info(f"sending user: {user_id} prompt to memory agent: {prompt}")
    response = ditto.prompt(prompt_with_stmem, user_id)

    # save response to short term memory
    ditto_stmem.save_response_to_stmem(user_id, prompt, response)

    return json.dumps({"response": response})

# Makes requests to the ditto memory langchain agent
@app.route("/users/<user_id>/prompt_llm", methods=["POST", "GET"])
def prompt_llm(user_id: str):
    requests = request.args
    try:
        if "prompt" not in requests:
            return ErrMissingArg("prompt")
        prompt = requests["prompt"]

        response = send_prompt_to_llm(user_id, prompt)

        return response

    except BaseException as e:
        log.error(e)
        return ErrException(e)

@app.route("/users/<user_id>/prompt_ditto", methods=["POST", "GET"])
def prompt_ditto(user_id: str):
    requests = request.args
    try:
        if "prompt" not in requests:
            return ErrMissingArg("prompt")
        
        # get user's prompt from request
        prompt = requests["prompt"]

        # write prompt to database
        ditto_db.write_prompt_to_db(user_id, prompt)

        # check if ditto unit is on
        ditto_unit_on = get_ditto_unit_on_bool(user_id)

        # if ditto unit is on, send prompt to ditto unit
        if ditto_unit_on:
            # ditto unit will write prompt and response to database
            send_prompt_to_ditto_unit(user_id, prompt)
            return '{"response": "success"}'
        else:
            # ditto unit is off, send prompt to memory agent
            response = json.loads(send_prompt_to_llm(user_id, prompt))['response']

            # write response to database
            ditto_db.write_response_to_db(user_id, response)

            return '{"response": "success"}'


    except BaseException as e:
        log.error(e)
        return ErrException(e)

@app.route("/users/<user_id>/reset_memory", methods=["POST", "GET"])
def reset_memory(user_id: str):
    try:
        log.info(f"resetting ditto's long and short-term memory for user: {user_id}")
        ditto.reset_memory(user_id)
        ditto_stmem.reset_stmem(user_id)
        log.info(f"resetting prompt and response history for user: {user_id}")
        ditto_db.reset_conversation(user_id)
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
            return ErrMissingArg("prompt")
        
        # get user's prompt from request
        prompt = requests["prompt"]      

        log.info(f"saving ditto unit prompt to database.")

        # save prompt to database
        ditto_db.write_prompt_to_db(user_id, prompt)  

        return '{"response": "success"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)

@app.route("/users/<user_id>/write_response", methods=["POST", "GET"])
def write_response(user_id: str):
    requests = request.args
    try:
        if "response" not in requests:
            return ErrMissingArg("response")
        
        # get user's prompt from request
        response = requests["response"]      

        log.info(f"saving ditto unit response to database.")

        # save prompt to database
        ditto_db.write_response_to_db(user_id, response)  

        return '{"response": "success"}'

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
            return ErrMissingArg("prompt")
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
        return ErrMissingArg("prompt")
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


def ErrMissingArg(arg: str):
    return '{"error": "missing argument %s"}' % arg


def ErrException(e: BaseException):
    return '{"error": "%s"}' % e
