from server import Server
from gevent.pywsgi import WSGIServer
import logging

log = logging.getLogger('start_server')
logging.basicConfig(level=logging.DEBUG)

class devnull:
    write = lambda _: None

def start_server():
    server = Server()
    http_server = WSGIServer(('0.0.0.0', 32032), server.app, log=devnull)
    log.info('NLP Server started on port 32032]')
    http_server.serve_forever()

if __name__ == "__main__":
    start_server()
