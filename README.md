# nlp_server
NLP server housing intent and NER models as well as Langchain memory agent for Ditto assistant clients.

## Running Locally with Docker 
1. `docker build -t nlp_server .`
2. `docker run --env-file .env -it -p 32032:32032 nlp_server`