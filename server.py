from ditto_memory import DittoMemory
import platform
from flask import Flask
from flask import request
from flask_cors import CORS
import json

# load intent model
from intent import IntentRecognition
intent_model = IntentRecognition(train=False)

# load ditto memory langchain agent
ditto = DittoMemory()

app = Flask(__name__)
CORS(app)

OS = 'Windows'
if platform.system() == 'Linux':
    OS = 'Linux'
elif platform.system() == 'Darwin':
    OS = 'Darwin'

# making requests to the intent model


@app.route("/prompt/", methods=['POST'])
def prompt():
    requests = request.args

    try:
        if request.method == "POST":

            # Request to send prompt to ditto
            if 'prompt' in requests:
                print('\nsending prompt to ditto memory langchain agent\n')
                prompt = requests['prompt']
                response = ditto.prompt(prompt)
                return response

            if 'reset' in requests:
                print("\nresetting ditto langchain agent's memory\n")
                ditto.reset_memory()
                return '{"reset_conversation": "true"}'

        else:
            return '{"error": "invalid request"}'

    except BaseException as e:
        print(e)
        return '{"internal error": "%s"}' % str(e)


@app.route("/intent/", methods=['POST'])
def intent_handler():
    requests = request.args

    try:
        if request.method == "POST":

            # Request to send prompt to ditto
            if 'prompt' in requests:
                print('\nsending prompt to intent model\n')
                prompt = requests['prompt']
                intent = intent_model.prompt(prompt)
                return intent

        else:
            return '{"error": "invalid request"}'

    except BaseException as e:
        print(e)
        return '{"internal error": "%s"}' % str(e)

# making requests to a NER model


@app.route("/ner/", methods=['POST'])
def ner_handler():
    requests = request.args
    ner_response = '{"response:" "None"}'
    try:
        if request.method == "POST":

            if 'ner-timer' in requests:
                print('\nsending request to ner-timer\n')
                prompt = requests['ner-timer']
                ner_response = intent_model.prompt_ner_timer(prompt)

            elif 'ner-light' in requests:
                print('\nsending request to ner_light\n')
                prompt = requests['ner-light']
                ner_response = intent_model.prompt_ner_light(prompt)

            elif 'ner-numeric' in requests:
                print('\nsending request to ner_numeric\n')
                prompt = requests['ner-numeric']
                ner_response = intent_model.prompt_ner_numeric(prompt)

            elif 'ner-play' in requests:
                print('\nsending request to ner_play\n')
                prompt = requests['ner-play']
                ner_response = intent_model.prompt_ner_play(prompt)

            print(ner_response)
            return ner_response

        else:
            return '{"error": "invalid request"}'

    except BaseException as e:
        print(e)
        return '{"internal error": "%s"}' % str(e)


@app.route("/", methods=['POST'])
def post_handler():
    return '{"nlp_server_status": "on"}'


class Server():

    def __init__(self):
        self.app = app


if __name__ == "__main__":

    server = Server()
    # app.run(port='32032', host='0.0.0.0')
