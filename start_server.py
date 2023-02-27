from server import Server
from gevent.pywsgi import WSGIServer

class devnull:
    write = lambda _: None

def start_server():
    server = Server()
    http_server = WSGIServer(('0.0.0.0', 32032), server.app, log=devnull)
    print('\n\n[NLP Server started on port 32032]\n\n')
    http_server.serve_forever()

if __name__ == "__main__":
    start_server()
    
