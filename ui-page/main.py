"""
Image files:
bot.jpg:        https://i.imgur.com/1p2XJr9.jpg
you.jpg:        https://i.imgur.com/PnPpzNd.jpg
fav_bot.jpg:    https://i.imgur.com/HHbH5TJ.jpg
"""
import sys
import time
from flask import Response, abort, Flask, request, render_template, make_response
import logging
import os
import mimetypes
import uuid
import datetime

URL = os.environ.get('URL', None)
SOCKET_URL = os.environ.get('SOCKET_URL', None)
UPLOADER_URL = os.environ.get('UPLOADER_URL', None)

flask_app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def log(log_message):
    if flask_app is not None:
        flask_app.logger.info(log_message)
    else:
        print(log_message)

@flask_app.route('/')
def flask_index():
    session_id = request.cookies.get('session_id')
    if session_id is None:
        session_id = str(uuid.uuid4())
    log('URL to load: ' + URL)
    log('Web socket URL: ' + SOCKET_URL)
    log('Uploader URL:  ' + UPLOADER_URL)
    print("Cookies: %s" % request.cookies)

    resp = make_response(render_template('index.html', 
                                         url=URL, 
                                         socket_url=SOCKET_URL, 
                                         uploader_url=UPLOADER_URL, 
                                         session_id=session_id))
     # set a cookie expiration date of 1 day
    expire_date = datetime.datetime.now() + datetime.timedelta(days=1)
    resp.set_cookie('session_id', session_id, expires=expire_date)
    return resp

# This is to return static files
@flask_app.route('/static/<path:file_path>')
def flask_file(file_path):
    filename = 'static/' + file_path
    try:
        file = open(filename, 'r')
        contents = file.read()
        file.close()
        mimetype = mimetypes.MimeTypes().guess_type(filename)[0]
        return contents, 200, {'Content-Type': mimetype}
    except FileNotFoundError:
        abort(404)

def ui(request):
    log('Starting function %s' % sys.argv[0])
    log('Python: ' + sys.version)
    print("Cookies: %s" % request.cookies)
    try:
        path = request.path
    except Exception as e:
        path = None
    log("Path: %s" % path)
    session_id = request.cookies.get('session_id')
    if session_id is None:
        session_id = str(uuid.uuid4())
    if path != None and len(path) > 1:
        filename = 'static' + path
        try:
            file = open(filename, 'r')
            contents = file.read()
            file.close()
            mimetype = mimetypes.MimeTypes().guess_type(filename)[0]
            log('returning file: %s - mimetype: %s' % (filename, mimetype))
            return contents, 200, {'Content-Type': mimetype}
        except FileNotFoundError:
            abort(404)
    else:
        # html = index()
        resp = make_response(render_template('index.html', 
                                             url=URL, 
                                             socket_url=SOCKET_URL, 
                                             uploader_url=UPLOADER_URL, 
                                             session_id=session_id))
        # set a cookie expiration date of 1 day
        expire_date = datetime.datetime.now() + datetime.timedelta(days=1)
        resp.set_cookie('session_id', session_id, expires=expire_date, samesite=None)
        return resp

if __name__ == '__main__':
    flask_app.run(debug=False, port='8090', host='0.0.0.0')