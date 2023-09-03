# uncomment to load .env file
set dotenv-load

# Run container, detaching (daemonize)
run:
    docker run -d --rm --env-file .env -p 32032:32032 nlp_server

# Run container, interactive mode
run-it:
    docker run --env-file .env -it -p 32032:32032 nlp_server

# Run without the container
rundev:
    python main.py

# Build the docker image
build:
    docker build -t nlp_server .
