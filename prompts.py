"""构造Prompt"""

import json
from solution import Subtask
import tools
import logger

table_meta_file = "prompts/table_meta.json"
prompt_knowledge_file = "prompts/knowledge.json"
prompt_task_decomposition_file = "prompts/task_decomposition.md"
prompt_atomic_question_file = "prompts/atomic_question.md"


def get_knowledge_by_question(question: str) -> list[str]:
    """
    根据问题获得背景知识

    :param question: 问题
    :return: 背景知识列表
    """
    with open(prompt_knowledge_file, "r", encoding="utf-8") as file:
        knowledge_list = json.load(file)
    knowledge_set = set()
    for item in knowledge_list:
        for key in item["keys"]:
            if key in question:
                knowledge_set.add(item["knowledge"])
    logger.info("【背景知识】", str(list(knowledge_set)))
    return list(knowledge_set)


def get_prompt_task_decomposition(question: str) -> str:
    """
    获得任务分解模板

    :param question: 问题
    :return: 任务分解模板
    """
    with open(prompt_task_decomposition_file, "r", encoding="utf-8") as file:
        task_decomposition = file.read()
    return f"""
    已知可调用的函数工具：{str(tools.tools_description)}
    已知信息:{str(get_knowledge_by_question(question))}
    {task_decomposition}
    """


def get_prompt_vote(question: str) -> str:
    """
    获得投票模板

    :param question: 问题
    :return: 投票模板
    """
    return f"""
    以下是针对问题<{question}>的多个回答结果，请评估并选择出现次数最多的答案：
    请返回投票过程、选择理由和最优答案的思考过程与最终答案：
    
    回答格式示例（严格遵循）：
    输入：2024/8/24 上午，折臂吊车的能耗占甲板机械设备的比例（以%输出，保留2位小数）？
    输出：以JSON格式输出，包含：
    - reasoning：思考过程及每一步的中间结果
    - correct：纠错步骤（如果有）
    - vote：投票过程、选择理由（如果有）
    - answer：以一句话给出最终答案
    {{
        "reasoning":"思考过程：\n1. 上午通常指 00:00 - 11:59；\n2. 2024/8/24 00:00 - 11:59 折臂吊车的总能耗为10.50kWh；\n3. 2024/8/24 00:00 - 11:59 甲板机械设备的总能耗为45.36kWh；\n3. 按照 (折臂吊车能耗 / 甲板机械设备能耗) * 100计算百分比，(10.50 / 45.36) * 100 = 23.148148%；\n4. 格式化输出，回答原数值、整数、保留1位小数、保留2位小数的带单位答案，并确保数值与单位 % 之间无空格；",
        "answer":"折臂吊车的能耗占甲板机械设备能耗的比例为23.148148%（整数：23%，1位小数：23.1%，2位小数：23.15%）"
    }}
    """


def get_prompt_atomic_question(
    task: Subtask, assumption: str, chain_of_subtasks: str, table_meta_list: list[dict]
) -> str:
    """
    获得原子问题模板

    :param task: 原子问题
    :param assumption: 假设条件
    :param table_meta_list: 数据表结构列表
    """
    question = task.question
    knowledge_list = get_knowledge_by_question(question)
    return f"""
    {f"当前需要解决的问题为：子任务{task.task_id} {question}"}
    {f"子任务链：{str(chain_of_subtasks)}" if len(chain_of_subtasks) > 0 else ""}
    {f"已知数据表结构：{str(table_meta_list)}" if len(table_meta_list) > 0 else ""}
    {f"已知知识：{str(knowledge_list)}" if len(knowledge_list) > 0 else ""}
    {f"假设条件：{str(assumption)}" if assumption else ""}
    
    已知上游任务执行结果：{str(task.get_parent_tasks_desc())}
    
    请回答问题：<{question}>，并严格遵守以下要求：
    - 求解当前子任务时充分利用子任务链中依赖的上游子任务的答案；
    - 返回的当前子任务答案需满足子任务链中下游任务的需求；
    - 不得杜撰时间、数据或关键动作，不得假设或猜测任何传入函数的参数值；
    - 回答中设备的关键动作不得拆开，用【】包裹，例如：【A架开机】；
    - 数值格式要求
        - 当存在字段的实际数值与表中数值不一致时，同时返回表中数值和实际数值，且均遵循格式要求；
        - 在有关时间的减法、除法等运算中，根据秒进行计算，然后再进行格式转换；
        - 不要进行任何格式转换（时间、数值、四舍五入），直接使用原始数据；
    - 涉及数学运算时，必须调用数学函数计算，不得手动计算；
    - 请先仔细思考，但仅需以一句话给出最终答案，不返回思考过程；
    
    回答格式示例
      - 2022/1/1 0:00 ~ 24:00时间段内，四台柴油发电机组的燃油消耗总量为300L。
      - 2024年8月19日下午A架的开机时间是13:34
    """


