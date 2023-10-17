# uncomment to load .env file
set dotenv-load

# Run container, detaching (daemonize)
run:
    docker run -d --env-file .env -p 32032:32032 --name nlp_server nlp_server

# Run container, detaching (daemonize) and removing container once stopped. Good for dev.
run-rm:
    docker run -d --rm --env-file .env -p 32032:32032 --name nlp_server nlp_server

# Run container, interactive mode
run-it:
    docker run --env-file .env -it -p 32032:32032 --name nlp_server nlp_server

logs:
    docker logs -f nlp_server

stop:
    docker stop nlp_server

# Run without the container
rundev:
    python main.py

# Build the docker image
build:
    docker build -t nlp_server .

# Backup your vector store and convo db
backup:
    docker cp nlp_server:memory .
    docker cp nlp_server:database .
