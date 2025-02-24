import json

tools = []
tools_description = []

tools_file = "knowledge/tools.json"
tools_description_file = "knowledge/tools_description.json"


def load_tools():
    global tools, tools_description
    try:
        with open(tools_file, "r", encoding="utf-8") as f:
            tools = json.load(f)
    except FileNotFoundError:
        print(f"Error: {tools_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {tools_file}.")

    try:
        with open(tools_description_file, "r", encoding="utf-8") as f:
            tools_description = json.load(f)
    except FileNotFoundError:
        print(f"Error: {tools_description_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {tools_description_file}.")
