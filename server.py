import platform
from flask import Flask
from flask import request
from flask_cors import CORS
import json

# import offline nlp resources
from nlp import NLP
nlp = NLP()
nlp.initialize()
nlp.contruct_sentence_vectors()

app = Flask(__name__)
CORS(app)

OS = 'Windows'
if platform.system() == 'Linux':
    OS = 'Linux'
elif platform.system() == 'Darwin':
    OS = 'Darwin'

# making requests to the intent model
@app.route("/intent/", methods=['POST'])
def intent_handler():
    requests = request.args

    try:
        if request.method == "POST":

            # Request to send prompt to ditto
            if 'prompt' in requests:
                print('\nsending prompt to intent model\n')
                prompt = requests['prompt']
                intent = nlp.prompt(prompt)
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
                ner_response = nlp.prompt_ner_timer(prompt)
            
            elif 'ner-light' in requests:
                print('\nsending request to ner_light\n')
                prompt = requests['ner-light']
                ner_response = nlp.prompt_ner_light(prompt)

            elif 'ner-numeric' in requests:
                print('\nsending request to ner_numeric\n')
                prompt = requests['ner-numeric']
                ner_response = nlp.prompt_ner_numeric(prompt)
            
            elif 'ner-play' in requests:
                print('\nsending request to ner_play\n')
                prompt = requests['ner-play']
                ner_response = nlp.prompt_ner_play(prompt)

            print(ner_response)
            return ner_response

        else:
            return '{"error": "invalid request"}'
        
    except BaseException as e:
        print(e)
        return '{"internal error": "%s"}' % str(e)


# Use Postman for POST Test and more!
@app.route("/", methods=['POST'])
def post_handler():
    return '{"nlp_server_status": "on"}'


class Server():

    def __init__(self):
        self.app = app


if __name__ == "__main__":

    server = Server()
