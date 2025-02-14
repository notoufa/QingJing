"""负责与GLM的API进行交互，执行函数调用"""

import json
from zhipuai import ZhipuAI
import tools
import functions
import prompts
import logger
import os
from utils import parse_res


def check_api_key():
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ZHIPUAI_API_KEY is not set. Please set the environment variable."
        )
    return api_key


def get_answer(question):
    """
    获得复杂问题的答案
    """
    assumption, tasks = get_task_decomposition(question)
    taskid_to_answer = {}
    for task in tasks:
        parent_answers = []
        for parent in task["parents"]:
            if taskid_to_answer.get(parent):
                parent_answers.append(taskid_to_answer[parent])
        task_answer = get_atomic_answer(
            task["question"], parent_answers, tools.tools, assumption
        )
        taskid_to_answer[task["id"]] = task_answer
    final_answer = taskid_to_answer[tasks[-1]["id"]]
    return final_answer
    # messages = [
    #     {
    #         "role": "system",
    #         "content": "请你按照原始问题的要求，调整答案中数值、时间、单位等格式",
    #     },
    #     {"role": "user", "content": f"原始问题：{question}\n答案：{final_answer}"},
    # ]
    # res = get_completion(messages)
    # return res.choices[0].message.content


def get_task_decomposition(question):
    """
    获得问题的分解结果
    """
    logger.info("【获取问题分解结果】", question)
    messages = [
        {"role": "system", "content": prompts.get_prompt_task_decomposition(question)},
        {"role": "user", "content": question},
    ]
    response = get_completion(messages, tools.tools)
    res = json.loads(parse_res(response.choices[0].message.content))
    assumption = None if not res.get("assumption") else res["assumption"]
    logger.success("【问题分解结果】", res)
    return assumption, res["subtasks"]


def get_atomic_answer(question, parent_answers, tools, assumption=None):
    """
    获得原子问题的答案
    """
    table_meta_list = get_table_meta(question)
    logger.info("【获取原子问题答案】", question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_atomic_question(
                question, table_meta_list, parent_answers, assumption
            ),
        },
    ]
    response = get_completion(messages, tools)
    messages.append(response.choices[0].message.model_dump())
    function_results = []
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        function_name = tool_call.function.name
        if function_name in functions.function_map:
            logger.info("【执行工具函数】", function_name, ", 参数:", args)
            function_result = functions.function_map[function_name](**args)
            logger.success("【工具函数执行结果】", function_result)
            function_results.append(function_result)
            messages.append(
                {
                    "role": "tool",
                    "content": f"{function_result}",
                    "tool_call_id": tool_call.id,
                }
            )
            response = get_completion(messages)
    res = parse_res(response.choices[0].message.content)
    logger.success("【原子问题答案】", res)
    return res


def get_table_meta(question):
    """
    获得问题所需的数据表的元信息
    """
    logger.info("【获取原子问题所需数据表】", question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_get_table_meta(question),
        },
    ]
    response = get_completion(messages)
    chosen_table_names = json.loads(parse_res(response.choices[0].message.content))
    logger.success("【原子问题所需数据表】", chosen_table_names)
    table_meta_list = prompts.get_table_meta_by_table_names(chosen_table_names)
    return table_meta_list


def get_completion(messages, tools=[], model="glm-4-plus"):
    """
    获得对话结果
    """
    client = ZhipuAI(api_key=check_api_key())
    logger.trace("【请求回答】", str(messages))
    response = client.chat.completions.create(
        model=model,
        stream=False,
        messages=messages,
        tools=tools,
    )
    logger.trace("【回答结果】", str(response))
    return response
    # import deepseek
    # return deepseek.request(messages, tools)
