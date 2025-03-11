import json
import concurrent.futures as cf
import os
import traceback
import api
import time
import argparse
from solution import VoteResult
import logger
import utils
import tools

solution_dir = "devlop_home/solutions"


def handle_question(query):
    """
    预处理问题
    """
    replace_dict = {
        "下放阶段以ON DP和OFF DP为标志，回收阶段以A架开机和关机为标志": "",
        "平均作业时长": "平均每天作业时长",
        "开机时长": "运行时长",
        "开机总时长": "运行总时长",
        "从征服者出水（约-43°）到落座（约35°）A架右舷摆过的角度可以记为一次完整的摆动（反之亦然），": "",
        "假设A架右舷同一方向上摆动超过10°即可算作一次摆动，": "同方向摆动，",
    }
    for key, value in replace_dict.items():
        query = query.replace(key, value)
    return query


def process_one(line: dict) -> VoteResult | dict:
    """
    获取一个问题的解决过程及答案
    """
    id = line["id"]
    question = handle_question(line["question"])
    try:
        logger.info(f"【开始获取问题{id}的答案】", question)
        vote_res = api.vote(id, question, utils.module_config.vote_times).clone()
        logger.special(
            f"【{id}的最终答案】:\n",
            vote_res.final_reasoning_answer.get_correct_answer(),
        )
        return vote_res
    except Exception as e:
        logger.error(f"【获取问题{id}的答案出错】错误堆栈：\n{traceback.format_exc()}")
        return {"id": id, "question": question, "answer": str(e)}


def init():
    """
    初始化
    """
    tools.load_tools()
    utils.load_api_config()
    utils.load_module_config()
    os.makedirs(submit_dir, exist_ok=True)
    os.makedirs(solution_dir, exist_ok=True)


def main():
    init()
    in_param_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(in_param_path, "r", encoding="utf-8") as load_f:
        content = load_f.read()
        input_params = json.loads(content)

    question_path = input_params["fileData"]["questionFilePath"]

    with open(question_path, "r", encoding="utf-8") as f:
        question_list = [json.loads(line.strip()) for line in f]
    if splice_index:
        question_list = question_list[:1]

    logger.debug(
        f"【运行模式】: {'测试' if is_test else '生产'},",
        f"【API 配置】: {utils.api_config.config_name},",
        f"【问题总数】: {len(question_list)},",
        f"【投票次数】: {utils.module_config.vote_times},",
        f"【问题并发线程数】: {max_workers_main},",
        f"【子任务并发线程数】: {max_workers_subtask},",
        f"【仅处理第一个问题】: {splice_index},",
        f"【问题文件】: {question_path}",
    )

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    submit_path = os.path.join(submit_dir, f"试试又不会怎样_result_{date_str}.jsonl")
    solution_path = os.path.join(solution_dir, f"solution_{date_str}.json")

    vote_results = []
    submit_result_list = []

    with cf.ThreadPoolExecutor(max_workers=max_workers_main) as executor:
        future_list = [executor.submit(process_one, item) for item in question_list]
        for future in cf.as_completed(future_list):
            vote_res = future.result()
            if isinstance(vote_res, VoteResult):
                vote_results.append(vote_res)
                submit_result_list.append(
                    vote_res.to_submit_json()
                    if isinstance(vote_res, VoteResult)
                    else vote_res
                )
                utils.save_submit_result(submit_result_list, submit_path)
                utils.save_solutions(vote_results, solution_path)
            else:
                submit_result_list.append(vote_res)
                utils.save_submit_result(submit_result_list, submit_path)


if __name__ == "__main__":
    logger.init()
    start_time = time.time()
    logger.info(
        "------------------------------【程序开始】------------------------------"
    )
    main()
    end_time = time.time()
    elapsed_time_minutes = (end_time - start_time) / 60
    logger.debug(f"【程序运行时间】 {elapsed_time_minutes:.2f} 分钟")
    logger.info(
        "------------------------------【程序结束】------------------------------"
    )
