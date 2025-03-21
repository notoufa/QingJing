import json
import concurrent.futures as cf
import os
import sys
import traceback
import api
import time
from solution import VoteResult
import logger
import utils
import tools

result_dir = "devlop_output/results"
solution_dir = "devlop_output/solutions"
answer_filepath = "devlop_home/test.jsonl"
replace_filepath = "devlop_home/knowledge/replace.json"


def handle_question(query):
    """
    预处理问题
    """
    with open(replace_filepath, "r", encoding="utf-8") as f:
        replace_dict = json.load(f)
    for key, value in replace_dict.items():
        query = query.replace(key, value)
    return query


def process_one(line: dict) -> VoteResult | dict:
    """
    获取一个问题的解决过程及答案
    """
    id = line["id"]
    int_id = int(id.split("_")[-1])
    question = handle_question(line["question"])

    # with open(answer_filepath, "r", encoding="utf-8") as f:
    #     answer_list = [json.loads(line.strip()) for line in f]
    # answer = None
    # for item in answer_list:
    #     if item["id"] == id:
    #         answer = item["answer"]
    #         return {"id": id, "question": question, "answer": answer}
    
    # if int_id not in range(51, 76):
    #     return {"id": id, "question": question, "answer": ""}

    try:
        logger.info(f"【开始获取问题{id}的答案】", question)
        vote_res = api.vote(id, question, utils.module_config.vote_times).clone()
        vote_res.init_question = line["question"]
        logger.special(
            f"【{id}的最终答案】:\n",
            vote_res.final_reasoning_answer.get_correct_answer(),
        )
        return vote_res
    except Exception as e:
        logger.error(f"【获取问题{id}的答案出错】错误堆栈：\n{traceback.format_exc()}")
        return {"id": id, "question": line["question"], "answer": str(e)}


def init():
    """
    初始化
    """
    tools.load_tools()
    utils.load_api_config()
    utils.load_module_config()
    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(solution_dir, exist_ok=True)


def main():
    init()
    in_param_path = sys.argv[1]

    with open(in_param_path, "r", encoding="utf-8") as load_f:
        content = load_f.read()
        input_params = json.loads(content)

    question_filepath = input_params["fileData"]["questionFilePath"]

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    solution_path = os.path.join(solution_dir, f"solution_{date_str}.json")
    if len(sys.argv) > 2:
        out_path = sys.argv[2]
    else:
        out_path = os.path.join(result_dir, f"result_{date_str}.jsonl")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(question_filepath, "r", encoding="utf-8") as f:
        question_list = [json.loads(line.strip()) for line in f]

    logger.debug(
        f"【API 配置】: {utils.api_config.config_name},",
        f"【问题总数】: {len(question_list)},",
        f"【投票次数】: {utils.module_config.vote_times},",
        f"【问题文件】: {question_filepath}",
        f"【输出文件】: {out_path}",
    )

    vote_results = []
    submit_result_list = []

    with cf.ThreadPoolExecutor(max_workers=20) as executor:
        future_list = [executor.submit(process_one, item) for item in question_list]
        for future in cf.as_completed(future_list):
            vote_res = future.result()
            if isinstance(vote_res, VoteResult):
                vote_results.append(vote_res)
                submit_result_list.append(vote_res.to_submit_json())
                utils.save_submit_result(submit_result_list, out_path)
                utils.save_solutions(vote_results, solution_path)
            else:
                submit_result_list.append(vote_res)
                utils.save_submit_result(submit_result_list, out_path)


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
