"""构造Prompt"""

prompt_background_knowledge_file = "prompts/background_knowledge.md"
prompt_task_decomposition_file = "prompts/task_decomposition.md"
prompt_atomic_question_file = "prompts/atomic_question.md"


def get_prompt_background_knowledge():
    """
    获得背景知识模板
    """
    with open(prompt_background_knowledge_file, "r", encoding="utf-8") as file:
        background_knowledge = file.read()
    return background_knowledge


def get_prompt_task_decomposition():
    """
    获得任务分解模板
    """
    with open(prompt_task_decomposition_file, "r", encoding="utf-8") as file:
        task_decomposition = file.read()
    return task_decomposition


def get_prompt_atomic_question(question, table_meta_list, parent_answers):
    """
    获得原子问题模板
    """
    table_meta_list_content = (
        f"已知数据表结构：{str(table_meta_list)}" if len(table_meta_list) > 0 else ""
    )
    parent_answers_content = (
        f"已知：{str(parent_answers)}" if len(parent_answers) > 0 else ""
    )
    question_content = f"""请回答以下问题：{question}
    你自己仔细思考判断，思考完成后，不需要返回思考过程，只需以一句话给出问题的答案，示例："2022/1/1 0:00 ~ 24:00时间段内，四台柴油发电机组的燃油消耗总量为300升。"
    """
    content = ""
    if table_meta_list_content:
        content += table_meta_list_content
        content += "\n"
    if parent_answers_content:
        content += parent_answers_content
        content += "\n"
    content += question_content
    return content


def get_prompt_table_meta(table_data, question):
    """
    获得数据表结构模板
    """
    return f"""我有如下数据表：<{str(table_data)}>，
    现在基于数据表回答问题：{question}，请分析需要哪些数据表
    你自己仔细思考判断，思考完成后，不需要返回思考过程，仅返回需要的数据表名列表，示例：["Ajia_plc_1"]
    """
