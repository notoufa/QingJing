# Copyright (c) 2025 试试又不会怎样
#
# This file is part of DeepseaAgent.
#
# All rights reserved.
# Licensed under the MIT License.

import json
import concurrent.futures as cf
import os
import sys
import traceback
import time
from schema import VoteResult
import logger
import utils
from agent.start import process_one

result_dir = "devlop_output/results"
solution_dir = "devlop_output/solutions"
answer_filepath = "devlop_home/test.jsonl"


def load_params():
    """
    加载参数
    """
    utils.load_api_config()
    utils.load_module_config()

    in_param_path = sys.argv[1]

    with open(in_param_path, "r", encoding="utf-8") as load_f:
        content = load_f.read()
        input_params = json.loads(content)

    question_filepath = None
    source_data_filepath = None

    try:
        question_filepath = input_params["fileData"]["questionFilePath"]
        source_data_filepath = input_params["fileData"]["sourceDataFilePath"]
    except Exception as e:
        logger.error(f"【读取输入参数出错】{input_params}")

    date_str = time.strftime("%Y-%m-%d", time.localtime())
    if len(sys.argv) > 2:
        out_path = sys.argv[2]
    else:
        out_path = os.path.join(result_dir, f"result_{date_str}.jsonl")
    solution_path = os.path.join(solution_dir, f"solution_{date_str}.json")

    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    os.makedirs(os.path.dirname(solution_path), exist_ok=True)

    return question_filepath, source_data_filepath, solution_path, out_path


def main():
    vote_result_list = []
    submit_result_list = []
    question_filepath, source_data_filepath, solution_path, out_path = load_params()

    with open(question_filepath, "r", encoding="utf-8") as f:
        question_list = [json.loads(line.strip()) for line in f]

    logger.debug(
        f"【API 配置】: {utils.api_config.config_name},",
        f"【投票次数】: {utils.module_config.vote_times},",
        f"【问题文件】: {question_filepath}",
        f"【问题总数】: {len(question_list)},",
        f"【输出文件】: {out_path}",
    )

    with cf.ThreadPoolExecutor(max_workers=20) as executor:
        future_list = [executor.submit(process_one, item) for item in question_list]
        for future in cf.as_completed(future_list):
            single_res = future.result()
            if isinstance(single_res, VoteResult):
                vote_result_list.append(single_res)
                submit_result_list.append(single_res.to_submit_json())
            else:
                submit_result_list.append(single_res)
            utils.save_submit_result(submit_result_list, out_path)
            utils.save_solutions(vote_result_list, solution_path)


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
