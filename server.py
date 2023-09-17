from ditto_memory import DittoMemory
import platform
from flask import Flask
from flask import request
from flask_cors import CORS
import logging

log = logging.getLogger("server")
logging.basicConfig(level=logging.INFO)

# load intent model
from intent import IntentRecognition

intent_model = IntentRecognition(train=False)

# load ditto memory langchain agent
log.info("[Loading Ditto Memory...]")
ditto = DittoMemory()

app = Flask(__name__)
CORS(app)

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
        if "prompt" in requests:
            log.info("sending prompt to ditto memory langchain agent")
            prompt = requests["prompt"]
            response = ditto.prompt(prompt, user_id)
            return response
        else:
            return ErrMissingArg("prompt")

    except BaseException as e:
        log.error(e)
        return ErrException(e)


@app.route("/users/<user_id>/reset_memory", methods=["POST"])
def reset_memory(user_id: str):
    try:
        log.info("resetting ditto langchain agent's memory")
        ditto.reset_memory(user_id)
        return '{"action": "reset_memory", "status": "ok"}'

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# Makes requests to the intent model
@app.route("/intent/", methods=["POST"])
def intent_handler():
    requests = request.args
    try:
        # Request to send prompt to ditto
        if "prompt" in requests:
            log.info("sending prompt to intent model")
            prompt = requests["prompt"]
            intent = intent_model.prompt(prompt)
            return intent

    except BaseException as e:
        log.error(e)
        return ErrException(e)


# making requests to a NER model
@app.route("/ner/", methods=["POST"])
def ner_handler():
    requests = request.args
    ner_response = '{"response:" "None"}'
    try:
        if "ner-timer" in requests:
            log.info("sending request to ner-timer")
            prompt = requests["ner-timer"]
            ner_response = intent_model.prompt_ner_timer(prompt)

        elif "ner-light" in requests:
            log.info("sending request to ner_light")
            prompt = requests["ner-light"]
            ner_response = intent_model.prompt_ner_light(prompt)

        elif "ner-numeric" in requests:
            log.info("sending request to ner_numeric")
            prompt = requests["ner-numeric"]
            ner_response = intent_model.prompt_ner_numeric(prompt)

        elif "ner-play" in requests:
            log.info("sending request to ner_play")
            prompt = requests["ner-play"]
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
