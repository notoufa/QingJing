"""主函数"""

import json
import concurrent.futures as cf
import os
import traceback
import api
import time
from solution import VoteResult
import logger

submit_dir = "results"
solution_dir = "solutions"
export_api_response = False
# 模式选择
mode = "test"
if mode == "test":
    splice_index = True
    question_path = "../assets/test.jsonl"
    vote_times = 1
else:
    splice_index = False
    question_path = "../assets/question.jsonl"
    vote_times = 3


def handle_question(query):
    replace_dict = {
        "下放阶段以ON DP和OFF DP为标志，回收阶段以A架开机和关机为标志": "",
        "平均作业时长": "平均每天作业时长",
    }
    for key, value in replace_dict.items():
        query = query.replace(key, value)
    return query


def process_one(line: dict) -> VoteResult | dict:
    id = line["id"]
    question = line["question"]
    question = handle_question(question)
    try:
        logger.info(f"【开始获取问题{id}的答案】", question)
        vote_res = api.vote(id, question, vote_times).clone()
        logger.special(f"【{id}的最终答案】: \n{vote_res.final_answer}")
        return vote_res
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"【获取问题{id}的答案出错】: {e}")
        logger.error(trace)
        return {
            "id": id,
            "question": question,
            "error_message": e,
            "traceback": trace,
        }


def main():
    logger.init()

    vote_results: list[VoteResult] = []
    submit_result_list: list[dict] = []

    with open(question_path, "r", encoding="utf-8") as f:
        q_json_list = [json.loads(line.strip()) for line in f]
    if splice_index:
        q_json_list = q_json_list[:1]

    logger.info(f"【问题总数】: {len(q_json_list)}")

    os.makedirs(submit_dir, exist_ok=True)
    os.makedirs(solution_dir, exist_ok=True)
    date_str = time.strftime("%Y-%m-%d", time.localtime())
    submit_path = os.path.join(submit_dir, "result_" + date_str + ".jsonl")
    solution_path = os.path.join(solution_dir, "solution_" + date_str + ".json")

    with cf.ThreadPoolExecutor(max_workers=20) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            vote_res = future.result()
            vote_results.append(vote_res)
            submit_result_list.append(vote_res.to_submit_json() if isinstance(vote_res, VoteResult) else vote_res)
            save_submit_result(submit_result_list, submit_path)
            save_solutions(vote_results, solution_path)


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
                [vote_res.to_dict(export_api_response) for vote_res in vote_results], ensure_ascii=False
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
