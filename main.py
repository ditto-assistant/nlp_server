import gevent.subprocess as subprocess
import sys
import nltk
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")


def start_server():
    """
    Boots the NLP Server for API calls.
    """
    log.info("Starting NLP Server...")
    nltk.download("punkt")
    nltk.download("wordnet")
    subprocess.call(["python", "start_server.py"])


if __name__ == "__main__":
    start_server()
