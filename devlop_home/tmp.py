# coding=utf-8

import json

import time
import sys
import jsonlines


def dump_2_report_answer(info, path):
    with open(path, 'w') as output_json_file:
        json.dump(info, output_json_file, ensure_ascii=False, indent=4)

def dump_jsonl(info, path):
    with jsonlines.open(path, "w") as json_file:
        for obj in info:
            json_file.write(obj)

def read_jsonl(path):
    content = []
    with jsonlines.open(path, "r") as json_file:
        for obj in json_file.iter(type=dict, skip_invalid=True):
            content.append(obj)
    return content

if __name__ == "__main__":
    '''
      online devlop 
    '''
    in_param_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(in_param_path, 'r') as load_f:
        input_params = json.load(load_f)

    questionFile = input_params["fileData"]["questionFilePath"]
    print("Read standard from %s" % questionFile)
    time.sleep(1)
    question_labels = []
    try:
        question_labels = read_jsonl(questionFile)
        for question in question_labels:
            print(question)

    except json.JSONDecodeError as e:
        print("Error: %s" % e)
        sys.exit()

    try:
        dump_jsonl(question_labels, out_path)
    except Exception as e:
        print("Error: %s" % e)
        sys.exit(1)
