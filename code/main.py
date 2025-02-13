"""主函数"""

import json
import concurrent.futures as cf
import os
import traceback
import api
import time
import logger


question_path = "../assets/test.jsonl"
result_dir = "results"


def process_one(question_json):
    line = question_json
    query = line["question"]
    try:
        logger.info(f"【获取问题{line['id']}的答案】", query)
        answer = str(api.get_answer(question=query))
        logger.special(f"【{line['id']}的最终答案】: {answer}")
        return {"id": line["id"], "question": query, "answer": answer}
    except Exception as e:
        logger.error(f"【获取问题{line['id']}的答案出错】: {query}")
        logger.error(traceback.format_exc())
        return {"id": line["id"], "question": query, "answer": "Error: " + str(e)}


def main():
    result_json_list = []

    with open(question_path, "r", encoding="utf-8") as f:
        q_json_list = [json.loads(line.strip()) for line in f]
    q_json_list = q_json_list[:1]

    logger.info(f"【问题总数】: {len(q_json_list)}")

    with cf.ThreadPoolExecutor(max_workers=20) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            result_json_list.append(future.result())

    result_json_list.sort(key=lambda x: x["id"])
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    result_path = os.path.join(result_dir, "result_" + str(int(time.time())) + ".json")
    with open(result_path, "w", encoding="utf-8") as f:
        for result in result_json_list:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    elapsed_time_minutes = (end_time - start_time) / 60
    logger.special(f"【程序运行时间】 {elapsed_time_minutes:.2f} 分钟")
