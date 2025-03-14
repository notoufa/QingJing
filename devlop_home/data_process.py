#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import pandas as pd
from collections import defaultdict
from datetime import datetime
import json
import logger
import traceback
import shutil

table_name_map = {
    "Ajia_plc_1.csv": "A架动作表.csv",
    "device_13_11_meter_1311.csv": "折臂吊车与小艇动作表.csv",
    "Port3_ksbg_9.csv": "艏推系统DP动作表.csv",
}

data_path = "devlop_data/assets/复赛数据/"
output_path = "devlop_data/data"

os.makedirs(output_path, exist_ok=True)
logger.init()

key_action_field = "key_action"
no_key_action_flag = "False"
running_status_field = "running_status"
stage_field = "stage"
no_stage_field = "False"
current_status_field = "current_status"
no_current_status_flag = "False"
running_flag = "开机运行中"
not_running_flag = "未运行"

# In[2]:


# 判断标注4个巡航阶段
import numpy as np

output_filename = "cruise_stage.csv"

file1 = "A架动作表.csv"
file2 = "艏推系统DP动作表.csv"
file3 = "Port3_ksbg_8.csv"
file4 = "Port4_ksbg_7.csv"
df_Ajia = pd.read_csv(os.path.join(output_path, file1), usecols=["csvTime", "stage"])
df_Dp = pd.read_csv(os.path.join(output_path, file2), usecols=["csvTime", "key_action"])
df_1tui = pd.read_csv(
    os.path.join(output_path, file3), usecols=["csvTime", "P3_15", "P3_32"]
)
df_2tui = pd.read_csv(
    os.path.join(output_path, file4), usecols=["csvTime", "P4_15", "P4_16"]
)
# 统一时间格式，并去除秒，只保留到分钟
for df in [df_Ajia, df_Dp, df_1tui, df_2tui]:
    df["csvTime"] = pd.to_datetime(df["csvTime"]).dt.strftime("%Y-%m-%d %H:%M")

# 以 df_1tui 为主，进行左连接合并
df_merge = (
    df_1tui.merge(df_Ajia, on="csvTime", how="left")
    .merge(df_Dp, on="csvTime", how="left")
    .merge(df_2tui, on="csvTime", how="left")
)
df_merge["cruise_stage"] = np.where(
    df_merge["key_action"] == "ON DP", "动力定位状态开始", ""
)
df_merge["cruise_stage"] = np.where(
    df_merge["key_action"] == "OFF DP", "动力定位状态结束", df_merge["cruise_stage"]
)


# 找到下一个P3_32为0的点
def find_next_zero(df, index):
    for i in range(index, len(df)):
        if df.loc[i, "P3_32"] == 0:
            return i
    return len(df)


# 找到下一个P3_32不为0的点
def find_next_nonzero(df, index):
    for i in range(index, len(df)):
        if df.loc[i, "P3_32"] > 300:
            return i
    return len(df)


df_merge["P3_32"] = pd.to_numeric(df_merge["P3_32"], errors="coerce")
first_index = 0
second_index = 0
for i in range(len(df)):
    if df_merge.loc[i, "P3_32"] == 0:
        first_index = i
        break
second_index = find_next_nonzero(df_merge, first_index + 1) - 1
df_merge.loc[first_index, "cruise_stage"] = "停泊状态开始"
df_merge.loc[second_index, "cruise_stage"] = "停泊状态结束"
while 1:
    first_index = find_next_zero(df_merge, second_index + 1)
    if first_index == len(df_merge):
        break
    if first_index - second_index < 120:
        df_merge.loc[second_index, "cruise_stage"] = ""
    else:
        df_merge.loc[first_index, "cruise_stage"] = "停泊状态开始"
    second_index = find_next_nonzero(df_merge, first_index + 1) - 1
    if second_index == len(df_merge) - 1:
        break
    df_merge.loc[second_index, "cruise_stage"] = "停泊状态结束"


def label_sailing_begin_end(df):
    sailing_begin_index = -1
    sailing_end_index = 0
    for i in range(1, df.shape[0]):
        if sailing_begin_index < sailing_end_index and df.loc[i, "P3_15"] >= 1000:
            sailing_begin_index = i
        if sailing_begin_index > sailing_end_index and df.loc[i, "P3_15"] < 1000:
            sailing_end_index = i
            df.loc[sailing_begin_index, "cruise_stage"] = "航渡状态开始"
            df.loc[sailing_end_index, "cruise_stage"] = "航渡状态结束"
        if df.loc[i, "stage"] == "布放阶段中" and df.loc[i, "key_action"] == "OFF DP":
            df.loc[i, "cruise_stage"] = "伴航状态开始"
        if df.loc[i, "stage"] == "回收阶段中" and df.loc[i, "key_action"] == "ON DP":
            df.loc[i - 1, "cruise_stage"] = "伴航状态结束"


label_sailing_begin_end(df_merge)
df_merge.to_csv(os.path.join(output_path, output_filename), index=False)

