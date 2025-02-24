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

submit_dir = "results"
solution_dir = "solutions"
export_api_response = False

test_vote_times = 1
test_splice_index = True
test_input_path = "questions/test.jsonl"

production_vote_times = 1
production_splice_index = False
production_input_path = "questions/question_B.jsonl"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the script in test or production mode."
    )
    parser.add_argument("-t", "--test", action="store_true", help="Run in test mode")
    parser.add_argument(
        "-p", "--production", action="store_true", help="Run in production mode"
    )
    args = parser.parse_args()

    if not args.test and not args.production:
        parser.error("You must specify either -t (test) or -p (production) mode.")

    return args


def handle_question(query):
    replace_dict = {
        "下放阶段以ON DP和OFF DP为标志，回收阶段以A架开机和关机为标志": "",
        "平均作业时长": "平均每天作业时长",
        "开机时长": "运行时长",
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
            f"【{id}的最终答案】: \n{vote_res.final_reasoning_answer.answer}"
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

    global vote_times

    logger.init()

    os.makedirs(submit_dir, exist_ok=True)
    os.makedirs(solution_dir, exist_ok=True)

    logger.info(f"【运行模式】: {'测试' if is_test else '生产'}")

    question_path = test_input_path if is_test else production_input_path
    vote_times = test_vote_times if is_test else production_vote_times
    splice_index = test_splice_index if is_test else production_splice_index

    with open(question_path, "r", encoding="utf-8") as f:
        q_json_list = [json.loads(line.strip()) for line in f]
    if splice_index:
        q_json_list = q_json_list[:1]

    logger.info(f"【问题总数】: {len(q_json_list)}")

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    submit_path = os.path.join(submit_dir, f"result_{date_str}.jsonl")
    solution_path = os.path.join(solution_dir, f"solution_{date_str}.json")

    vote_results = []
    submit_result_list = []

    with cf.ThreadPoolExecutor(max_workers=20) as executor:
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
    logger.special(f"【程序运行时间】 {elapsed_time_minutes:.2f} 分钟")
    logger.info(
        "------------------------------【程序结束】------------------------------"
    )
