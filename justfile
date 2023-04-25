# uncomment to load .env file
# set dotenv-load

run:
    (cd ..; source ditto/bin/activate; cd nlp_server; python main.py)