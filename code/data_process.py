# 预处理数据文件

from collections import defaultdict
import os
import pandas as pd

data_path = '../assets/初赛数据/'

def merge_csv_files(folder_path, out_path):
    """
    将两个时间跨度的表合并为一张表
    :param folder_path: 原始数据路径.
    :param out_path: 转换结果路径.
    """
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

def convert_to_numeric(value):
    """
    将字符串转换为数字，如果无法转换则返回-1
    """
    try:
        return float(value)
    except ValueError:
        return -1


merge_csv_files(data_path, 'data')



# 给A架打标签
df = pd.read_csv('data/Ajia_plc_1.csv')
# A架开机
df['Ajia-3_v'] = df['Ajia-3_v'].apply(convert_to_numeric)
df['Ajia-5_v'] = df['Ajia-5_v'].apply(convert_to_numeric)
df['status'] = 'False'
df['check_current_presence'] = 'False'
for i in range(1, df.shape[0]):
    if (df.loc[i - 1, 'Ajia-3_v'] == -1 and (df.loc[i, 'Ajia-3_v'] >= 0)) and (df.loc[i - 1, 'Ajia-5_v'] == -1 and (df.loc[i, 'Ajia-5_v'] >= 0)):
        df.loc[i, 'status'] = '开机'
    if (df.loc[i, 'Ajia-3_v'] == -1 and df.loc[i - 1, 'Ajia-3_v']== 0) or (df.loc[i, 'Ajia-5_v'] == -1 and df.loc[i - 1, 'Ajia-5_v']== 0):
        df.loc[i, 'status'] = '关机'
    
    if (df.loc[i, 'Ajia-5_v'] > 0 and df.loc[i - 1, 'Ajia-5_v'] == -1):
        df.loc[i, 'check_current_presence'] = '有电流'
    if df.loc[i, 'Ajia-5_v'] > 0 and (df.loc[i - 1, 'Ajia-5_v'] == 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'check_current_presence'] = '有电流'
    if df.loc[i, 'Ajia-5_v'] == 0 and (df.loc[i - 1, 'Ajia-5_v'] > 0 or df.loc[i - 1, 'Ajia-5_v'] == '0'):
        df.loc[i, 'check_current_presence'] = '无电流'
