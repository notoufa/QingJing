import json
import re


def natural_key(text):
    """自然排序的 key 生成函数，保证 '10' 在 '9' 之后"""
    parts = re.split(r"(\d+)", text.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def read_meta():
    with open("meta.json", "r", encoding="utf-8") as f:
        return json.load(f)


def process_meta(meta):
    for table in meta:
        fields = table["字段名"]
        descs = table["字段含义"]

        field_descs = [
            {"字段名": fields[i], "字段含义": descs[i]} for i in range(len(fields))
        ]

        field_descs.sort(key=lambda x: natural_key(x["字段名"]))

        table["字段名"] = [item["字段名"] for item in field_descs]
        table["字段含义"] = [item["字段含义"] for item in field_descs]
    meta.sort(key=lambda x: natural_key(x["数据表名"]))


def write_meta(meta):
    with open("sorted_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    meta = read_meta()
    process_meta(meta)
    write_meta(meta)
    print("字段排序完成，结果已保存至 sorted_meta.json")
