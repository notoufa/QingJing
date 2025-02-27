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
                f"【第{i+1}次得到的最终答案】: \n{str(solution.reasoning_answer)}"
            )
        except Exception as e:
            logger.error(f"【第{i+1}次获取问题的答案出错】: {e}")
            logger.error(traceback.format_exc())

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

    tasks_by_level = {}
    for task in decomposition.subtasks:
        if task.level not in tasks_by_level:
            tasks_by_level[task.level] = []
        tasks_by_level[task.level].append(task)

    sorted_levels = sorted(tasks_by_level.keys())
    last_level = sorted_levels[len(sorted_levels) - 1]

    for level in sorted(tasks_by_level.keys()):
        level_tasks = tasks_by_level[level]

        if len(level_tasks) > 5:
            max_workers = max(max_workers, 5)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for task in level_tasks:
                if not task.completed():
                    futures.append(executor.submit(handle_task, task, decomposition))

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # if level != last_level:
        #     update_decomposition(question, decomposition)

    reasoning_answer, api_response = get_summary(solution)
    solution.reasoning_answer = reasoning_answer
    solution.summary_api_response = api_response
    reasoning_answer, api_response = correct(solution)
    solution.reasoning_answer = reasoning_answer
    solution.correct_api_response = api_response
    return solution


def handle_task(task: Subtask, decomposition: Decomposition):
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
    get_atomic_answer(decomposition, task)


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
        logger.error(f"【问题总结出错】: {e}")
        logger.error(traceback.format_exc())


def correct(solution: ProblemSolution) -> tuple[ReasoningAnswer, ApiResponse]:
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
        logger.error(f"【问题纠错出错】: {e}\n{traceback.format_exc()}")


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
    :return: 是否需要更新任务分解树
    """
    logger.debug("【询问是否需要更新任务分解树】")
    messages = [
        {
            "role": "system",
            "content": prompts.get_prompt_update_decomposition(question),
        },
        {
            "role": "user",
            "content": str(decomposition.to_update_dict()),
        },
    ]
    response = get_completion(messages)
    res = json.loads(parse_res(response))
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
    decomposition = res_decomposition
    decomposition.draw_table()


def get_atomic_answer(decomposition: Decomposition, task: Subtask):
    """
    获得原子问题的答案

    :param decomposition: 问题的分解结果
    :param task: 原子问题
    :param parent_tasks: 父任务
    """
    table_meta_list, tool_list = get_table_meta_and_tool(decomposition, task)
    logger.info("【开始获取原子问题答案】", task.question)
    if task.has_parent_task():
        system_prompt, user_prompt = prompts.get_prompt_pre_atomic_question(
            task,
            decomposition.assumption,
            decomposition.chain_of_subtasks,
        )
        pre_messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]
        pre_response = get_completion(pre_messages)

        try:
            content = pre_response.choices[0].message.content
            cleaned_content = (
                content.strip()
                .replace("json\n", "")
                .replace("\n", "")
                .replace("```", "")
            )
            pre_task = json.loads(cleaned_content)
            logger.special("【原子问题预处理】", pre_task)
            is_answer = pre_task["can_answer_directly"]
            if is_answer:
                logger.special("【原子问题答案】", pre_task["response"])
                task.answer = pre_task["response"]
                task.api_response = ApiResponse(pre_messages, pre_response)
                return
            else:
                logger.special(
                    "【重写原子问题】",
                    f"原问题：{task.question}----->重写后的问题：{pre_task['response']}",
                )
                task.question = pre_task["response"]
        except Exception as e:
            logger.error(f"【原子问题预处理出错】: {e}")
            logger.error(traceback.format_exc())

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
    # 循环调用函数
    function_results = []
    max_iterations = 6
    for _ in range(max_iterations):
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
    if not decomposition.contains_time and "设备参数详情表" not in tables:
        tables.append("设备参数详情表")
    logger.info("【原子问题所需数据表】", tables, "【所需工具】", need_tools)
    table_meta_list = prompts.get_table_meta_by_table_names(tables)
    tool_list = []
    for tool in tools.tools:
        if tool["function"]["name"] in need_tools:
            tool_list.append(tool)
    return table_meta_list, tool_list
