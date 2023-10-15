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

# load intent model
intent_model = IntentRecognition(train=False)

# load ditto memory langchain agent
log.info("[Loading Ditto Memory...]")
ditto = DittoMemory()

# load ditto short term memory store
log.info("[Loading Ditto Short Term Memory Store...]")
ditto_stmem = ShortTermMemoryStore()

# set Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# set OS variable
OS = "Windows"
if platform.system() == "Linux":
    OS = "Linux"
elif platform.system() == "Darwin":
    OS = "Darwin"


# Makes requests to the ditto memory langchain agent
@app.route("/users/<user_id>/prompt", methods=["POST"])
def prompt(user_id: str):
    requests = request.args
    try:
        if "prompt" not in requests:
            return ErrMissingArg("prompt")
        prompt = requests["prompt"]

        # add short term memory to prompt
        prompt_with_stmem = ditto_stmem.get_prompt_with_stmem(user_id, prompt)

        log.info(f"sending user: {user_id} prompt to memory agent: {prompt}")
        response = ditto.prompt(prompt_with_stmem, user_id)

        # save response to short term memory
        ditto_stmem.save_response_to_stmem(user_id, prompt, response)

        return response

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/reset_memory", methods=["POST"])
def reset_memory(user_id: str):
    try:
        log.info(f"resetting ditto's long and short-term memory for user: {user_id}")
        ditto.reset_memory(user_id)
        ditto_stmem.reset_stmem(user_id)
        return '{"action": "reset_memory", "status": "ok"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


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
