# nlp_server
NLP server housing intent and NER models as well as Langchain memory agent for Ditto [assistant](http://github.com/omarzanji/assistant) clients.

## Running Locally with Docker 
1. Rename `.env.example` to `.env` and set `OPENAI_API_KEY` to your OpenAI API key.
2. Rename `example_users.json` to `users.json` and add user's information.
3. `docker build -t nlp_server .`
4. `docker run --env-file .env --rm -p 32032:32032 nlp_server`

## Set up Google Search API for LLM (optional)
1. Main Google Search Agent:
    1. Create an account on [serpapi.com](http://serpapi.com/) and set `SERPAPI_API_KEY` to your API key in `.env`.
2. Fallback Agent:
    2. Create an account on [serper.dev](http://serper.dev/) and set `SERPER_API_KEY` to your API key in `.env`.

## Changing LLM Provider
1. If you prefer using HuggingFace's API, set `HUGGINGFACEHUB_API_TOKEN` to your HuggingFace API key and set `LLM=huggingface` in `.env`.
