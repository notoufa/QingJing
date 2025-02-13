## 负责与GLM的API进行交互，执行函数调用

import json
import requests
from zhipuai import ZhipuAI
import tools
import functions
import prompts

table_meta_file = "meta.json"


def get_answer(question):
    """
    获得复杂问题的答案
    """
    tasks = get_task_decomposition(question)
    taskid_to_answer = {}
    for task in tasks:
        parent_answers = []
        for parent in task["parents"]:
            if taskid_to_answer.get(parent):
                parent_answers.append(taskid_to_answer[parent])
        task_answer = get_atomic_answer(task["question"], parent_answers, tools.tools)
        taskid_to_answer[task["id"]] = task_answer
    return taskid_to_answer[tasks[-1]["id"]]


def get_atomic_answer(question, parent_answers, tools):
    """
    获得原子问题的答案
    """
    table_meta_list = get_table_meta(question)
    print("开始获取原子问题的答案:", question)
    table_meta_list_content = (
        f"已知数据表结构：{str(table_meta_list)}" if len(table_meta_list) > 0 else ""
    )
    parent_answers_content = (
        f"已知：{str(parent_answers)}" if len(parent_answers) > 0 else ""
    )
    question_content = f"请回答以下问题：{question}，你自己仔细思考判断，思考完成后，不需要返回思考过程，只需以一句话给出问题的答案"
    content = "\n".join(
        [table_meta_list_content, parent_answers_content, question_content]
    )
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_atomic_question(),
        },
        {
            "role": "user",
            "content": content,
        },
    ]
    response = simple_completion(messages, tools)
    print("问题答案:", response.choices[0].message.content)
    res_content = parse_res(response.choices[0].message.content)
    messages.append(
        {
            "role": "assistant",
            "content": res_content,
        }
    )
    function_results = []
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        function_name = tool_call.function.name
        if function_name in functions.function_map:
            print("开始执行工具函数:", function_name)
            function_result = functions.function_map[function_name](**args)
            function_results.append(function_result)
            messages.append(
                {
                    "role": "tool",
                    "content": f"{function_result}",
                    "tool_call_id": tool_call.id,
                }
            )
            response = simple_completion(messages)
    return response.choices[0].message.content


def get_task_decomposition(question):
    """
    获得问题的分解结果
    """
    print("开始获取问题的分解结果:", question)
    response = simple_completion(
        [
            {
                "role": "system",
                "content": prompts.get_prompt_task_decomposition(),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        [],
    )
    tasks = json.loads(parse_res(response.choices[0].message.content))
    print("问题的分解结果:", tasks)
    return tasks


def get_table_meta(question):
    """
    获得问题所需的数据表
    """
    print("开始获取问题所需的数据表:", question)
    with open(table_meta_file, "r", encoding="utf-8") as file:
        table_data = json.load(file)
    prompt = f"""
    我有如下数据表：<{str(table_data)}>，
    现在基于数据表回答问题：{question}，请分析需要哪些数据表
    仅返回需要的数据表名列表，无需给出思考过程，示例：["Ajia_plc_1"]
    """
    messages = [{"role": "user", "content": prompt}]
    response = simple_completion(messages, [])
    # 将如["Ajia_plc_1"]的字符串转换为列表
    res = parse_res(response.choices[0].message.content)
    chosen_table_names = json.loads(res)
    print("问题所需的数据表:", chosen_table_names)
    table_meta_list = [
        item for item in table_data if item["数据表名"] in chosen_table_names
    ]
    return table_meta_list


def simple_completion(messages, tools, model="glm-4-plus"):
    """
    获得一次对话的回复
    """
    # client = ZhipuAI()
    # response = client.chat.completions.create(
    #     model=model,
    #     stream=False,
    #     messages=messages,
    #     tools=tools,
    # )
    # return response
    import deepseek

    response = deepseek.request(messages, tools)
    return response


def complex_completion(messages, tools, max_attempts=8, model="glm-4-plus"):
    client = ZhipuAI()
    for _ in range(max_attempts):
        response = client.chat.completions.create(
            model=model,
            stream=False,
            messages=messages,
            tools=tools,
        )
        if (
            response.choices
            and response.choices[0].message
            and response.choices[0].message.content
        ):
            if "```python" in response.choices[0].message.content:
                continue
            else:
                break
        else:
            return response
    return response


def parse_res(res):
    """
    解析结果
    """
    try:
        res = res.split("</think>")[1]
        res = res.split("```json")[1]
        res = res.split("```")[0]
        res = res.strip()
    except Exception:
        pass
    return res
