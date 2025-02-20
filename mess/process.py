# import pandas as pd


# def modify_columns(input_file, output_file, columns_to_remove, new_columns):
#     df = pd.read_csv(input_file)

#     df.drop(
#         columns=[col for col in columns_to_remove if col in df.columns], inplace=True
#     )

#     for col_name, default_value in new_columns.items():
#         df[col_name] = default_value

#     df.to_csv(output_file, index=False)
#     print(f"处理完成，已保存至 {output_file}")


# input_csv = "submits/正确答案.csv"
# output_csv = "submits/处理后.csv"
# columns_to_remove = [
#     "answer_submits/2025-02-17-第6次.jsonl",
#     "answer_submits/2025-02-18-第2次.jsonl",
# ]
# new_columns = {"思考过程": "", "正确答案": ""}
# modify_columns(input_csv, output_csv, columns_to_remove, new_columns)

import json
import csv

input_file = "../assets/question.jsonl"
output_file = "output.csv"

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8", newline="") as outfile:
    writer = csv.writer(outfile)
    
    writer.writerow(["ID", "问题", "答案"])
    
    for idx, line in enumerate(infile, start=1):
        data = json.loads(line.strip())
        id = data.get("id", "")
        question = data.get("question", "")
        answer = data.get("answer", "")
        writer.writerow([id, question, answer])

print(f"转换完成，CSV 文件已保存为 {output_file}")
