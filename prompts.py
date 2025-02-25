"""构造Prompt"""

import json
from solution import Decomposition, Subtask
import tools
import logger

table_meta_file = "knowledge/table_meta.json"
knowledge_file = "knowledge/knowledge.json"
atomic_questions_file = "knowledge/atomic_questions.json"

prompt_task_decomposition_file = "prompts/task_decomposition.md"
prompt_update_decomposition_file = "prompts/update_decomposition.md"
prompt_vote_file = "prompts/vote.md"
prompt_atomic_question_file = "prompts/atomic_question.md"
prompt_summary_file = "prompts/summary.md"
prompt_get_table_meta_and_tool_file = "prompts/get_table_meta_and_tool.md"
prompt_get_tool_file = "prompts/get_tool.md"


def get_knowledge_by_question(question: str) -> list[str]:
    """
    根据问题获得背景知识

    :param question: 问题
    :return: 背景知识列表
    """
    with open(knowledge_file, "r", encoding="utf-8") as file:
        knowledge_list = json.load(file)
    knowledge_set = set()
    for item in knowledge_list:
        for key in item["keys"]:
            if key in question:
                knowledge = item["knowledge"]
                if item.get("example"):
                    knowledge += f"（示例：{item['example']}）"
                knowledge_set.add(knowledge)
    logger.info("【背景知识】", str(list(knowledge_set)))
    return list(knowledge_set)


def get_atomic_questions():
    """
    加载所有原子问题
    """
    atomic_questions = []
    with open(atomic_questions_file, "r", encoding="utf-8") as file:
        atomic_questions = json.loads(file.read())
    return atomic_questions


def get_prompt_task_decomposition(question: str, tool_names: list[str]) -> str:
    """
    获得任务分解模板

    :param question: 问题
    :return: 任务分解模板
    """
    with open(prompt_task_decomposition_file, "r", encoding="utf-8") as file:
        res = file.read()
    atomic_questions = get_atomic_questions()
    res = res.replace("<<atomic_questions>>", str(atomic_questions))
    res = res.replace(
        "<<function_calls>>", tools.tools_description_str_by_names(tool_names)
    )
    res = res.replace("<<knowledge>>", str(get_knowledge_by_question(question)))
    return res


def get_prompt_update_decomposition(question: str) -> str:
    """
    获得任务分解更新模板

    :param question: 问题
    :return: 任务分解模板
    """
    with open(prompt_task_decomposition_file, "r", encoding="utf-8") as file:
        res = file.read()
    res = res.replace("<<knowledge>>", str(get_knowledge_by_question(question)))
    return res


def get_prompt_vote(question: str) -> str:
    """
    获得投票模板

    :param question: 问题
    :return: 投票模板
    """
    with open(prompt_vote_file, "r", encoding="utf-8") as file:
        res = file.read()
    res = res.replace("<<question>>", question)
    return res


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
    with open(prompt_atomic_question_file, "r", encoding="utf-8") as file:
        res = file.read()
    res = res.replace("<<knowledge>>", str(get_knowledge_by_question(question)))
    if str(chain_of_subtasks) != "None":
        res = res.replace("<<chain_of_subtasks>>", str(chain_of_subtasks))
    res = res.replace("<<table_meta_list>>", str(table_meta_list))
    res = res.replace("<<assumption>>", assumption)
    res = res.replace("<<question>>", f"【子任务{task.task_id}】{question}")
    res = res.replace("<<parent_tasks_desc>>", str(task.get_parent_tasks_desc()))
    return res


def get_prompt_summary(summary: dict) -> str:
    """
    获得问题总结模板

    :param summary: 问题总结
    :return: 问题总结模板
    """
    with open(prompt_summary_file, "r", encoding="utf-8") as file:
        res = file.read()
    res = res.replace(
        "<<knowledge>>", str(get_knowledge_by_question(summary["question"]))
    )
    res = res.replace("<<summary>>", str(summary))
    return res


def get_prompt_get_tool(question: str) -> str:
    """
    生成可能所需的工具的 Prompt

    :param question: 问题
    :return: Prompt
    """
    with open(prompt_get_tool_file, "r", encoding="utf-8") as file:
        res = file.read()
    res = res.replace("<<knowledge>>", str(get_knowledge_by_question(question)))
    res = res.replace("<<tools>>", str(str(tools.tools_description_str())))
    res = res.replace("<<question>>", f"{question}")
    return res


def get_prompt_get_table_meta_and_tool(task: Subtask, assumption: str) -> str:
    """
    生成数据表结构查询的 Prompt

    :param task: 问题
    :param assumption: 假设条件
    :return: Prompt
    """
    with open(prompt_get_table_meta_and_tool_file, "r", encoding="utf-8") as file:
        res = file.read()
    question = task.question
    res = res.replace("<<knowledge>>", str(get_knowledge_by_question(question)))
    res = res.replace("<<tools>>", tools.tools_description_str())
    res = res.replace("<<table_desc>>", get_table_desc_str())
    res = res.replace("<<assumption>>", assumption)
    res = res.replace("<<question>>", f"【子任务{task.task_id}】{question}")
    res = res.replace("<<parent_tasks_desc>>", str(task.get_parent_tasks_desc()))
    return res


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


def get_table_desc_str() -> str:
    """
    获得数据表描述字符串

    :return: 数据表描述字符串
    """
    with open(table_meta_file, "r", encoding="utf-8") as file:
        raw_table_data = json.load(file)

    table_data = [
        {"表名": item["table_name"], "表的描述信息": item["table_desc"]}
        for item in raw_table_data
    ]
    table_data_str = "\n".join(
        [
            f"{idx + 1}. 表名: {item['表名']}, 表的描述信息: {item['表的描述信息']}"
            for idx, item in enumerate(table_data)
        ]
    )
    return table_data_str
