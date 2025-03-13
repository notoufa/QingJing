"""与GLM的API交互，获得问题答案"""

import json
import concurrent
from solution import (
    ProblemSolution,
    Decomposition,
    Subtask,
    VoteResult,
    ApiResponse,
    ReasoningAnswer,
)
import tools
import functions
import prompts
import logger
from utils import *
import utils


def vote(id: str, question: str, vote_times: int) -> VoteResult:
    """
    多次调用 get_answer 获取答案，并让 LLM 评估选出最优答案

    :param id: 问题 ID
    :param question: 问题
    :param vote_times: 采样次数
    :return: LLM 评估后选出的最佳答案
    """

    vote_res = VoteResult(id, question, vote_times)

    for i in range(vote_times):
        try:
            logger.info(f"【开始第{i+1}次获取问题答案】")
            solution = get_answer(id, question)
            vote_res.solutions.append(solution)
            logger.success(
                f"【第{i+1}次得到的最终答案】",
                str(solution.reasoning_answer),
            )
        except Exception as e:
            logger.error(
                f"【第{i+1}次获取问题的答案出错】错误堆栈：\n{traceback.format_exc()}"
            )

    if len(vote_res.solutions) == 1:
        vote_res.final_reasoning_answer = vote_res.solutions[0].reasoning_answer
        return vote_res

    logger.info(f"【开始投票】")

    answer_content = "\n".join(
        [f"答案 {i+1}: {result}" for i, result in enumerate(vote_res.get_answers())]
    )

    messages = [
        {"role": "system", "content": prompts.get_prompt_vote()},
        {"role": "user", "content": f"问题：{question}\n{answer_content}"},
    ]

    response = get_completion(messages)
    best_answer = json.loads(parse_res(response))
    vote_res.final_reasoning_answer = ReasoningAnswer.from_dict(best_answer)

    return vote_res


def get_answer(id: str, question: str, max_workers=1) -> ProblemSolution:
    """
    获得复杂问题的答案，返回最终答案

    :param id: 问题 ID
    :param question: 问题
    :param max_workers: 子任务线程数
    :return: 问题解答
    """
    solution = ProblemSolution(id, question)
    decomposition, api_response = get_task_decomposition(solution.question)
    solution.init_decomposition = decomposition.clone()
    solution.decomposition = decomposition
    solution.decomposition_api_response = api_response

    tasks_by_level, sorted_levels = group_tasks_by_level(decomposition.subtasks)
    current_index = 0

    while current_index < len(sorted_levels):
        current_level = sorted_levels[current_index]
        level_tasks = tasks_by_level[current_level]

        if len(level_tasks) > utils.module_config.max_workers_subtask * 1.5:
            max_workers = max(max_workers, utils.module_config.max_workers_subtask)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for task in level_tasks:
                if not task.completed():
                    futures.append(executor.submit(handle_task, task, decomposition, question))

            for future in concurrent.futures.as_completed(futures):
                future.result()

        if (
            utils.module_config.enable_update_decomposition
            and current_level != sorted_levels[-1]
        ):
            decomposition = update_decomposition(question, decomposition)
            solution.decomposition = decomposition
            tasks_by_level, sorted_levels = group_tasks_by_level(decomposition.subtasks)
            if current_level == sorted_levels[-1]:
                break

        current_index += 1

    solution.reasoning_answer = ReasoningAnswer(
        solution.decomposition.subtasks[-1].answer
    )
    if utils.module_config.enable_summary:
        reasoning_answer, api_response = get_summary(solution)
        solution.reasoning_answer = reasoning_answer
        solution.summary_api_response = api_response
    if utils.module_config.enable_correct:
        reasoning_answer, api_response = get_correct(solution)
        solution.reasoning_answer = reasoning_answer
        solution.correct_api_response = api_response
    return solution


def group_tasks_by_level(subtasks):
    """
    将子任务按级别分组，并返回按级别排序的任务字典。

    :param subtasks: 子任务列表，包含多个任务对象，每个任务对象需要有 `level` 属性。
    :return: 一个字典，按任务级别分组，并且级别已排序。
    """
    tasks_by_level = {}

    for task in subtasks:
        if task.level not in tasks_by_level:
            tasks_by_level[task.level] = []
        tasks_by_level[task.level].append(task)

    sorted_levels = sorted(tasks_by_level.keys())
    return tasks_by_level, sorted_levels


