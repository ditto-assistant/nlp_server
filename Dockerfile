# The builder image, used to build the virtual environment
FROM python:3.11.4-slim-bullseye as builder
RUN apt update && apt install -y git build-essential gcc

COPY . ./
RUN pip install --upgrade pip && pip install -r requirements.txt

HEALTHCHECK --start-period=10s --interval=1m CMD python healthcheck.py

# initialize default OPENAI_API_KEY to 'key'
ENV OPENAI_API_KEY=key
EXPOSE 32032
CMD python main.py

