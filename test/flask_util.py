from flask import Flask, request
from multiprocessing import Process
from threading import Thread
import time

def start_flask_server(request_info):

    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        request_info['GET'] = request.args
        return ''

    app.run(port=9876)


class FlaskServer(object):
    def start(self):
        self.request_info = {}
        p = Thread(target=start_flask_server, kwargs={'request_info': self.request_info})
        p.daemon = True
        #self.server_process = p
        p.start()
        time.sleep(0.5)
   
    def stop(self):
        pass
        #self.server_process.terminate()
