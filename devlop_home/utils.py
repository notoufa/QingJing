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

        if response.choices[0].finish_reason == "length":
            logger.warning("【回答长度过长】")
        logger.trace("【回答结果】", str(response))
        return response
    except Exception as e:
        logger.error(f"【请求回答出错】: {e}")
        logger.error(traceback.format_exc())
        raise e


def txt_to_pdf(input_file, input_data, output_file=None, font_size=12):
    try:
        from fpdf import FPDF

        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.pdf"
        output_path = os.path.join(os.getcwd(), output_file)

        line_height = font_size * 0.4
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("Microsoft Yahei", "", font_file, uni=True)
        pdf.set_font("Microsoft Yahei", size=font_size)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(left=15, top=15, right=15)

        if os.path.exists(input_file):
            with open(input_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().replace("\r", "").replace("\n", "")
                    if line:
                        pdf.multi_cell(pdf.epw, line_height, txt=line, ln=1)
        elif input_data:
            pdf.multi_cell(pdf.epw, line_height, txt=str(input_data), ln=1)
        else:
            return None
        pdf.output(output_path)
        return output_path
    except Exception:
        return None


def txt_to_doc(input_file, input_data, output_file=None, font_size=12):
    try:
        from docx import Document
        from docx.shared import Pt

        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}.docx"
        output_path = os.path.join(os.getcwd(), output_file)

        doc = Document()

        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(font_size)

        if os.path.exists(input_file):
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                doc.add_paragraph(content)
        elif input_data:
            print(input_data)
            doc.add_paragraph(str(input_data))
        else:
            return None

        doc.save(output_path)
        doc = None
        return output_path
    except Exception:
        return None


def check_knowledge(path, data=None):
    if api_config.type.upper() == "ZHIPUAI":
        try:
            target_path = txt_to_doc(path, data)
            if target_path:
                client = ZhipuAI(api_key=check_api_key(api_config.api_key_env))
                client.files.create(
                    file=open(target_path, "rb"),
                    purpose="retrieval",
                    knowledge_id=module_config.knowledge_id,
                )
                if os.path.exists(target_path):
                    time.sleep(1)
                    os.remove(target_path)
        except Exception:
            pass
