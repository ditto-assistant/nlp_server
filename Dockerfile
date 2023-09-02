# The builder image, used to build the virtual environment
FROM python:3.11.4-slim-bullseye as builder
RUN apt update && apt install -y git
RUN apt install -y build-essential gcc

# initialize default OPENAI_API_KEY to 'key'
ENV OPENAI_API_KEY=key

COPY data /data
COPY memory /memory
COPY models /models
COPY vectorizers /vectorizers

COPY chat.py chat.py
COPY ditto_memory.py ditto_memory.py
COPY intent.py intent.py
COPY LICENSE LICENSE
COPY main.py main.py
COPY ner.py ner.py
COPY requirements.txt requirements.txt
COPY server.py server.py
COPY start_server.py start_server.py

EXPOSE 32032

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]