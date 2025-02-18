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


def get_answer(question, n=3):
    """
    获得复杂问题的答案
    """
    assumption, format_requirement, contains_time, subtasks = get_task_decomposition(
        question
    )

    def get_task_by_id(id):
        for task in subtasks:
            if task["id"] == id:
                return task
        return None

    for task in subtasks:
        parent_tasks = []
        for parent in task["parent_ids"]:
            parent = get_task_by_id(parent)
            if parent:
                parent_tasks.append(
                    {
                        "question": parent["question"],
                        "answer": parent["answer"],
                        "function_results": parent["function_results"],
                    }
                )

        answer, function_results = get_atomic_answer(
            task["question"], parent_tasks, assumption, contains_time
        )
        task["answer"] = answer
        task["function_results"] = function_results
    summary = {
        "question": question,
        "assumption": assumption,
        "format_requirement": format_requirement,
        "subtasks": subtasks,
    }
    return get_summary(summary)


def get_summary(summary):
    """
    获得问题总结的答案
    """
    logger.info("【问题总结】", summary)
    messages = [
        {"role": "user", "content": prompts.get_prompt_summary_question(summary)},
    ]
    response = get_completion(messages)
    return response.choices[0].message.content


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
    assumption = res["assumption"]
    format_requirement = res.get("format_requirement")
    contains_time = res.get("contains_time")
    subtasks = res.get("subtasks")
    logger.success("【问题分解结果】", res)
    return assumption, format_requirement, contains_time, subtasks


def get_atomic_answer(question, parent_tasks, assumption=None, contains_time=True):
    """
    获得原子问题的答案
    """
    table_meta_list, tool_list = get_table_meta_and_tool(
        question, contains_time, parent_tasks, assumption
    )
    logger.info("【开始获取原子问题答案】", question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_atomic_question(
                question, table_meta_list, parent_tasks, assumption
            ),
        },
    ]
    response = get_completion(messages, tool_list)
    messages.append(response.choices[0].message.model_dump())
    # 循环调用函数
    function_results = []
    max_iterations = 1
    for _ in range(max_iterations):
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                if function_name in functions.function_map.keys():
                    logger.info("【开始执行工具函数】", function_name, ", 参数:", args)
                    function_result = functions.function_map[function_name](**args)
                    function_results.append(function_result)
                    logger.success("【工具函数执行结果】", function_result)
                    messages.append(
                        {
                            "role": "tool",
                            "content": f"{function_result}",
                            "tool_call_id": tool_call.id,
                        }
                    )
            response = get_completion(messages, tool_list)
        else:
            break
    res = parse_res(response.choices[0].message.content)
    logger.success("【原子问题答案】", res)
    return res, function_results


def get_table_meta_and_tool(
    question, contains_time=True, parent_tasks=[], assumption=None
):
    """
    获得问题所需的数据表的元信息和所需工具
    """
    logger.info("【开始获取原子问题所需数据表和工具】", question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_get_table_meta_and_tool(
                question, parent_tasks, assumption
            ),
        },
    ]
    response = get_completion(messages)
    res = json.loads(parse_res(response.choices[0].message.content))
    tables = res.get("tables", [])
    need_tools = res.get("tools", [])
    if not contains_time and "设备参数详情表" not in tables:
        tables.append("设备参数详情表")
    logger.success("【原子问题所需数据表】", tables, "【所需工具】", need_tools)
    table_meta_list = prompts.get_table_meta_by_table_names(tables)
    tool_list = []
    for tool in tools.tools:
        if tool["function"]["name"] in need_tools:
            tool_list.append(tool)
    return table_meta_list, tool_list


def get_completion(messages, tools=[], model="glm-4-plus"):
    """
    获得对话结果
    """
    client = ZhipuAI(api_key=check_api_key())
    logger.trace("【请求回答】", str(messages), "【工具】", str(tools))
    response = client.chat.completions.create(
        model=model,
        stream=False,
        messages=messages,
        tools=tools,
    )
    logger.trace("【回答结果】", str(response))
    return response