def handle_task(task: Subtask, decomposition: Decomposition, init_question: str):
    """
    在单独的线程中处理每个子任务

    :param task: 子任务
    :param decomposition: 分解结果
    """
    parent_tasks = []
    for parent_id in task.parent_ids:
        parent_task = decomposition.get_task_by_id(parent_id)
        if parent_task:
            parent_tasks.append(parent_task)
    task.parent_tasks = parent_tasks
    get_atomic_answer(decomposition, task, init_question)


def get_summary(solution: ProblemSolution) -> tuple[ReasoningAnswer, ApiResponse]:
    """
    获得问题总结的答案

    :param solution: 问题解答
    :return: 问题总结的答案
    """
    logger.info("【问题总结】", solution.to_summary_json())
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_summary(solution.question),
        },
        {
            "role": "user",
            "content": str(solution.to_summary_json()),
        },
    ]
    response = get_completion(messages)
    try:
        res = json.loads(parse_res(response))
        res_answer = ReasoningAnswer.from_dict(res)
        logger.special(f"【问题总结结果】: \n{res_answer}")
        return (
            res_answer,
            ApiResponse(messages, response),
        )
    except Exception as e:
        logger.error(f"【问题总结出错】错误堆栈：\n{traceback.format_exc()}")


def get_correct(solution: ProblemSolution) -> tuple[ReasoningAnswer, ApiResponse]:
    """
    获得问题纠错的答案

    :param solution: 问题解答
    :return: 问题纠错的答案
    """
    logger.info("【问题纠错】", solution.to_correct_json())
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_correct(solution.question),
        },
        {
            "role": "user",
            "content": str(solution.to_correct_json()),
        },
    ]
    res_answer = solution.reasoning_answer.clone()
    response = get_completion(messages)
    try:
        res = json.loads(parse_res(response))
        res_answer.corrected_reasoning = res["corrected_reasoning"]
        res_answer.corrected_answer = res["corrected_answer"]
        res_answer.correct = res["correct"]
        return (
            res_answer,
            ApiResponse(messages, response),
        )
    except Exception as e:
        logger.error(f"【问题纠错出错】错误堆栈：\n{traceback.format_exc()}")


def get_task_decomposition(question: str) -> tuple[Decomposition, ApiResponse]:
    """
    获得问题的分解结果

    :param question: 问题
    :return: 问题的分解结果
    """
    logger.info("【开始获取问题分解结果】", question)
    tool_names = get_tool(question)
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_task_decomposition(question, tool_names),
        },
        {
            "role": "user",
            "content": question,
        },
    ]
    response = get_completion(messages)
    res = json.loads(parse_res(response))
    decomposition = Decomposition.from_dict(res)
    decomposition.need_tools = tool_names
    decomposition.draw_table()
    return decomposition, ApiResponse(messages, response)


def update_decomposition(question: str, decomposition: Decomposition) -> Decomposition:
    """
    询问 LLM 是否需要更新任务分解树

    :param decomposition: 问题的分解结果
    :return: 更新后的decomposition
    """
    logger.debug("【开始更新任务分解树】")
    user_prompt = "已知初始任务问题为：<<question>> \n 当前任务分解树如下:<<decomposition>>\n 是否需要更新任务分解树？"
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_update_decomposition(question),
        },
        {
            "role": "user",
            "content": user_prompt.replace("<<question>>", str(question)).replace(
                "<<decomposition>>", str(decomposition.to_update_dict())
            ),
        },
    ]
    response = get_completion(messages)

    try:
        res = json.loads(parse_res(response))
    except Exception as e:
        logger.error(f"【更新任务分解树出错】错误堆栈：\n{traceback.format_exc()}")
        logger.error(f"{parse_res(response)}")
        return decomposition

    res_decomposition = Decomposition.from_dict(res)
    for subtask in res_decomposition.subtasks:
        init_task = decomposition.get_task_by_id(subtask.task_id)
        if init_task and init_task.completed():
            subtask.answer = init_task.answer
            subtask.need_tools = init_task.need_tools
            subtask.need_tables = init_task.need_tables
            subtask.function_results = init_task.function_results
            subtask.parent_tasks = init_task.parent_tasks
            subtask.api_response = init_task.api_response
    res_decomposition.need_tools = decomposition.need_tools
    res_decomposition.draw_table()
    return res_decomposition


