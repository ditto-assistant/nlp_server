# uncomment to load .env file
# set dotenv-load

run:
    docker run --env-file .env -it -p 32032:32032 nlp_server

build:
    docker build -t nlp_server .