def get_prompt_summary_question(summary: dict) -> str:
    """
    获得问题总结模板

    :param summary: 问题总结
    :return: 问题总结模板
    """
    knowledge_list = get_knowledge_by_question(summary["question"])
    return f"""
    {f"已知知识：{str(knowledge_list)}" if len(knowledge_list) > 0 else ""}
    请根据问题解答过程<{summary}>，给出最终答案，并严格遵守以下要求：
    
    - 评估并修正：验证解答过程的正确性，如有错误，尝试修正；
    - 设备关键动作：不得拆开，需用【】包裹（示例：【A架开机】）
    - 数值与单位要求
        - 数值与单位间不得有空格（示例：300L）
        - 计算时间的减法/除法时，按秒计算后再格式化
        - 若实际数值与表中数值不符，同时返回二者，均需带单位
        - 转换为整数、小数、整数分钟时，默认为四舍五入，若未指定精度，保留2位小数
        - 回答数值问题时，同时提供原数值、整数、保留1位小数、保留2位小数的带单位答案
        - 严格遵守问题中的单位、时间格式、数值格式等要求，同时给出原始数值及格式化后的数值
        - 当题目要求回答时长且未指定单位时，需同时提供分钟和秒
    - 请先仔细思考，简要描述思考过程及每一步的中间结果后，以一句话给出最终答案
    - 根据题目要求，调整答案格式，确保答案与题目要求一致
    - 当题目为选择题时（如选择A、B、C），必须选择一项，且需同时回答选项及选项内容
    
    回答格式示例（严格遵循）：
    输入：2024/8/24 上午，折臂吊车的能耗占甲板机械设备的比例（以%输出，保留2位小数）？
    输出：以JSON格式输出，包含：
    - reasoning：思考过程及每一步的中间结果
    - correct：纠错步骤（如果有）
    - answer：以一句话给出最终答案
    {{
        "reasoning":"思考过程：\n1. 上午通常指 00:00 - 11:59；\n2. 2024/8/24 00:00 - 11:59 折臂吊车的总能耗为10.50kWh；\n3. 2024/8/24 00:00 - 11:59 甲板机械设备的总能耗为45.36kWh；\n3. 按照 (折臂吊车能耗 / 甲板机械设备能耗) * 100计算百分比，(10.50 / 45.36) * 100 = 23.148148%；\n4. 格式化输出，回答原数值、整数、保留1位小数、保留2位小数的带单位答案，并确保数值与单位 % 之间无空格；",
        "answer":"折臂吊车的能耗占甲板机械设备能耗的比例为23.148148%（整数：23%，1位小数：23.1%，2位小数：23.15%）"
    }}
    """


def get_prompt_get_table_meta_and_tool(task: Subtask, assumption: str) -> str:
    """
    生成数据表结构查询的 Prompt

    :param task: 问题
    :param assumption: 假设条件
    :return: Prompt
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        raw_table_data = json.load(file)

    table_data = [
        {"table_name": item["table_name"], "table_desc": item["table_desc"]}
        for item in raw_table_data
    ]

    return f"""
    已知可用的数据表：{str(table_data)}
    已知可调用的函数工具：{str(tools.tools_description)}
    {f"假设条件：{str(assumption)}" if assumption else ""}
    已知信息：{str(task.get_parent_tasks_desc())}
    
    请基于数据表、工具和已知条件回答以下问题：<{task.question}>：
    要求：
    - 分析解决该问题所必需的数据表和工具；  
    - 涉及计算的问题尽可能选择对应的工具 
    - 若已知条件或工具可独立解决问题，无需使用数据表；
    - 请先仔细思考，但仅需返回最终结果，不需要提供思考过程；
    - 输出格式：仅返回 JSON 格式的所需数据表名列表和工具列表，例如：
    {{
        "tables": ["table1", "table2"],
        "tools": ["tool1", "tool2"]
    }}
    """


def get_table_meta_by_table_names(table_names: list[str]) -> list[dict]:
    """
    根据数据表名获得数据表结构

    :param table_names: 数据表名列表
    :return: 数据表结构列表
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        table_data = json.load(file)
    table_meta_list = [item for item in table_data if item["table_name"] in table_names]
    return table_meta_list
