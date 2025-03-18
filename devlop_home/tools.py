import json

tools = []
tools_description = []

tools_file = "devlop_home/knowledge/tools.json"
tools_description_file = "devlop_home/knowledge/tools_description.json"

calculate_tools_name = [
    "perform_math_operations",
    "convert_seconds_to_time",
    "calculate_duration",
    "sort_only_by_time",
    "calculate_list_length",
]


def get_calculate_tools() -> list[dict]:
    return [item for item in tools if item["function"]["name"] in calculate_tools_name]


def tools_description_str(tools: list[str] = None) -> str:
    if tools is None:
        tools = tools_description
    desc_strs = []
    for idx, item in enumerate(tools):
        desc_str = f"{idx + 1}. 函数名称：{item['function_name']}，输入：{item['input']}，输出：{item['output']}"
        if item.get("notices"):
            desc_str += f"，【注意】：{item['notices']}"
        if item.get("example"):
            desc_str += f"，【示例问题】：{item['example']}"
        desc_strs.append(desc_str)
    return "\n".join(desc_strs)


def tools_description_str_by_names(tool_names: list[str]) -> str:
    need_tools_description = [
        item for item in tools_description if item["function_name"] in tool_names
    ]
    return tools_description_str(need_tools_description)


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
