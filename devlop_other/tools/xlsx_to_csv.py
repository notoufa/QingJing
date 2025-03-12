import pandas as pd
import sys

input_file = sys.argv[1]
output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.xlsx', '.csv')

try:
    df = pd.read_excel(input_file, engine='openpyxl')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"转换成功：{output_file}")
except Exception as e:
    print(f"转换失败：{e}")
