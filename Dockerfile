FROM python:3.11.4-slim-bullseye as builder

RUN apt update && \
    apt upgrade -y && \
    apt install -y --no-install-recommends git build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# Separate layer for pip install caching
COPY requirements.txt ./  
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . ./

HEALTHCHECK --start-period=10s --interval=1m --retries=3 \
    CMD python healthcheck.py

# initialize default API key values to 'key'
ENV OPENAI_API_KEY=key
ENV SERPER_API_KEY=key

EXPOSE 32032
CMD python main.py

