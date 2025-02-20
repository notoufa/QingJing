import json

input_file = "submits/2025-02-20-第1次-84.9.jsonl"
output_file = "submits/2025-02-20-第2次.jsonl"


def extract_answers(input_file, output_file):
    """
    读取 JSONL 文件，提取 '问题答案' 部分，并写入新的 JSONL 文件。

    :param input_file: 输入 JSONL 文件路径
    :param output_file: 输出 JSONL 文件路径
    """
    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", encoding="utf-8"
    ) as outfile:
        for line in infile:
            data = json.loads(line.strip())
            answer = data.get("answer", "")
            final_answer = answer.split("\n\n\n")[-1].strip()
            final_answer = final_answer.split("\n")[-1].strip()

            result = {
                "id": data.get("id"),
                "question": data.get("question"),
                "answer": final_answer,
            }

            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")


def merge_answers(input_files, output_file):
    """
    读取一系列 JSONL 文件，导出为csv，分别为 id, question, answer_1, answer_2, ... 的格式。

    :param input_files: 输入的 JSONL 文件路径列表
    :param output_file: 输出 CSV 文件路径
    """
    with open(output_file, "w", encoding="utf-8") as outfile:
        id_to_answers = {}
        for input_file in input_files:
            with open(input_file, "r", encoding="utf-8") as infile:
                for line in infile:
                    data = json.loads(line.strip())
                    id = data.get("id")
                    question = data.get("question")
                    answer = data.get("answer")
                    if id not in id_to_answers.keys():
                        id_to_answers[id] = {
                            "id": id,
                            "question": question,
                            "answers": [answer],
                        }
                    else:
                        id_to_answers[id]["answers"].append(answer)

        columns = ["id", "question"]
        columns.extend([f"answer_{file_name}" for file_name in input_files])
        outfile.write(",".join(columns) + "\n")
        for id, data in id_to_answers.items():
            row = [data["id"], data["question"]]
            row.extend(f"\"{answer}\"" for answer in data["answers"])
            outfile.write(",".join(row) + "\n")


extract_answers(input_file, output_file)
# merge_answers(["submits/2025-02-17-第6次.jsonl", "submits/2025-02-18-第2次.jsonl"], "submits/对比.csv")
