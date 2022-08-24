"""
Bot to solve Sudoku puzzles
"""
import os
from socket import IPV6_DONTFRAG
import sys
import logging
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, jsonify, render_template, Response, abort
from threading import Thread, Event
import random
import requests
from google.cloud import dialogflow
import json
import redis
import traceback
import resource
import urllib.parse
import cv2
import numpy as np
import image_utils
import re
from datetime import datetime
import time

PROJECT_ID = 'cloud-run-stuff'

ABOUT_YOU = 'about.you'
BYE = 'bye'
CALL_ME = 'call.me'
CHECK_VALUE = 'check.value'
INPUT_UNKNOWN = 'input.unknown'
WELCOME = 'welcome'
DONT_CALL_ME_THAT = 'dont.call.me.that'
DONT_CALL_ME_THAT_FALLBACK = 'dont.call.me.that.fallback'
GIVE_ME_A_HINT = 'give.me.a.hint'
GIVE_ME_THE_ANSWER = 'give.me.the.answer'
GIVE_ME_THE_INPUT_PUZZLE = 'give.me.the.input.puzzle'
INPUT_NUMBER_LIST = 'input.number.list'
INPUT_URL = 'input.url'
I_HAVE_A_PUZZLE = 'i.have.a.puzzle'
NEGATIVE_RESPONSE = 'negative.response'
POSITIVE_RESPONSE = 'positive.response'
ROW_COLUMN_HINT_PRE = 'row.column.hint.pre'
ROW_COLUMN_HINT_POST = 'row.column.hint.post'
ROW_COLUMN_FIX_PRE = 'row.column.fix.pre'
ROW_COLUMN_FIX_POST = 'row.column.fix.post'
SOLVE_MY_PUZZLE = 'solve.my.puzzle'
START_OVER = 'start.over'
THANK_YOU = 'thank.you'
WHAT_ARE_YOUR_CAPABILITIES = 'what.are.your.capabilities'

ENTITY_ROW = 'row'
ENTITY_COLUMN = 'column'
ENTITY_NUMBER = 'number-integer'
ENTITY_ORDINAL = 'ordinal-number'
ENTITY_PERSON = 'person'
ENTITY_PERSON_NAME = 'name'
ENTITY_URL = 'url'
ENTITY_EMPTY = 'empty'

INPUT = 'input'
INTENT = 'intent'
CONFIDENCE = 'confidence'
ANSWER = 'answer'
ACTION = 'action'
PARAMETERS = 'parameters'
IMAGE_URL = 'image_url'

PUZZLE_INPUT = 'puzzle_input'
PUZZLE_INPUT_MATRIX = 'puzzle_input_matrix'
PUZZLE_INPUT_IMAGE_URL = 'puzzle_input_image_url'
PUZZLE_INPUT_IMAGE_COORDINATES = 'puzzle_input_image_coordinates'
PUZZLE_SOLUTION_MATRIX = 'puzzle_solution_matrix'
PUZZLE_SOLUTION_IMAGE_URL = 'puzzle_solution_image_url'
PUZZLE_ACTION = 'puzzle_action'
PUZZLE_ASYNC_JOB_ID = 'puzzle_async_job_id'
PUZZLE_CALL_ME = 'puzzle_call_me'
INPUT_IMAGE_ID = 'input_image_id'
REQUEST_HOST = 'request_host'

INSULTING_NAME = 'INSULTING_NAME'
I_HAVE_AN_ANSWER = 'I_HAVE_AN_ANSWER'
I_CANT_SOLVE_YOUR_PUZZLE = 'I_CANT_SOLVE_YOUR_PUZZLE'
I_CANT_FIND_YOUR_INPUT = 'I_CANT_FIND_YOUR_INPUT'
I_WILL_NOW_CALL_YOU = 'I_WILL_NOW_CALL_YOU'
I_DONT_HAVE_A_PUZZLE = 'I_DONT_HAVE_A_PUZZLE'
I_HAVENT_SOLVED_THE_PUZZLE = 'I_HAVENT_SOLVED_THE_PUZZLE'
TA_DA = 'TA_DA'
I_CANT_HEAR_YOU = 'I_CANT_HEAR_YOU'
I_DONT_HAVE_SOMETHING_TO_FIX = 'I_DONT_HAVE_SOMETHING_TO_FIX'
I_NEED_ROW_AND_COLUMN_TO_FIX = 'I_NEED_ROW_AND_COLUMN_TO_FIX'
I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_FIX = 'I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_FIX'
I_NEED_ROW_AND_COLUMN_TO_HINT = 'I_NEED_ROW_AND_COLUMN_TO_HINT'
I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_HINT = 'I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_HINT'
ROW_COLUMN_IS_ALREADY = 'ROW_COLUMN_IS_ALREADY'
ROW_COLUMN_IS_NOW = 'ROW_COLUMN_IS_NOW'
YOU_NEED_TO_ASK_ME_TO_SOLVE = 'YOU_NEED_TO_ASK_ME_TO_SOLVE'
ROW_COLUMN_IS = 'ROW_COLUMN_IS'
ROW_COLUMN_IS_NOT = 'ROW_COLUMN_IS_NOT'
THISLL_JUST_BE_A_MINUTE = 'THISLL_JUST_BE_A_MINUTE'
IVE_ALREADY_SOLVED_IT = 'IVE_ALREADY_SOLVED_IT'
I_ALREADY_HAVE_A_PUZZLE = 'I_ALREADY_HAVE_A_PUZZLE'
IVE_SOLVED_YOUR_PUZZLE = 'IVE_SOLVED_YOUR_PUZZLE'
I_DONT_RECOGNIZE_YOUR_IMAGE = 'I_DONT_RECOGNIZE_YOUR_IMAGE'
HUH = 'HUH'

REDIS_TTL = 3600
MAX_IMAGE_HEIGHT = 1280
TIME_SLEEP_INTERVAL = 5

SUDOKU_SOLVER_URL = os.environ['SUDOKU_SOLVER_URL']
if SUDOKU_SOLVER_URL[len(SUDOKU_SOLVER_URL) - 1] != '/':
    SUDOKU_SOLVER_URL += '/'
REDIS_HOST_URL = os.environ['REDIS_HOST']
REDIS_PW = os.environ['REDIS_PW']
REDIS_PORT = os.environ['REDIS_PORT']
JWT_SECRET = os.environ['JWT_SECRET']
# Your Account Sid and Auth Token from twilio.com/user/account
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


runtime_cache = redis.Redis(
    host=REDIS_HOST_URL,
    port=REDIS_PORT,
    password=REDIS_PW)
# Testing Redis connection.
runtime_cache.setex('/test/test', REDIS_TTL, 'test_value')
test_value = runtime_cache.delete('/test/test')

# pylint: disable=C0103
flask_app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def log(log_message):
    if flask_app is not None:
        flask_app.logger.info(log_message)
    else:
        print(log_message)


