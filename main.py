import gevent.subprocess as subprocess
import sys
import nltk
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")

args = sys.argv

MODE = "dev"
if len(args) > 1:
    MODE = args[1]


def start_server():
    """
    Boots the NLP Server for API calls.
    """
    log.info("Starting NLP Server...")
    nltk.download("punkt")
    nltk.download("wordnet")
    if MODE == "prod":
        subprocess.call(["python", "~/nlp_server/start_server.py"])
    else:
        subprocess.call(["python", "start_server.py"])


if __name__ == "__main__":
    start_server()
