import pandas as pd


def modify_columns(input_file, output_file, columns_to_remove, new_columns):
    df = pd.read_csv(input_file)

    df.drop(
        columns=[col for col in columns_to_remove if col in df.columns], inplace=True
    )

    for col_name, default_value in new_columns.items():
        df[col_name] = default_value

    df.to_csv(output_file, index=False)
    print(f"处理完成，已保存至 {output_file}")


input_csv = "submits/正确答案.csv"
output_csv = "submits/处理后.csv"
columns_to_remove = [
    "answer_submits/2025-02-17-第6次.jsonl",
    "answer_submits/2025-02-18-第2次.jsonl",
]
new_columns = {"思考过程": "", "正确答案": ""}
modify_columns(input_csv, output_csv, columns_to_remove, new_columns)