@flask_app.before_request
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

@flask_app.after_request
def do_something_after_a_request_finishes(response):
    # log('Max memory used: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return response

@flask_app.errorhandler(Exception)
def handle_bad_request(e):
    log('>>>>>>>>>>>>>>>>>>>> Error: ' + str(e))
    log(traceback.format_exc())
    log('Max memory used: %s' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return str(e)

def add_links(json_string):
    url_regex = r'https?://[0-9a-zA-z.\-$#@]+:?\d+[/0-9a-zA-z.\-$#@]+'
    matches = re.findall(url_regex, json_string)
    for match in matches:
        match_with_link = "<a href=%s>%s</a>" % (match, match)
        json_string = json_string.replace(match, match_with_link)
    return json_string

@flask_app.route('/converse',methods = ['POST', 'GET'])
def converse():
    
    session_id = request.headers['Host'].replace(':','.')
    parms = request.args
    image_parm = parms.get('image')
    if image_parm is not None:
        text = image_parm
    else:
        form = request.form
        text = form['text_input']
    conversation_response = call_dialogflow(text, session_id)
    conversation_response = process_conversation_turn(conversation_response, session_id)
    response_json = json.dumps(conversation_response, indent=4)
    json_with_links = add_links(response_json)
    return render_template('index.html', input=text, response=json_with_links)

@flask_app.route('/sms',methods = ['POST', 'GET'])
def sms_reply():
    values = request.values
    resp = MessagingResponse()
    if len(values) > 0:
        body = values.get('Body')
        from_number = values.get('From')
        media_url = values.get('MediaUrl0')
        session_id = from_number[1:]
        if media_url is not None and len(media_url) > 0:
            text = '%s. %s' % (body, media_url)
        else: 
            text = body
        log('From: %s. Body: %s. Media URL: %s.' % (from_number, body, media_url))
        conversation_response = call_dialogflow(text, session_id)
        conversation_response['sms_from'] = from_number
        conversation_response = process_conversation_turn(conversation_response, session_id)
        msg = resp.message(conversation_response['answer'])
        images = conversation_response.get(IMAGE_URL)
        if images is not None:
            if isinstance(images, list):
                for i in images:
                    msg.media(i)
            else:
                msg.media(images)
    else:
        resp.message('%s\n%s' % (get_response_text_for(I_CANT_HEAR_YOU),get_response_text_for(INSULTING_NAME)))
    log('SMS Response:')
    log(str(resp))
    return str(resp)

@flask_app.route('/sms-test',methods = ['POST', 'GET'])
def sms_test():
    resp = MessagingResponse()

    from_number = '+19192446142'
    media_url = 'https://i.imgur.com/hHzcWLq.png'
    session_id = request.headers['Host'].replace(':','.')
    text = media_url
    conversation_response = call_dialogflow(text, session_id)
    conversation_response['sms_from'] = from_number
    conversation_response = process_conversation_turn(conversation_response, session_id)
    response_json = json.dumps(conversation_response, indent=4)
    json_with_links = add_links(response_json)
    return render_template('index.html', input=text, response=json_with_links)

@flask_app.route('/sms-retry',methods = ['POST', 'GET'])
def sms_retry():
    # Used for debugging when responses to Tiwlio exceed time limit.
    values = request.values
    resp = MessagingResponse()
    if len(values) > 0:
        body = values.get('Body')
        from_number = values.get('From')
        media_url = values.get('MediaUrl0')
        resp.message('SMS Retry - From: %s. Body: %s. Media URL: %s.' % (from_number, body, media_url))
    else:
        resp.message('SMS Retry - no payload. Should never see this.')
    log('SMS Retry Response:')
    log(str(resp))
    return str(resp)

@flask_app.route('/favicon.ico')
def favicon():
    return flask_app.send_static_file('favicon-96x96.png')

@flask_app.route('/build', methods=['GET', 'POST'])
def build():
    try:
        build_file = open('static/build.txt')
        build_stamp = build_file.readlines()[0]
        build_file.close()
    except FileNotFoundError:
        build_stamp = generate_build_stamp()
    results = 'Running %s %s.\nBuild %s.\nPython %s.' % (sys.argv[0], flask_app.name, build_stamp, sys.version)
    return results

def generate_build_stamp():
    from datetime import date
    return 'Development build - %s' % date.today().strftime('%m/%d/%y')

@flask_app.route('/redis', defaults={'file_path': ''})
@flask_app.route('/redis/<path:file_path>')
def redis_content(file_path):
    if file_path is None or file_path == '':
        matrix_image_names_as_bytes = runtime_cache.keys()
        matrix_image_names = []
        for entry in matrix_image_names_as_bytes:
            matrix_image_names.append(entry.decode('utf-8'))
        return render_template('redis.html', files=matrix_image_names, title='Redis cache content')
    else:
        url_file_path = urllib.parse.quote("/%s" % file_path)
        bytes = runtime_cache.get(url_file_path)
        if bytes is None:
            return abort(404)
        else:
            filename, file_extension = os.path.splitext(url_file_path)
            if file_extension == '.json':
                json_string = bytes.decode("utf-8")
                json_results = json.loads(json_string)
                return jsonify(json_results)
            else:
                return Response(bytes, mimetype='image/png', status=200)

@flask_app.route('/clear_redis')
def clear_redis():
    keys = runtime_cache.keys()
    number_of_entries = len(keys)
    for key in keys:
        runtime_cache.delete(key)
    # return Response('Removed %s redis entries' % number_of_entries, mimetype='text/text', status=200)
    return 'Removed %s redis entries' % number_of_entries

@flask_app.route('/')
def index():
    return render_template('index.html')

def call_dialogflow(text, session_id):
    log('Session %s calling DialogFlow with \'%s\'.' % (session_id, text))
    language_code = 'en-US'
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    resp = session_client.detect_intent(
        request={'session': session, 'query_input': query_input}
    )
    intent = resp.query_result.intent.display_name
    confidence = resp.query_result.intent_detection_confidence
    answer_text = resp.query_result.fulfillment_text
    action = resp.query_result.action
    parameters = {}
    for key in resp.query_result.parameters:
        value = resp.query_result.parameters[key]
        if key == ENTITY_COLUMN or key == ENTITY_ROW:
            parameters[key] = value
        elif key == ENTITY_PERSON:
            if value is None or len(value) == 0:
                parameters[key] = {'name': ''}
            else:
                name = value.get('name')
                parameters[key] = {'name': name}
        elif key == ENTITY_URL:
            parameters[key] = value
        else:
            # These are instances of ENTITY_NUMBER or ENTITY_ORDINAL
            # Need to convert to a list since what comes back from the API call is an instance of
            # proto.marshal.collections.repeated.RepeatedComposite, which is not JSON serializable
            values_list = []
            for item in value:
                if isinstance(item, float):
                    values_list.append(int(item))
                else:
                    values_list.append(item)
            parameters[key] = values_list
    conversation_response = {
        'input': text,
        'intent': intent,
        'confidence': confidence,
        'answer': answer_text,
        'action': action,
        'parameters': parameters
    }
    set_context(session_id, REDIS_HOST_URL, request.host_url)
    log('Result of DialogFlow call:')
    log(json.dumps(conversation_response, indent=4))
    return conversation_response

def process_conversation_turn(conversation_response, session_id):
    print('Action: %s' % conversation_response[ACTION])
    if conversation_response[ACTION] == CALL_ME:
        conversation_response = call_me(conversation_response, session_id)
    elif conversation_response[ACTION] == DONT_CALL_ME_THAT_FALLBACK:
        conversation_response = call_me_fallback(conversation_response, session_id)
    elif conversation_response[ACTION] == GIVE_ME_THE_ANSWER:
        conversation_response = provide_solution_matrix(conversation_response, session_id)
    elif conversation_response[ACTION] == GIVE_ME_THE_INPUT_PUZZLE:
        conversation_response = provide_input_matrix(conversation_response, session_id)
    elif conversation_response[ACTION] == INPUT_NUMBER_LIST:
        conversation_response = handle_text_input(conversation_response, session_id)
    elif conversation_response[ACTION] == INPUT_URL:
        conversation_response = handle_url_input(conversation_response, session_id)
    elif conversation_response[ACTION] == ROW_COLUMN_HINT_PRE or conversation_response[ACTION] == ROW_COLUMN_HINT_POST:
        conversation_response = provide_hint(conversation_response, session_id)
    elif conversation_response[ACTION] == ROW_COLUMN_FIX_PRE or conversation_response[ACTION] == ROW_COLUMN_FIX_POST:
        conversation_response = fix_input_matrix(conversation_response, session_id)
    elif conversation_response[ACTION] == SOLVE_MY_PUZZLE:
        conversation_response = solve_puzzle(conversation_response, session_id)
    elif conversation_response[ACTION] == START_OVER:
        conversation_response = start_over(conversation_response, session_id)
    elif conversation_response[ACTION] == WHAT_ARE_YOUR_CAPABILITIES:
        conversation_response[IMAGE_URL] = [
            'https://i.imgur.com/hHzcWLq.png',
            'https://i.imgur.com/agkUm86.jpg'
        ]
    
    answer = conversation_response[ANSWER]
    if answer is not None and len(answer) > 0:
        if get_context(session_id, PUZZLE_CALL_ME) is not None:
            add_response_text(conversation_response, [get_context(session_id, PUZZLE_CALL_ME)])
        else:
            add_response_text(conversation_response, [get_response_text_for(INSULTING_NAME)])
    return conversation_response

def ordinal_to_integer(entity):
    if entity == 'first':
        int_value = 1
    elif entity == 'second':
        int_value = 2
    elif entity == 'third':
        int_value = 3
    elif entity == 'fourth':
        int_value = 4
    elif entity == 'fifth':
        int_value = 5
    elif entity == 'sixth':
        int_value = 6
    elif entity == 'seventh':
        int_value = 7
    elif entity == 'eighth':
        int_value = 8
    elif entity == 'ninth':
        int_value = 9
    elif entity == 'last':
        int_value = 9
    elif entity == 'penultimate':
        int_value = 8
    return int_value

def get_row_location(input_text):
    loc = input_text.find('row')
    if loc < 0:
        loc = input_text.find('r')
    return loc

def get_column_location(input_text):
    loc = input_text.find('column')
    if loc < 0:
        loc = input_text.find('col')
        if loc < 0:
            loc = input_text.find('c')
    return loc

def fix_input_matrix(conversation_response, session_id):
    if get_context(session_id, PUZZLE_INPUT_MATRIX) is None:
        set_response_text(conversation_response, [get_response_text_for(I_DONT_HAVE_SOMETHING_TO_FIX)])
    else:
        if len(conversation_response[PARAMETERS][ENTITY_ROW]) > 0:
            row = True
        else:
            row = False
        if len(conversation_response[PARAMETERS][ENTITY_COLUMN]) > 0:
            column = True
        else:
            column = False
        ordinals = conversation_response[PARAMETERS][ENTITY_ORDINAL]
        ordinal_numbers = []
        for ordinal in ordinals:
            ordinal_numbers.append(ordinal_to_integer(ordinal))
        numbers = conversation_response[PARAMETERS][ENTITY_NUMBER]
        # This is a hack because empty entity is coming back as an array characters instead of as a string.
        if len(conversation_response[PARAMETERS][ENTITY_EMPTY]) > 0:
            empty_entity = 1
        else:
            empty_entity = 0
        if row is False or column is False:
            set_response_text(conversation_response, [get_response_text_for(I_NEED_ROW_AND_COLUMN_TO_FIX)])
        elif len(ordinal_numbers) + len(numbers) + empty_entity != 3 or (len(numbers) + empty_entity) == 0:
            set_response_text(conversation_response, [get_response_text_for(I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_FIX)])
        else:
            row_location = get_row_location(conversation_response[INPUT])
            column_location = get_column_location(conversation_response[INPUT])
            if conversation_response[ACTION] == ROW_COLUMN_FIX_PRE:
                if empty_entity != 0:
                    new_value = 0
                    first_number_index = 0
                    second_number_index = 1
                else:
                    new_value = numbers[0]
                    first_number_index = 1
                    second_number_index = 2
                if len(ordinal_numbers) == 0:
                    if row_location < column_location:
                        row_value = numbers[first_number_index]
                        column_value = numbers[second_number_index]
                    else:
                        row_value = numbers[second_number_index]
                        column_value = numbers[first_number_index]
                elif len(ordinal_numbers) == 1:
                    if row_location < column_location:
                        row_value = numbers[first_number_index]
                        column_value = ordinal_numbers[0]
                    else:
                        row_value = ordinal_numbers[0]
                        column_value = numbers[first_number_index]
                else:
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = ordinal_numbers[1]
                    else:
                        row_value = ordinal_numbers[1]
                        column_value = ordinal_numbers[0]
            else:
                if len(ordinal_numbers) == 0:
                    if empty_entity == 1:
                        new_value = 0
                    else:
                        new_value = numbers[2]
                    if row_location < column_location:
                        row_value = numbers[0]
                        column_value = numbers[1]
                    else:
                        row_value = numbers[1]
                        column_value = numbers[0]
                elif len(ordinal_numbers) == 1:
                    if empty_entity == 1:
                        new_value = 0
                    else:
                        new_value = numbers[1]
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = numbers[0]
                    else:
                        row_value = numbers[0]
                        column_value = ordinal_numbers[0]
                else:
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = ordinal_numbers[1]
                    else:
                        row_value = ordinal_numbers[1]
                        column_value = ordinal_numbers[0]
                    if empty_entity == 1:
                        new_value = 0
                    else:
                        new_value = numbers[0]
            input = get_context(session_id, PUZZLE_INPUT_MATRIX)
            current_value = input[row_value-1][column_value-1]
            if current_value == new_value:
                solution_processing_message = get_response_text_for(ROW_COLUMN_IS_ALREADY) % (row_value, column_value, new_value)
                set_response_text(conversation_response, [solution_processing_message])
            else:
                input[row_value-1][column_value-1] = new_value
                set_context(session_id, PUZZLE_INPUT_MATRIX, input)
                solution_processing_message = get_response_text_for(ROW_COLUMN_IS_NOW) % (row_value, column_value, new_value)
                set_response_text(conversation_response, [solution_processing_message])
                if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
                    delete_context(session_id, PUZZLE_SOLUTION_MATRIX)
                    delete_context(session_id, PUZZLE_SOLUTION_IMAGE_URL)
                conversation_response = provide_input_matrix(conversation_response, session_id)
                # conversation_response = handle_url_input(conversation_response, session_id)
            
    return conversation_response

def provide_hint(conversation_response, session_id):

    if get_context(session_id, PUZZLE_INPUT_MATRIX) is None:
        set_response_text(conversation_response, [get_response_text_for(I_DONT_HAVE_A_PUZZLE)])
    elif get_context(session_id, PUZZLE_SOLUTION_MATRIX) is None:
        set_response_text(conversation_response, [get_response_text_for(YOU_NEED_TO_ASK_ME_TO_SOLVE)])
    else:
        if len(conversation_response[PARAMETERS][ENTITY_ROW]) > 0:
            row = True
        else:
            row = False
        if len(conversation_response[PARAMETERS][ENTITY_COLUMN]) > 0:
            column = True
        else:
            column = False
        ordinals = conversation_response[PARAMETERS][ENTITY_ORDINAL]
        ordinal_numbers = []
        for ordinal in ordinals:
            ordinal_numbers.append(ordinal_to_integer(ordinal))
        numbers = conversation_response[PARAMETERS][ENTITY_NUMBER]
        if row is False or column is False:
            set_response_text(conversation_response, [get_response_text_for(I_NEED_ROW_AND_COLUMN_TO_HINT)])
        elif len(ordinal_numbers) + len(numbers) < 2:
            set_response_text(conversation_response, [get_response_text_for(I_NEED_ROW_AND_COLUMN_TO_HINT)])
        elif len(ordinal_numbers) + len(numbers) > 3:
            set_response_text(conversation_response, [get_response_text_for(I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_HINT)])
        else:
            row_location = get_row_location(conversation_response[INPUT])
            column_location = get_column_location(conversation_response[INPUT])
            if conversation_response[ACTION] == ROW_COLUMN_HINT_PRE:
                guess_value = numbers[0]
                if len(ordinal_numbers) == 0:
                    if row_location < column_location:
                        row_value = numbers[1]
                        column_value = numbers[2]
                    else:
                        row_value = numbers[2]
                        column_value = numbers[1]
                elif len(ordinal_numbers) == 1:
                    if row_location < column_location:
                        row_value = numbers[1]
                        column_value = ordinal_numbers[0]
                    else:
                        row_value = ordinal_numbers[0]
                        column_value = numbers[1]
                else:
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = ordinal_numbers[1]
                    else:
                        row_value = ordinal_numbers[1]
                        column_value = ordinal_numbers[0]
            else:
                if len(ordinal_numbers) == 0:
                    if len(numbers) == 3:
                        if row_location < column_location:
                            row_value = numbers[0]
                            column_value = numbers[1]
                            guess_value = numbers[2]
                        else:
                            row_value = numbers[1]
                            column_value = numbers[0]
                            guess_value = numbers[2]
                    else:
                        if row_location < column_location:
                            row_value = numbers[0]
                            column_value = numbers[1]
                        else:
                            row_value = numbers[1]
                            column_value = numbers[0]
                        guess_value = None
                    
                elif len(ordinal_numbers) == 1:
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = numbers[0]
                    else:
                        row_value = numbers[0]
                        column_value = ordinal_numbers[0]
                    if len(numbers) > 1:
                        guess_value = numbers[0]
                    else:
                        guess_value = None
                else:
                    if row_location < column_location:
                        row_value = ordinal_numbers[0]
                        column_value = ordinal_numbers[1]
                    else:
                        row_value = ordinal_numbers[1]
                        column_value = ordinal_numbers[0]
                    if len(numbers) == 1:
                        guess_value = numbers[0]
                    else:
                        guess_value = None

            solution = get_context(session_id, PUZZLE_SOLUTION_MATRIX)
            answer_value = solution[row_value-1][column_value-1]
            if guess_value is None:
                solution_processing_message = get_response_text_for(ROW_COLUMN_IS) % (row_value, column_value, answer_value)
                set_response_text(conversation_response, [solution_processing_message])
            else:
                if answer_value == guess_value:
                    solution_processing_message = get_response_text_for(ROW_COLUMN_IS) % (row_value, column_value, guess_value)
                    set_response_text(conversation_response, [solution_processing_message])
                else:
                    solution_processing_message = get_response_text_for(ROW_COLUMN_IS_NOT) % (row_value, column_value, guess_value)
                    set_response_text(conversation_response, [solution_processing_message])
    
    return conversation_response

def process_input_image(conversation_response, session_id, bw_input_puzzle_image):

    def process_image(done_event=None):
        height, width = bw_input_puzzle_image.shape
        log('!!!!!!!!!!!!! Input image dimensions: %s x %s.' % (height, width))
        if height > MAX_IMAGE_HEIGHT:
            reduction = int(np.log2(height / MAX_IMAGE_HEIGHT)) + 1
            new_dim = (int(width / 2 ** reduction), int(height / 2 ** reduction))
            resized_image = cv2.resize(bw_input_puzzle_image, new_dim)
            height, width = resized_image.shape
            log("!!!!!!!!!!!!! Reduced input image by factor of %s. New dimensions: %s x %s." % (2**reduction, height, width))
            image_to_process = resized_image
        else:
            image_to_process = bw_input_puzzle_image

        input_matrix, image_with_ocr, image_with_lines, coordinates = \
            image_utils.extract_matrix_from_image(image_to_process, flask_app=flask_app)
        log('!!!!!!!!!!!!! finished image processing')
        log('Input matrix: %s' % input_matrix)
        now = datetime.now()
        ocr_image_filename = urllib.parse.quote('/ocr-input/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                                                            now.strftime('%H-%M-%S')))
        ocr_image_bytes = cv2.imencode('.png', image_with_ocr)
        runtime_cache.setex(ocr_image_filename, REDIS_TTL, ocr_image_bytes[1].tobytes())

        lines_image_filename = urllib.parse.quote(
            '/ocr-lines/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                        now.strftime('%H-%M-%S')))
        lines_image_bytes = cv2.imencode('.png', image_with_lines)
        runtime_cache.setex(lines_image_filename, REDIS_TTL, lines_image_bytes[1].tobytes())

        input_image_filename = urllib.parse.quote(
            '/input-image/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                        now.strftime('%H-%M-%S')))
        input_image_bytes = cv2.imencode('.png', image_to_process)
        runtime_cache.setex(input_image_filename, REDIS_TTL, input_image_bytes[1].tobytes())
        set_context(session_id, PUZZLE_INPUT_IMAGE_URL, input_image_filename)
        # Need this step to convert coordinates from int64 to int so they can me converted to string
        int_coordinates = []
        for i in range(len(coordinates)):
            new_row = []
            for j in range(len(coordinates[i])):
                new_pair = []
                for k in range(len(coordinates[i][j])):
                    new_pair.append(int(coordinates[i][j][k]))
                new_row.append(new_pair)
            int_coordinates.append(new_row)

        set_context(session_id, PUZZLE_INPUT_IMAGE_COORDINATES, int_coordinates)

        # This next step is to convert from numpy array (which can't be automatically serialized)
        # to a list, which can. If the sum of the input matrix returned from image processing is 0 is meas
        # we couldn't extract the numbers from the image
        if sum(sum(input_matrix)) > 0:
            matrix_as_list = []
            for row in input_matrix:
                new_row = []
                for number in row:
                    new_row.append(int(number))
                matrix_as_list.append(new_row)
            set_context(session_id, PUZZLE_INPUT_MATRIX, matrix_as_list)
        
        # If there is an event passed, it means that this was from an SMS and this process_image call was a forked
        # thread. 
        if done_event is not None:
            done_event.set()

    def random_response():

        responses = [
            'Hold please, I\'ll just be a minute more.',
            'I\'m thinking.',
            'Look, stop fidgiting; I\'ll figure it out.',
            'OK, I didn\'t expect that.',
            'This is harder than I thought.',
            'Oops, um, give me a moment to fix this.',
            'Do you happen to have a calculator, or even an abacus?',
            'Oooh, that cough medicine is making me a bit woozy.',
            'I probably shouldn\'t have had that third margarita last night.',
            'I\'m sorry this is taking so long, but it\'d take you longer.',
            'Frowning at me isn\'t going to make this go faster.',
            'Um, do you have an eraser?',
            'I don\'t think my prescription is working.'
        ]

        random_index = int(random.random() * len(responses))
        return responses[random_index]

    def spew_messages(done_event):
        send_sms(conversation_response, get_response_text_for(THISLL_JUST_BE_A_MINUTE) % get_response_text_for(INSULTING_NAME))
        time.sleep(TIME_SLEEP_INTERVAL)
        while not done_event.is_set():
            send_sms(conversation_response, "%s\n%s" % (random_response(), get_response_text_for(INSULTING_NAME)))
            time.sleep(TIME_SLEEP_INTERVAL)
        return

    from_number = conversation_response.get('sms_from')
    if from_number is not None:
        # Meaning this is an SMS from Twilio
        done = Event()
        spew_thread = Thread(target=spew_messages, args=(done,))
        # spew_thread.daemon = True
        spew_thread.start()
        process_image(done)
    else:
        process_image()

    conversation_response = provide_input_matrix(conversation_response, session_id)
    puzzle_input_matrix = get_context(session_id, PUZZLE_INPUT_MATRIX)
    if puzzle_input_matrix is not None and sum_matrix(puzzle_input_matrix) > 0:
        http_headers = {'Content-Type': 'application/json',
                'Accept': 'application/json'}
        data = json.dumps({'inputMatrix': get_context(session_id, PUZZLE_INPUT_MATRIX)})
        response = requests.post(SUDOKU_SOLVER_URL + 'getSolution', headers=http_headers,
                                data=data)
        if response.status_code == 200:
            results = response.json()
            set_context(session_id, PUZZLE_SOLUTION_MATRIX, results)
            if from_number is not None:
                send_sms(conversation_response, '%s\n%s' % (get_response_text_for(I_HAVE_AN_ANSWER),get_response_text_for(INSULTING_NAME)))
                conversation_response[ANSWER] = ''
                conversation_response[IMAGE_URL] = None
            else:
                add_response_text(conversation_response, [get_response_text_for(I_HAVE_AN_ANSWER)])
        else:
            if from_number is not None:
                send_sms(conversation_response, '%s\n%s' % (get_response_text_for(I_CANT_SOLVE_YOUR_PUZZLE),get_response_text_for(INSULTING_NAME)))
                conversation_response[ANSWER] = ''
                conversation_response[IMAGE_URL] = None
            else:
                add_response_text(conversation_response, [get_response_text_for(I_CANT_SOLVE_YOUR_PUZZLE)])
            if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
                delete_context(session_id, PUZZLE_SOLUTION_MATRIX)
    else:
        if from_number is not None:
            send_sms(conversation_response, '%s\n%s' % (get_response_text_for(I_CANT_SOLVE_YOUR_PUZZLE),get_response_text_for(INSULTING_NAME)))
            conversation_response[ANSWER] = ''
            conversation_response[IMAGE_URL] = None
        else:
            add_response_text(conversation_response, [get_response_text_for(I_CANT_SOLVE_YOUR_PUZZLE)])
        if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
            delete_context(session_id, PUZZLE_SOLUTION_MATRIX)

    return conversation_response

def sum_matrix(matrix):
    total = 0
    for row in matrix:
        total += sum(row)
    return total

def handle_text_input(conversation_response, session_id):
    if get_context(session_id, PUZZLE_INPUT_MATRIX) is not None:
        set_response_text(conversation_response, ['I already have a matrix to solve.',
                                    'If you want me to solve another, tell me to start over.'])
    else:
        conversation_response = process_text_input(conversation_response, session_id)
        conversation_response = provide_input_matrix(conversation_response, session_id)
        conversation_response = solve_puzzle(conversation_response, session_id)

    return conversation_response

def process_text_input(conversation_response, session_id):
    input = conversation_response[PARAMETERS][ENTITY_NUMBER]
    if len(input) > 81:
        input = np.array(input[0:81])
    else:
        if len(input) < 81:
            input = np.pad(input, (0, 81-len(input)))

    # At this point we have a valid sequence of 81 digits representing the input matrix. Now create the matrix
    input_string_index = 0
    input_matrix = []
    for row in range(0, 9):
        new_row = []
        for column in range(0, 9):
            new_row.append(int(input[input_string_index]))
            input_string_index += 1
        input_matrix.append((new_row))
    set_context(session_id, PUZZLE_INPUT_MATRIX, input_matrix)
    return conversation_response

def provide_input_matrix(conversation_response, session_id):
    input_image_id = get_context(session_id, INPUT_IMAGE_ID)
    if input_image_id is None:
        input_image_id = session_id
        set_context(session_id, INPUT_IMAGE_ID, input_image_id)
    filename = '%s.%s.png' % (input_image_id, 'input')

    input_image_url = get_context(session_id, PUZZLE_INPUT_IMAGE_URL)
    input_image_coordinates = get_context(session_id, PUZZLE_INPUT_IMAGE_COORDINATES)
    input_matrix = get_context(session_id, PUZZLE_INPUT_MATRIX)
    if input_image_url is None or input_image_coordinates is None:
        # This means input was not by means of an image or url of an image
        if input_matrix is not None:
            processed_input_image_url = generate_matrix_image(session_id, input_matrix, filename)
            conversation_response[IMAGE_URL] = processed_input_image_url
        else:
            set_response_text(conversation_response, [get_response_text_for(I_DONT_HAVE_A_PUZZLE)])
    else:
        # Input came as a texted image or a url to an image
        input_image_bytes = runtime_cache.get(input_image_url)
        image_bytearray = np.asarray(bytearray(input_image_bytes), dtype="uint8")
        input_image = cv2.imdecode(image_bytearray, cv2.IMREAD_COLOR)

        processed_input_image_url = generate_matrix_image(session_id, input_matrix, filename, input_image=input_image,
                                                input_image_coordinates=input_image_coordinates)
        conversation_response[IMAGE_URL] = processed_input_image_url

    return conversation_response

def generate_matrix_image(session_id, input_matrix, filename, input_image=None,
                          input_image_coordinates=None, solution_matrix=None):
    if solution_matrix is None:
        if input_image is None:
            image = image_utils.generate_matrix_image(input_matrix)
        else:
            image = image_utils.apply_matrix_to_image(input_matrix, input_image, input_image_coordinates)
    else:
        if input_image is None:
            image = image_utils.generate_matrix_image(input_matrix, solution_matrix=solution_matrix)
        else:
            partial_solution_matrix = np.zeros((9, 9), dtype="uint8")
            for row in range(len(solution_matrix)):
                for col in range(len(solution_matrix[row])):
                    if input_matrix[row][col] == 0:
                        partial_solution_matrix[row][col] = solution_matrix[row][col]
            image = image_utils.apply_matrix_to_image(partial_solution_matrix,
                                                      input_image,
                                                      input_image_coordinates,
                                                      show_coordinates=False)
    matrix_filename = urllib.parse.quote("/sudoku/%s" % filename)
    runtime_cache.setex(matrix_filename, REDIS_TTL, image)
    log("Saving matrix_image %s. length: %s: %s" %
          (matrix_filename, len(image), str(image[0:10])))
    matrix_image_url = '%sredis%s' % (get_context(session_id, REDIS_HOST_URL), matrix_filename)
    return matrix_image_url

def solve_puzzle(conversation_response, session_id):
    if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
        set_response_text(conversation_response, [get_response_text_for(IVE_ALREADY_SOLVED_IT)])
    else:
        if get_context(session_id, PUZZLE_INPUT_MATRIX) is  None:
            set_response_text(conversation_response, [get_response_text_for(I_DONT_HAVE_A_PUZZLE)])
        else:
            http_headers = {'Content-Type': 'application/json',
                    'Accept': 'application/json'}
            data = json.dumps({'inputMatrix': get_context(session_id, PUZZLE_INPUT_MATRIX)})
            response = requests.post(SUDOKU_SOLVER_URL + 'getSolution', headers=http_headers,
                                    data=data)
            if response.status_code == 200:
                results = response.json()
                set_context(session_id, PUZZLE_SOLUTION_MATRIX, results)
                add_response_text(conversation_response, [get_response_text_for(IVE_SOLVED_YOUR_PUZZLE)])
            else:
                add_response_text(conversation_response, [get_response_text_for(I_CANT_SOLVE_YOUR_PUZZLE)])
                if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
                    delete_context(session_id, PUZZLE_SOLUTION_MATRIX)   

    return conversation_response

def handle_url_input(conversation_response, session_id):
    if get_context(session_id, PUZZLE_SOLUTION_MATRIX) is not None:
        set_response_text(conversation_response, [get_response_text_for(IVE_ALREADY_SOLVED_IT)])
    else:
        input_puzzle_url = conversation_response[PARAMETERS].get(ENTITY_URL)
        if input_puzzle_url is not None and len(input_puzzle_url) > 0:
            if get_context(session_id, PUZZLE_INPUT_MATRIX) is not None:
                set_response_text(conversation_response, [get_response_text_for(I_ALREADY_HAVE_A_PUZZLE)])
            else:
                log('Retreiving input image \'%s\'.' % input_puzzle_url)
                response = requests.get(input_puzzle_url)
                if response.status_code == 200:
                    log('Successfully retrieved input image \'%s\'.' % input_puzzle_url)
                    input_image = response.content
                    set_context(session_id, INPUT_IMAGE_ID, session_id)
                    
                    log('!!!!!!!!!!!!! starting image processing')
                    image_bytearray = np.asarray(bytearray(input_image), dtype="uint8")
                    bw_input_puzzle_image = cv2.imdecode(image_bytearray, cv2.IMREAD_GRAYSCALE)
                    if bw_input_puzzle_image is None:
                        # This means the file or page was not a valid image
                        add_response_text(conversation_response,
                        [get_response_text_for(I_DONT_RECOGNIZE_YOUR_IMAGE)])
                    else:
                        process_input_image(conversation_response, session_id, bw_input_puzzle_image)
                else:
                    log('%s error retreiving input image \'%s\'.' % (response.status_code, input_puzzle_url))
                    add_response_text(conversation_response,
                              [get_response_text_for(I_DONT_RECOGNIZE_YOUR_IMAGE)])

        else:
            add_response_text(conversation_response, [get_response_text_for(HUH)])          

    return conversation_response

def provide_solution_matrix(conversation_response, session_id):
    input_matrix = get_context(session_id, PUZZLE_INPUT_MATRIX)
    solution_matrix = get_context(session_id, PUZZLE_SOLUTION_MATRIX)
    solution_image_url = get_context(session_id, PUZZLE_SOLUTION_IMAGE_URL)
    answer_message = None
    if input_matrix is None:
        answer_message = get_response_text_for(I_DONT_HAVE_A_PUZZLE)
    elif solution_matrix is None:
        answer_message = get_response_text_for(I_HAVENT_SOLVED_THE_PUZZLE)
    elif solution_image_url is not None:
        conversation_response[IMAGE_URL] = solution_image_url
        answer_message = get_response_text_for(TA_DA)
    else:
        filename = '%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID), 'solution')

        input_image_url = get_context(session_id, PUZZLE_INPUT_IMAGE_URL)
        input_image_coordinates = get_context(session_id, PUZZLE_INPUT_IMAGE_COORDINATES)
        if input_image_url is None or input_image_coordinates is None:
            # This means input was not by means of an image or url of an image
            solution_image_url = generate_matrix_image(session_id, input_matrix, filename, solution_matrix=solution_matrix)
        else:
            # Input came as a texted image or a url to an image
            input_image_bytes = runtime_cache.get(input_image_url)
            image_bytearray = np.asarray(bytearray(input_image_bytes), dtype="uint8")
            input_image = cv2.imdecode(image_bytearray, cv2.IMREAD_COLOR)
            solution_image_url = generate_matrix_image(session_id, input_matrix, filename, input_image=input_image,
                                                       input_image_coordinates=input_image_coordinates,
                                                       solution_matrix=solution_matrix)
        conversation_response[IMAGE_URL] = solution_image_url
        set_context(session_id, PUZZLE_SOLUTION_IMAGE_URL, solution_image_url)
        answer_message = get_response_text_for(TA_DA)


    set_response_text(conversation_response, [answer_message])
    return conversation_response

def start_over(conversation_response, session_id):
    delete_context(session_id, PUZZLE_INPUT)
    delete_context(session_id, PUZZLE_INPUT_MATRIX)
    delete_context(session_id, PUZZLE_INPUT_IMAGE_URL)
    delete_context(session_id, PUZZLE_INPUT_IMAGE_COORDINATES)
    delete_context(session_id, PUZZLE_SOLUTION_MATRIX)
    delete_context(session_id, PUZZLE_SOLUTION_IMAGE_URL)
    delete_context(session_id, INPUT_IMAGE_ID)
    delete_context(session_id, PUZZLE_ASYNC_JOB_ID)
    return conversation_response

def call_me(conversation_response, session_id):
    new_call_me = None
    person_entity = conversation_response[PARAMETERS].get(ENTITY_PERSON)
    if person_entity is not None:
        new_call_me = person_entity.get(ENTITY_PERSON_NAME)
    if new_call_me is not None and len(new_call_me) > 0:
        set_context(session_id, PUZZLE_CALL_ME, new_call_me)
        set_response_text(conversation_response, [get_response_text_for(I_WILL_NOW_CALL_YOU) % new_call_me])
    else:
        input_text = conversation_response[INPUT]
        if input_text is not None and len(input_text) > 0:
            found = input_text.find('all me')
            if found > 0:
                new_call_me = input_text[found+6:len(input_text)]
                found = new_call_me.find(',')
                if found > 0:
                    new_call_me = new_call_me[0:found]
            else: 
                new_call_me = input_text
            new_call_me = new_call_me.strip()
            set_context(session_id, PUZZLE_CALL_ME, new_call_me)
            set_response_text(conversation_response, [get_response_text_for(I_WILL_NOW_CALL_YOU) % new_call_me])
        else:
            set_response_text(conversation_response, [get_response_text_for(HUH)])
    return conversation_response

def call_me_fallback(conversation_response, session_id):
    new_call_me = conversation_response[INPUT].strip()
    set_context(session_id, PUZZLE_CALL_ME, new_call_me)
    set_response_text(conversation_response, [get_response_text_for(I_WILL_NOW_CALL_YOU) % new_call_me])
    return conversation_response

def set_response_text(conversation_response, list_of_texts):
    conversation_response[ANSWER] = list_of_texts[0] 
    if len(list_of_texts) > 1:
        add_response_text(conversation_response, list_of_texts[1:])
    return conversation_response

def add_response_text(conversation_response, list_of_texts):
    for text in list_of_texts:
        if len(conversation_response[ANSWER]) == 0:
            conversation_response[ANSWER] = text
        else:
            conversation_response[ANSWER] = conversation_response[ANSWER] + '\n%s' % text
    return conversation_response

def get_redis_context_key(session_id):
    return "/context/%s.json" % session_id

def get_context_from_redis(session_id):
    redis_context_key = get_redis_context_key(session_id)
    context_string = runtime_cache.get(redis_context_key)
    if context_string is None:
        context = {}
    else:
        context = json.loads(context_string)
    return context

def put_context_to_redis(session_id, context):
    redis_context_key = get_redis_context_key(session_id)
    runtime_cache.setex(redis_context_key, REDIS_TTL, json.dumps(context))
    return context

def get_context(session_id, key):
    context = get_context_from_redis(session_id)
    return context.get(key)

def set_context(session_id, key, value):
    context = get_context_from_redis(session_id)
    context[key] = value
    put_context_to_redis(session_id, context)

def delete_context(session_id, key):
    context = get_context_from_redis(session_id)
    value = context.get(key)
    if value is not None:
        context.pop(key)
    put_context_to_redis(session_id, context)

def get_response_text_for(text_response_type):
    if text_response_type == INSULTING_NAME:
        values = [
            'Fartface', 'Dick nose', 'Butthead', 'Dumb ass', 'Bonehead',
            'Dipshit', 'Shithead', 'Doofus']
    elif text_response_type == TA_DA:
        values = ['Ta Da!', 'Viola!', 'Hold the applause', '[mic drop]', 'Woo Hoo!']
    elif text_response_type == I_CANT_HEAR_YOU:
        values = [
            'Speak up, I can\'t hear you.',
            'What\'d you say?',
            'Speak louder.',
            'I\'m not hearing you.',
            'Huh?']
    elif text_response_type == I_HAVE_AN_ANSWER:
        values = [
            'I have an answer to this puzzle.',
            'I know the solution to this.',
            'That was easy, I know the answer.',
            'I have a solution to this.',
            'I know the answer to this puzzle.'
        ]
    elif text_response_type == I_CANT_SOLVE_YOUR_PUZZLE:
        values = [
            'I can\'t solve your puzzle, through no fault of mine',
            'That\'s a bogus puzzle.',
            'Even Einstein couldn\'t solve your stupid puzzle.',
            'Get a real puzzle.',
            'Even with my super powers, your puzzle is beyond hope.'
        ]
    elif text_response_type == I_DONT_HAVE_SOMETHING_TO_FIX:
        values = [
            'I don\'t have a matrix to fix.',
            'I need your input first. I don\' have anything to fix.',
            'Give me your input first.',
            'You\'re questioning my integrity before you\'ve given me something to solve.',
            'I don\'t yet have anything from you to fix.'
        ]
    elif text_response_type == I_NEED_ROW_AND_COLUMN_TO_FIX:
        values = [
            'I need both a row and column number to fix your input.',
            'If you want me to fix your input, I need both a row and column.',
            'I\'m assuming you want me to fix your input. I need row and column.',
            'Which row AND column?',
            'Both row and column please.'
        ]
    elif text_response_type == I_NEED_ROW_AND_COLUMN_TO_HINT:
        values = [
            'I need both a row and column number to provide a hint.',
            'If you want a hint, I need a row and column.',
            'I\'m assuming you want a hint. I need row and column.',
            'Which row AND column?',
            'Both row and column please.'
        ]
    elif text_response_type == I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_FIX:
        values = [
            'I need a row, column, and new value only to fix your matrix.',
            'Three numbers please, row, column, and new value.',
            'I don\'t have a magic eight ball; row, column, and new value, please.',
            'I don\'t have a ouiji board; give me a row, column, and new value to fix your input.',
            'If you want me to fix your input, give me the row column and new value.'
        ]
    elif text_response_type == I_NEED_ROW_COLUMN_AND_NEW_VALUE_TO_HINT:
        values = [
            'I need a row, column, your guess only.',
            'Three numbers please, row, column, and your guess.',
            'I don\'t have a magic eight ball; row, column, and suspected value, please.',
            'I don\'t have a ouiji board; give me a row, column, and your guess.',
            'If you want a hint, give me the row column and your guess.'
        ]
    elif text_response_type == ROW_COLUMN_IS_ALREADY:
        values = [
            'Row %s column %s is already %s.',
            'Row %s column %s currently is %s.',
            'Nothing to fix here, row %s column %s is %s.',
            'Row %s column %s is %s.',
            'Cell %s, %s is %s, duh.'
        ]
    elif text_response_type == ROW_COLUMN_IS_NOW:
        values = [
            'Row %s column %s is now %s.',
            'I\'ve made row %s column %s %s.',
            'Fixed! Cell %s %s is now %s.',
            'Cell %s %s is now %s. Please do better next time.',
            'Row %s column %s is changed to %s.'
        ]
    elif text_response_type == I_DONT_HAVE_A_PUZZLE:
        values = [
            'I don\'t yet have a puzzle to solve for you.',
            'You haven\'t yet given me a puzzle to solve.',
            'I first need your input.',
            'I don\'t yet have a puzzle to solve for you. Give me a little help here',
            'You gotta give me something to work with first.',
            'I first need the puzzle you want me to solve.'
        ]
    elif text_response_type == YOU_NEED_TO_ASK_ME_TO_SOLVE:
        values = [
            'You need to ask me to solve the puzzle first before you can ask for a hint.',
            'Before I can give you a hint, you need to ask me to solve the puzzle.',
            'I need to solve the puzzle first and you haven\'t asked me to.',
            'I\'ve no hints for you because I haven\'t solved the puzzle.',
            'Ask me to solve the puzzle first'
        ]
    elif text_response_type == I_HAVENT_SOLVED_THE_PUZZLE:
        values = [
            'I first need to solve the puzzle.',
            'You need to ask me to solve the puzzle.',
            'I need to solve the puzzle first and you haven\'t asked me to.',
            'I haven\'t solved the puzzle yet.',
            'Ask me to solve the puzzle first'
        ]
    elif text_response_type == ROW_COLUMN_IS:
        values = [
            'Row %s column %s is %s.',
            'The answer to row %s column %s is %s.',
            'Cell %s %s is %s.',
            'The value in row %s column %s is %s.',
            'Puzzle row %s column %s is %s.'
        ]
    elif text_response_type == ROW_COLUMN_IS_NOT:
        values = [
            'Row %s column %s is not %s.',
            'The answer to row %s column %s is not %s.',
            'Cell %s %s is not %s.',
            'The value in row %s column %s is not %s.',
            'Puzzle row %s column %s is not %s.'          
        ]
    elif text_response_type == THISLL_JUST_BE_A_MINUTE:
        values = [
            'OK, this\'ll just be a minute.\n%s',
            'I got this, one moment.\n%s',
            'Give me a second to work on this.\n%s',
            'One moment please.\n%s',
            'Right. Give me a minute to figure this out.\n%s'
        ]
    elif text_response_type == IVE_ALREADY_SOLVED_IT:
        values = [
            'I\'ve already solved your puzzle. You can ask me to start over.',
            'I\'ve solved this. Ask me to start over if you want a new puzzle.',
            'I already know this answer. Ask me to start over if you want.',
            'I\'ve solve this already. You can ask me to start over.',
            'Duh, I already know this answer. Ask me to start over if you want.'
        ]
    elif text_response_type == I_ALREADY_HAVE_A_PUZZLE:
        values = [
            'I already have a puzzle to solve. You can ask me to solve this or start over.',
            'I think you\'re trying to give me a puzzle to solve and I already have one.',
            'I have an input puzzle. I can solve this or I can start over.',
            'You\'ve already given me a puzzle to solve. I can solve this one or start over.',
            'I have your input. I can start again or solve what you\'ve given me.'
        ]
    elif text_response_type == IVE_SOLVED_YOUR_PUZZLE:
        values = [
            'Hah, I\'ve solved your puzzle.',
            'I have it, I know the answer!', 
            'Done. That was easy peasy.',
            'Finished. Give me something a bit harder next time.',
            'I know that answer, not terribly surprising though.'
        ]
    elif text_response_type == I_DONT_RECOGNIZE_YOUR_IMAGE:
        values = [
            'I\'m sorry, I don\'t recognize your input as an image. If it\'s a GIF, we don\'t do GIFs, they\'re for losers.',
            'That\'s not an image (GIFs don\'t count).',
            'I don\'t see an image in your input. I don\'t do GIFs.',
            'I need a better image from you. BTW, GIFs are for losers.',
            'I don\'t understand your input at all, it may be because it\'s a GIF.'
        ]
    elif text_response_type == I_WILL_NOW_CALL_YOU:
        values = [
            'Fine. I will now call you \'%s\'.',
            'OK, you will now be called \'%s\'.',
            'Right. Henceforth you shall be \'%s\'.',
            'Right. From now on you shall be know as \'%s\'.',
            'Got it. Your name is now \'%s\'.'
        ]
    elif text_response_type == HUH:
        values = [
            'Huh, what did you say?',
            'What?',
            'I don\'t understand',
            'I didn\'t get that.',
            'Come again?'
        ]
    elif text_response_type == I_CANT_FIND_YOUR_INPUT:
        values = [
            ''
        ]
    choice = int(random.random() * len(values))
    return values[choice]

def send_sms(conversation_response, msg):
    from_number = conversation_response.get('sms_from')
    image_url = conversation_response.get(IMAGE_URL)
    if from_number is not None:
        message = twilio_client.messages.create(
            body=msg,
            from_=TWILIO_PHONE_NUMBER,
            to=from_number
            )
        if image_url is not None:
            message = twilio_client.messages.create(
                from_=TWILIO_PHONE_NUMBER,
                media_url=image_url,
                to=from_number
            )
        return message.sid
    else:
        return None

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    flask_app.run(debug=False, port=server_port, host='0.0.0.0')
