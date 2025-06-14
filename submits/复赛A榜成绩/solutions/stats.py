import json
from collections import Counter

# 读取原始数据
with open('solution_2025-03-21-第2次.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 收集所有 subtask_count
subtask_count_list = []

for item in data:
    solutions = item.get("solutions", [])
    for sol in solutions:
        decomposition = sol.get("decomposition", {})
        subtasks = decomposition.get("subtasks", [])
        subtask_count = len(subtasks)
        subtask_count_list.append(subtask_count)

# 使用 Counter 统计频率
count_freq = Counter(subtask_count_list)

# 按 subtask_count 升序排序，并转为字典
sorted_count_freq = dict(sorted(count_freq.items()))

# 输出为 JSON 文件
with open('subtask_count_frequencies2.json', 'w', encoding='utf-8') as f:
    json.dump(sorted_count_freq, f, ensure_ascii=False, indent=4)

print("频次统计并排序完成，结果已保存到 subtask_count_frequencies.json。")
