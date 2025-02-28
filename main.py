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
from tools import load_tools

submit_dir = "results"
solution_dir = "solutions"
export_api_response = False

test_input_path = "questions/test.jsonl"
production_input_path = "questions/question_new.jsonl"


def parse_args():
    parser = argparse.ArgumentParser(description="以测试或生产模式运行脚本。")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--test", action="store_true", help="以测试模式运行")
    group.add_argument("-p", "--production", action="store_true", help="以生产模式运行")
    parser.add_argument(
        "-s",
        "--splice_index",
        action="store_true",
        help="仅处理问题文件中的第一个问题，用于测试",
    )
    parser.add_argument(
        "-m", "--max_workers", type=int, default=20, help="最大并发线程数，默认为20"
    )
    parser.add_argument("-q", "--question_file", type=str, help="指定问题文件")
    parser.add_argument(
        "-v", "--vote_times", type=int, default=1, help="指定投票次数，默认为1"
    )
    parser.add_argument(
        "-c",
        "--api_config_name",
        type=str,
        default="GLM",
        help="API 配置名称，默认为 GLM",
    )
    args = parser.parse_args()

    if not args.test and not args.production:
        parser.error("必须指定 -t（测试模式）或 -p（生产模式）之一。")

    if not utils.load_config(args.api_config_name):
        parser.error(f"未找到名称为 {args.api_config_name} 的 API 配置。")
    return args


def handle_question(query):
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
    id = line["id"]
    question = handle_question(line["question"])
    try:
        logger.info(f"【开始获取问题{id}的答案】", question)
        vote_res = api.vote(id, question, vote_times).clone()
        logger.special(
            f"【{id}的最终答案】: \n{vote_res.final_reasoning_answer.get_correct_answer()}"
        )
        return vote_res
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"【获取问题{id}的答案出错】: {e}")
        logger.error(trace)
        return {"id": id, "question": question, "answer": str(e)}


def main():
    args = parse_args()
    is_test = args.test
    max_workers = args.max_workers
    question_path = args.question_file or (
        test_input_path if is_test else production_input_path
    )
    splice_index = args.splice_index
    api_config_name = args.api_config_name

    global vote_times
    vote_times = args.vote_times

    logger.init()
    load_tools()

    os.makedirs(submit_dir, exist_ok=True)
    os.makedirs(solution_dir, exist_ok=True)

    with open(question_path, "r", encoding="utf-8") as f:
        q_json_list = [json.loads(line.strip()) for line in f]
    if splice_index:
        q_json_list = q_json_list[:1]

    logger.debug(
        f"【运行模式】: {'测试' if is_test else '生产'},",
        f"【API 配置】: {api_config_name},",
        f"【问题总数】: {len(q_json_list)},",
        f"【投票次数】: {vote_times},",
        f"【最大并发线程数】: {max_workers},",
        f"【仅处理第一个问题】: {splice_index},",
        f"【问题文件】: {question_path}",
    )

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    submit_path = os.path.join(submit_dir, f"试试又不会怎样_result_{date_str}.jsonl")
    solution_path = os.path.join(solution_dir, f"solution_{date_str}.json")

    vote_results = []
    submit_result_list = []

    with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            vote_res = future.result()
            if isinstance(vote_res, VoteResult):
                vote_results.append(vote_res)
                submit_result_list.append(
                    vote_res.to_submit_json()
                    if isinstance(vote_res, VoteResult)
                    else vote_res
                )
                save_submit_result(submit_result_list, submit_path)
                save_solutions(vote_results, solution_path)
            else:
                submit_result_list.append(vote_res)
                save_submit_result(submit_result_list, submit_path)


def save_submit_result(submit_result_list, submit_path):
    submit_result_list.sort(key=lambda x: x["id"])
    with open(submit_path, "w", encoding="utf-8") as f:
        for result in submit_result_list:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


def save_solutions(vote_results: list[VoteResult], result_path):
    vote_results.sort(key=lambda x: x.id)
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                [vote_res.to_dict(export_api_response) for vote_res in vote_results],
                ensure_ascii=False,
                default=utils.custom_serializer,
            )
        )


if __name__ == "__main__":
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
