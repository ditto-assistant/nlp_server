# nlp_server
NLP server housing intent and NER models as well as Langchain memory agent for Ditto assistant clients.

## Running Locally with Docker 
1. Rename `.env.example` to `.env` and set `OPENAI_API_KEY`.
2. `docker build -t nlp_server .`
3. `docker run --env-file .env -it -p 32032:32032 nlp_server`
