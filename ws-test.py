"""
https://blog.miguelgrinberg.com/post/add-a-websocket-route-to-your-flask-2-x-application
"""
from flask_sock import Sock
import os
from flask import Flask, request, render_template, make_response
import time
from threading import Thread
import json
import uuid

app = Flask(__name__)
sock_app = Sock(app)

output = []

def log(log_message):
    if app is not None:
        app.logger.info(log_message)
    else:
        print(log_message)

@app.before_request
def do_something_whenever_a_request_comes_in():
    r = request
    log('>>>>>>>>>>>>>>>>>>>> %s %s' % (r.method, r.url))
    headers = r.headers
    if len(headers) > 0:
        log('Request headers: \n%s' % headers)
    args = r.args
    if len(args) > 0:
        log('Request query parameters: \n%s' % args)
    values = r.values
    if len(values) > 0:
        log('Request values: \n%s' % values)
    data = r.data
    if len(data) > 0:
        log('Data payload: \n%s' % data)

def spew(sock):
    sock.send("starting spew")
    time.sleep(2)
    for current_try in range(5):
        if sock.connected is False:
            break
        else:
            sock.send("in loop: %s" % current_try)
            time.sleep(2)
            current_try += 1


@app.route('/')
def index():
    resp = make_response(render_template('ws-test.html'))
    session_id = request.cookies.get('session_id')
    if session_id is None:
        session_id = str(uuid.uuid4())
        resp.set_cookie('session_id', session_id)
    return resp

@sock_app.route('/ws')
def echo(sock):
    while True:
        data = sock.receive()
        session_id = request.cookies.get('session_id')
        sock.send('Echo: %s' % data)


if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
