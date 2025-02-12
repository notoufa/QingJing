# 预处理数据文件

from collections import defaultdict
import os
import pandas as pd

data_path = '../assets/初赛数据/'

def merge_csv_files(folder_path, out_path):
    # Store files by their prefix
    file_groups = defaultdict(list)
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv') and '字段释义' not in file_name:
            prefix = file_name.rsplit('_', 1)[0]
            file_groups[prefix].append(os.path.join(folder_path, file_name))

    # Merge files with the same prefix
    for prefix, file_list in file_groups.items():
        merged_df = pd.concat((pd.read_csv(file) for file in file_list), ignore_index=True)
        output_file = os.path.join(out_path, f'{prefix}.csv')
        merged_df.rename(columns={merged_df.columns[0]: "index"}, inplace=True)
        print(output_file)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        merged_df.to_csv(output_file, index=False)
        print(f'Merged files with prefix "{prefix}" into {output_file}')

merge_csv_files(data_path, 'data')