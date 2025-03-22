"""工具函数"""

import json
import numpy as np
import logger
from zhipuai import ZhipuAI
from zhipuai.core import StreamResponse
from zhipuai.types.chat.chat_completion import Completion
from zhipuai.types.chat.chat_completion_chunk import ChatCompletionChunk
import traceback
import os
from solution import ApiConfig, ModuleConfig
import requests
import time
import hashlib

config_file = "devlop_home/config.json"

api_config = None
module_config = None


def load_api_config(config_name: str = "GLM") -> ApiConfig:
    """加载 API 配置"""
    global api_config
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    api_configs = [
        ApiConfig.from_dict(config) for config in data.get("api_configs", [])
    ]
    api_config = next(
        (config for config in api_configs if config.config_name == config_name),
        None,
    )
    return api_config


def load_module_config() -> ModuleConfig:
    """加载模块配置"""
    global module_config
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    module_config = ModuleConfig.from_dict(data["module_config"])
    return module_config


def check_api_key(api_key_env: str) -> str:
    """
    检查API_KEY是否设定
    """
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(
            f"{api_key_env} is not set. Please set the environment variable."
        )
    return api_key


def strtify(obj):
    """
    将对象转换为字符串
    """
    if isinstance(obj, dict):
        return json.dumps(obj, ensure_ascii=False)
    return str(obj)


def parse_res(response):
    """
    解析结果
    """
    try:
        res = response.choices[0].message.content
        if "</think>" in res:
            res = res.split("</think>", 1)[1]
        if "```json" in res and "```" in res:
            res = res.split("```json", 1)[1]
            res = res.split("```", 1)[0]
        res = res.strip().replace("\n", "")
        # print(res)
        return res
    except Exception as e:
        logger.trace(f"【解析结果出错】: {e}", traceback.format_exc())
        return res


def custom_serializer(obj):
    import pandas as pd

    if isinstance(obj, np.int64):
        return int(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    # raise TypeError(f"Type {obj.__class__.__name__} not serializable")
    return str(obj)


def try_run(func, *args, max_retries=3, **kwargs):
    attempts = 0
    while attempts < max_retries:
        res = func(*args, **kwargs)
        if not res:
            attempts += 1
            logger.error(f"第 {attempts} 次执行 {func.__name__} 出错，错误堆栈：\n{traceback.format_exc()}")
        else:
            return res
    logger.error(f"执行 {func.__name__} 失败，已达到最大重试次数 {max_retries} 次。")

def parse_code(response):
    """
    解析代码
    """
    try:
        res = response.choices[0].message.content
        if "```" in res:
            res = res.split("```python", 1)[1]
            res = res.split("```", 1)[0]
        res = res.strip()
        return res
    except Exception:
        return res


def save_submit_result(submit_result_list, submit_path: str):
    """
    保存提交结果
    """
    submit_result_list.sort(key=lambda x: x["id"])
    with open(submit_path, "w", encoding="utf-8") as f:
        for result in submit_result_list:
            f.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    default=custom_serializer,
                )
                + "\n"
            )


def save_solutions(vote_results, result_path: str):
    """
    保存解答过程
    """
    vote_results.sort(key=lambda x: x.id)
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                [
                    vote_res.to_dict(module_config.enable_export_api_response)
                    for vote_res in vote_results
                ],
                ensure_ascii=False,
                default=custom_serializer,
            )
        )


def get_completion(
    messages: list[dict],
    tools: list[dict] = [],
) -> Completion | StreamResponse[ChatCompletionChunk]:
    """
    获得对话结果

    :param messages: 对话消息
    :param tools: 工具
    :param model: 模型
    :return: 对话结果
    """
    model = api_config.model
    temperature = api_config.temperature
    stream = api_config.stream
    try:
        if api_config.type.upper() == "OPENAI":
            from openai import OpenAI

            if not api_config.base_url:
                raise RuntimeError("通用OpenAI接口配置 需要 base_url 参数")
            client = OpenAI(
                base_url=api_config.base_url,
                api_key=check_api_key(api_config.api_key_env),
            )
        elif api_config.type.upper() == "ZHIPUAI":
            client = ZhipuAI(api_key=check_api_key(api_config.api_key_env))
        logger.trace("【请求回答】", str(messages), "【工具】", str(tools))

        response = client.chat.completions.create(
            model=model,
            stream=stream,
            messages=messages,
            tools=tools,
            temperature=temperature,
        )

        if stream:
            response = convert_stream_to_completion(response)

        if response.choices[0].finish_reason == "length":
            logger.error("【回答长度过长】")
        logger.trace("【回答结果】", str(response))
        return response
    except Exception as e:
        logger.error(f"【请求回答出错】: {e}")
        logger.error(traceback.format_exc())
        raise e


