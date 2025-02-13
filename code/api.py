## 负责与GLM的API进行交互，执行函数调用

import json
from zhipuai import ZhipuAI
import tools
import functions
import prompts

table_meta_file = "meta.json"

def get_answer(question,parent_answers):
    """
    获得复杂问题的答案
    """
    tasks = get_task_decomposition(question)
    taskid_to_answer = {}
    for task in tasks:
        parent_answers = []
        for parent in task["parents"]:
            if taskid_to_answer[parent] is not None:
                parent_answers.append(taskid_to_answer[parent])
        task_answer = get_atomic_answer(task["question"], parent_answers,tools.tools)
        taskid_to_answer[task["id"]] = task_answer
    return taskid_to_answer[tasks[-1]["id"]]

def get_atomic_answer(question, parent_answers,tools):
    """
    获得原子问题的答案
    """
    table_meta_list = get_table_meta(question)
    messages = [
            {
                "role": "system",
                "content": prompts.get_prompt_atomic_question(),
            },
            {
                "role": "user",
                "content": f"{str(table_meta_list)}\n{parent_answers.join("\n")}\n{question}",
            },
        ],
    response = simple_completion(messages,tools)
    messages.append(response.choices[0].message.model_dump())
    function_results = []
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        function_name = tool_call.function.name
        if function_name in functions.function_map:
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
        ]
    )
    tasks = json.loads(response.choices[0].message.content)
    return tasks


def get_table_meta(question):
    """
    获得问题所需的数据表
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        table_data = json.load(file)
    prompt = f"""我有如下数据表：<{str(table_data)}>，
    现在基于数据表回答问题：{question}，请分析需要哪些数据表；仅返回需要的数据表名，无需展示分析过程。
    """
    messages = [{"role": "user", "content": prompt}]
    response = simple_completion(messages)
    chosen_table_name = str(response.choices[0].message.content)
    table_meta_list = [
        item for item in table_data if item["数据表名"] in chosen_table_name
    ]
    return table_meta_list

def simple_completion(messages,tools, model="glm-4-plus"):
    """
    获得一次对话的回复
    """
    client = ZhipuAI()
    response = client.chat.completions.create(
        model=model, 
        stream=False, 
        messages=messages,
        tools=tools,
    )
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
