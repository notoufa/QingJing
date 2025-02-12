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

def get_prompt_atomic_question():
    """
    获得原子问题模板
    """
    with open(prompt_atomic_question_file, "r", encoding="utf-8") as file:
        atomic_question = file.read()
    return atomic_question
