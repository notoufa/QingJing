"""工具函数"""

import json
import numpy as np
import logger
import traceback
import os
from solution import ApiConfig, ModuleConfig

config_file = "devlop_home/config.json"
font_file = "devlop_home/msyh.ttf"

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


def check_base_url(base_url_env: str = "BASE_HOST") -> str:
    """
    检查BASE_HOST是否设定
    """
    base_url = os.getenv(base_url_env)
    if not base_url:
        logger.warning(
            f"{base_url_env} is not set. Please set the environment variable."
        )
    return base_url


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
            logger.error(
                f"第 {attempts} 次执行 {func.__name__} 出错，错误堆栈：\n{traceback.format_exc()}"
            )
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


def get_completion(messages: list[dict], tools: list[dict] = []):
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
            from zhipuai import ZhipuAI

            client = ZhipuAI(
                base_url=check_base_url(),
                api_key=check_api_key(api_config.api_key_env),
            )

        logger.trace("【请求回答】", str(messages), "【工具】", str(tools))

        response = client.chat.completions.create(
            model=model,
            stream=stream,
            messages=messages,
            tools=tools,
            temperature=temperature,
        )

        logger.trace("【回答结果】", str(response))

        if response.choices[0].finish_reason == "length":
            logger.warning("【回答长度过长】")

        return response
    except Exception as e:
        logger.error(f"【请求回答出错】: {e}\n{traceback.format_exc()}")
        raise e
