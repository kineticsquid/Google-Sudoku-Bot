import json
import argparse

parser = argparse.ArgumentParser(
    description='Morphs Assistant training data for DialogFlow')
# Add arguments
parser.add_argument(
    '-f', '--file', type=str, help='Path of input file. ', required=True)

args = parser.parse_args()
input_file_path = args.file
input_file = open(input_file_path, 'r')
input_text = input_file.read()
input_json = json.loads(input_text)
intents_json = []
for intent in input_json['intents']:
    new_intent = {}