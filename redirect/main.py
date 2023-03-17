"""
Image files:
bot.jpg:        https://i.imgur.com/1p2XJr9.jpg
you.jpg:        https://i.imgur.com/PnPpzNd.jpg
fav_bot.jpg:    https://i.imgur.com/HHbH5TJ.jpg
"""
import sys
import time
from flask import Response, abort, Flask, request, render_template
import logging
import os
import mimetypes

URL = os.environ.get('URL', None)
WEB_SOCKET_URL = os.environ.get('WEB_SOCKET_URL', None)

flask_app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def log(log_message):
    if flask_app is not None:
        flask_app.logger.info(log_message)
    else:
        print(log_message)

@flask_app.route('/')
def flask_index():
    host = request.host
    # liklely need to add port
    if '127.0.0.1' in host or '0.0.0.0' in host:
        # means we're running locally or in an image locally
        web_socket_url = "ws://%s/ws" % host
    else:
        # anything else means we're running on Cloud Run and we need wss
        web_socket_url = "wss://%s/ws" % host
    web_socket_url = WEB_SOCKET_URL
    log('Web socket URL: ' + web_socket_url)

    return render_template('index.html', url=URL, web_socket_url=web_socket_url)

# This is to return static files
@flask_app.route('/redirect/<path:file_path>')
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

def index():
    file = open('templates/index.html', 'r')
    html = file.read()
    file.close()
    html = html.replace('{{url}}', URL)
    html = html.replace('{{web_socket_url}}', WEB_SOCKET_URL)
    return Response(html, mimetype='text/html')

def redirect(request):
    log('Starting function %s' % sys.argv[0])
    log('Python: ' + sys.version)
    try:
        path = request.path
    except Exception as e:
        path = None
    log("Path: %s" % path)
    if path != None and len(path) > 1:
        filename = 'static' + path
        try:
            file = open(filename, 'r')
            contents = file.read()
            file.close()
            mimetype = mimetypes.MimeTypes().guess_type(filename)[0]
            return contents, 200, {'Content-Type': mimetype}
        except FileNotFoundError:
            abort(404)
    else:
        html = index()
        return html

if __name__ == '__main__':
    flask_app.run(debug=False, port='8090', host='0.0.0.0')