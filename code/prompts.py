"""构造Prompt"""

import json
import logger

table_meta_file = "prompts/table_meta.json"
prompt_knowledge_file = "prompts/knowledge.json"
prompt_task_decomposition_file = "prompts/task_decomposition.md"
prompt_atomic_question_file = "prompts/atomic_question.md"


def get_knowledge_by_question(question):
    """
    根据问题获得背景知识
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


def get_prompt_task_decomposition(question):
    """
    获得任务分解模板
    """
    with open(prompt_task_decomposition_file, "r", encoding="utf-8") as file:
        task_decomposition = file.read()
    return f"已知:{str(get_knowledge_by_question(question))}\n{task_decomposition}"


def get_prompt_atomic_question(
    question, table_meta_list, parent_answers, assumption=None
):
    """
    获得原子问题模板
    """
    table_meta_list_content = (
        f"已知数据表结构：{str(table_meta_list)}" if len(table_meta_list) > 0 else ""
    )
    parent_answers.append(get_knowledge_by_question(question))
    parent_answers_content = (
        f"已知：{str(parent_answers)}" if len(parent_answers) > 0 else ""
    )
    assumption_content = f"假设：{str(assumption)}" if assumption else ""
    question_content = f"""请回答问题：{question}，要求如下：
    - 不要杜撰数据、关键动作等内容，不要假设或猜测传入函数的参数值；
    - 如果用户的描述不明确，请要求用户提供必要信息；
    - 涉及到数学运算时，请调用数学函数计算，不要手动计算；
    - 如果问题中包含单位、时间格式、数值格式等要求，请严格遵守要求回答问题；
    - 你自己仔细思考判断，思考完成后，不需要返回思考过程，只需以一句话给出问题的答案；
    - 回答示例："2022/1/1 0:00 ~ 24:00时间段内，四台柴油发电机组的燃油消耗总量为300L"。
    """
    content = ""
    if table_meta_list_content:
        content += table_meta_list_content
        content += "\n"
    if parent_answers_content:
        content += parent_answers_content
        content += "\n"
    if assumption_content:
        content += assumption_content
        content += "\n"
    content += question_content
    return content


def get_prompt_get_table_meta(question):
    """
    获得数据表结构模板
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        raw_table_data = json.load(file)
    table_data = [
        {
            "table_name": item["table_name"],
            "table_desc": item["table_desc"],
        }
        for item in raw_table_data
    ]
    return f"""我有如下数据表：<{str(table_data)}>，
    现在基于数据表回答问题：{question}，请分析需要哪些数据表
    你自己仔细思考判断，思考完成后，不需要返回思考过程，仅返回需要的数据表名列表，示例：["Ajia_plc_1"]
    """


def get_table_meta_by_table_names(table_names):
    """
    根据数据表名获得数据表结构
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        table_data = json.load(file)
    table_meta_list = [item for item in table_data if item["table_name"] in table_names]
    return table_meta_list
