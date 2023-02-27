import gevent.subprocess as subprocess

def start_server():
        '''
        Boots the NLP Server for API calls.
        '''
        print('\n[Starting NLP Server...]')
        subprocess.call(['python', 'start_server.py'])
        

if __name__ == "__main__":
    start_server()