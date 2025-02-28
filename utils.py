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
        return res
    except Exception as e:
        logger.trace(f"【解析结果出错】: {e}", traceback.format_exc())
        return res


def custom_serializer(obj):
    if isinstance(obj, np.int64):
        return int(obj)
    raise TypeError(f"Type {obj.__class__.__name__} not serializable")


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


def check_api_key() -> str:
    """
    检查API_KEY是否设定
    """
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ZHIPUAI_API_KEY is not set. Please set the environment variable."
        )
    return api_key


def get_completion(
    messages: list[dict],
    tools: list[dict] = [],
    model: str = "glm-4-plus",
    temperature: float = 0,
    json_output: bool = False,
) -> Completion | StreamResponse[ChatCompletionChunk]:
    """
    获得对话结果

    :param messages: 对话消息
    :param tools: 工具
    :param model: 模型
    :return: 对话结果
    """
    try:
        client = ZhipuAI(api_key=check_api_key())
        logger.trace("【请求回答】", str(messages), "【工具】", str(tools))
        if json_output:
            response_format = {"type": "json_object"}
        else:
            response_format = {"type": "text"}
        response = client.chat.completions.create(
            model=model,
            stream=False,
            messages=messages,
            tools=tools,
            response_format=response_format,
            temperature=temperature,
        )
        if response.choices[0].finish_reason == "length":
            logger.error("【回答长度过长】")
        logger.trace("【回答结果】", str(response))
        return response
    except Exception as e:
        logger.error(f"【请求回答出错】: {e}")
        logger.error(traceback.format_exc())
        raise e


