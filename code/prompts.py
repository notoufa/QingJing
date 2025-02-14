"""构造Prompt"""

import json
import tools
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
    - 不要杜撰时间、数据、关键动作等内容，不要假设或猜测传入函数的参数值；
    - 答案中设备的关键动作用【】包裹，如【A架开机】；
    - 涉及到数学运算时，请调用数学函数计算，不要手动计算；
    - 如果问题中包含单位、时间格式、数值格式等要求，请严格遵守要求回答问题，并需同时给出原数值与处理格式后的数值；
    - 答案中的数值与对应单位之间不要有空格，如：300L；
    - 如果答案未说明小数点位数，默认保留小数点两位；
    - 你自己仔细思考判断，思考完成后，不需要返回思考过程，只需以一句话给出问题的答案；
    - 回答示例
        - 2022/1/1 0:00 ~ 24:00时间段内，四台柴油发电机组的燃油消耗总量为300L。
        - 2024年8月19日下午A架的第一次开机时间是13:34
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


def get_prompt_summary_question(message):
    """
    获得问题总结模板
    """
    return f"""请根据问题解答过程{message}，给出最终答案，要求如下：
    - 评估验证解答过程的正确性，如果不正确，尝试修正答案；
    - 答案中设备的关键动作用【】包裹，如【A架开机】；
    - 涉及到数学运算时，请调用数学函数计算，不要手动计算；
    - 如果问题中包含单位、时间格式、数值格式等要求，请严格遵守要求回答问题，并需同时给出原数值与处理格式后的数值；
    - 答案中的数值与对应单位之间不要有空格，如：300L；
    - 如果答案未说明小数点位数，默认保留小数点两位；
    - 你自己仔细思考判断，思考完成后，返回简略的思考过程，并以一句话给出问题的答案；
    示例：
    问题：2024/8/24 上午，折臂吊车的能耗占甲板机械设备的比例（以%输出，保留2位小数）？
    思考过程：
    1. 上午通常指 00:00 - 11:59；
    2. 获取折臂吊车的能耗数据，得到2024/8/24 00:00 - 11:59 折臂吊车的总能耗为10.50kWh。
    3. 获取甲板机械设备的能耗数据；得到'2024/8/24 00:00 - 11:59 甲板机械设备的总能耗为45.36kWh。
    3. 计算折臂吊车能耗占甲板机械设备能耗的比例，按照 `(折臂吊车能耗 / 甲板机械设备能耗) * 100` 计算百分比，并保留两位小数。  
    4. 输出格式符合要求，即数值与 `%` 之间无空格，保留两位小数。
    问题答案：
    折臂吊车的能耗占甲板机械设备能耗的比例为23.15%。
    """

def get_prompt_get_table_meta_and_tool(question):
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
    return f"""我有如下数据表：<{str(table_data)}>，以下函数工具：<{str(tools.tools)}>
    现在基于数据表和函数调用回答问题：{question}，请分析需要哪些数据表和工具（当工具能够解决问题时，无需使用数据表）
    你自己仔细思考判断，思考完成后，不需要返回思考过程，仅返回需要的数据表名列表和工具列表，示例：
    {{\"tables\": [\"table1\", \"table2\"], \"tools\": [\"tool1\", \"tool2\"]}}
    """


def get_table_meta_by_table_names(table_names):
    """
    根据数据表名获得数据表结构
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        table_data = json.load(file)
    table_meta_list = [item for item in table_data if item["table_name"] in table_names]
    return table_meta_list