def get_atomic_answer(decomposition: Decomposition, task: Subtask, init_question: str):
    """
    获得原子问题的答案

    :param decomposition: 问题的分解结果
    :param task: 原子问题
    :param parent_tasks: 父任务
    """
    logger.info("【开始获取原子问题答案】", task.question)
    if utils.module_config.enable_rewrite_atomic_question and task.has_parent_task():
        rewrite_atomic_question(decomposition, task, init_question)
        
    # 重写问题后再获取所需要的base table和tools
    table_meta_list, tool_list = get_table_meta_and_tool(decomposition, task)
    system_prompt, user_prompt = prompts.get_prompt_atomic_question(
        task,
        decomposition.assumption,
        decomposition.chain_of_subtasks,
        table_meta_list,
    )
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
    response = get_completion(messages, tool_list)
    messages.append(response.choices[0].message.model_dump())
    function_results = []
    for _ in range(utils.module_config.max_function_calling_iterations):
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                if function_name in functions.function_map.keys():
                    logger.debug("【开始执行工具函数】", function_name, ", 参数:", args)
                    function_result = functions.function_map[function_name](**args)
                    function_results.append(function_result)
                    logger.info("【工具函数执行结果】", function_result)
                    messages.append(
                        {
                            "role": "tool",
                            "content": f"{function_result}",
                            "tool_call_id": tool_call.id,
                        }
                    )
                else:
                    logger.error("【未找到工具函数】", function_name)
            response = get_completion(messages, tool_list)
            messages.append(response.choices[0].message.model_dump())
        else:
            break
    api_response = ApiResponse(messages, response)
    answer = parse_res(response)
    logger.success("【原子问题答案】", answer)
    task.answer = answer
    task.function_results = function_results
    task.api_response = api_response
    task.need_tools = [item["function"]["name"] for item in tool_list]
    task.need_tables = [table["table_name"] for table in table_meta_list]


def rewrite_atomic_question(decomposition: Decomposition, task: Subtask, init_question: str):
    """
    重写原子问题

    :param decomposition: 问题的分解结果
    :param task: 原子问题
    """
    logger.debug("【开始重写原子问题】", task.question)
    system_prompt, user_prompt = prompts.get_prompt_rewrite_atomic_question(
        task,
        decomposition.assumption,
        decomposition.chain_of_subtasks,
        init_question,
    )
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
    response = get_completion(messages)
    try:
        pre_task = json.loads(parse_res(response))
        logger.special(
            "【重写原子问题】",
            f"原问题：{task.question}----->重写后的问题：{pre_task['response']}",
        )
        task.question = pre_task["response"]
    except Exception as e:
        logger.error(f"【原子问题预处理出错】错误堆栈：\n{traceback.format_exc()}")


def get_tool(question: str) -> list:
    """
    获得问题所需的工具

    :param question: 问题
    :return: 所需工具的名称列表
    """
    logger.debug("【开始获取初始问题所需工具】", question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_get_tool(question),
        },
    ]
    response = get_completion(messages)
    tool_names = json.loads(parse_res(response))
    logger.info("【问题所需工具】", tool_names)
    return tool_names


def get_table_meta_and_tool(
    decomposition: Decomposition, task: Subtask
) -> tuple[list, list]:
    """
    获得问题所需的数据表的元信息和所需工具

    :param decomposition: 问题的分解结果
    :param task: 原子问题
    :return: 数据表的元信息和所需工具
    """
    logger.debug("【开始获取原子问题所需数据表和工具】", task.question)
    messages = [
        {
            "role": "user",
            "content": prompts.get_prompt_get_table_meta_and_tool(
                task, decomposition.assumption
            ),
        },
    ]
    response = get_completion(messages)
    res = json.loads(parse_res(response))
    tables = res.get("tables", [])
    need_tools = res.get("tools", [])
    if not decomposition.contains_time and "设备参数详情" not in tables:
        tables.append("设备参数详情")
    logger.info("【原子问题所需数据表】", tables, "【所需工具】", need_tools)
    table_meta_list = prompts.get_table_meta_by_table_names(tables)
    tool_list = []
    for tool in tools.tools:
        if tool["function"]["name"] in need_tools:
            tool_list.append(tool)
    return table_meta_list, tool_list