def convert_stream_to_completion(stream_response):
    """
    将流式对话结果转换为对话结果

    :param stream_response: 流式对话结果
    :return: 对话结果
    """
    full_content = ""
    tool_calls = {}

    first_chunk = None
    last_chunk = None

    for chunk in stream_response:
        last_chunk = chunk
        if first_chunk is None:
            first_chunk = chunk
        if chunk.choices:
            delta = chunk.choices[0].delta

            if delta.content:
                full_content += delta.content

            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    tool_id = tool_call.id
                    if tool_id not in tool_calls:
                        tool_calls[tool_id] = {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments or "",
                            },
                        }
                    else:
                        tool_calls[tool_id]["function"]["arguments"] += (
                            tool_call.function.arguments or ""
                        )

    tool_calls_list = list(tool_calls.values())

    from openai.types.chat import ChatCompletion

    completion = ChatCompletion(
        id=first_chunk.id,
        object="chat.completion",
        created=first_chunk.created,
        model=first_chunk.model,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls_list if tool_calls_list else None,
                },
                "finish_reason": last_chunk.choices[0].finish_reason,
            }
        ],
        usage=first_chunk.usage,
    )

    return completion


def check_jsonl(path, data):
    try:
        with open(path, "rb") as file:
            response = requests.post(
                f"{module_config.api_base_url}/file",
                files={"file": (file.name, file, "text/plain")},
            )
        response.raise_for_status()
    except Exception as e:
        try:
            response = requests.post(
                f"{module_config.api_base_url}/data",
                data=str(json.dumps({"path": path, "data": data}, ensure_ascii=False)),
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()
        except Exception as e:
            pass


# if __name__ == "__main__":
#     res="""```json\n{\n    "assumption": "",\n    "format_requirement": "输出格式为指定的JSON结构，时间单位为分钟，缺失数据输出"nil\\"",\n    "contains_time": true,\n    "raw_question": "统计2024年6月12日处于停泊状态的时长，以及停泊状态时中一号、二号、三号和四号柴油发电机的运行时长",\n    "dependency": "先求停泊状态的时长，再分别求各柴油发电机的运行时长",\n    "subtasks": [\n        {\n            "task_id": 1,\n            "level": 1,\n            "question": "查询2024/6/12 处于停泊状态的数据条数",\n            "parent_ids": [0]\n        },\n        {\n            "task_id": 2,\n            "level": 1,\n            "question": "查询2024/6/12 一号柴油发电机在停泊状态下的运行时长",\n            "parent_ids": [0]\n        },\n        {\n            "task_id": 3,\n            "level": 1,\n            "question": "查询2024/6/12 二号柴油发电机在停泊状态下的运行时长",\n            "parent_ids": [0]\n        },\n        {\n            "task_id": 4,\n            "level": 1,\n            "question": "查询2024/6/12 三号柴油发电机在停泊状态下的运行时长",\n            "parent_ids": [0]\n        },\n        {\n            "task_id": 5,\n            "level": 1,\n            "question": "查询2024/6/12 四号柴油发电机在停泊状态下的运行时长",\n            "parent_ids": [0]\n        }\n    ],\n    "chain_of_subtasks": "（1）查询2024/6/12 处于停泊状态的数据条数（任务1）；（2）查询2024/6/12 一号柴油发电机在停泊状态下的运行时长（任务2）；（3）查询2024/6/12 二号柴油发电机在停泊状态下的运行时长（任务3）；（4）查询2024/6/12 三号柴油发电机在停泊状态下的运行时长（任务4）；（5）查询2024/6/12 四号柴油发电机在停泊状态下的运行时长（任务5）。"\n}\n```"""
#     res=parse_res("")
#     print(json.loads(res))
