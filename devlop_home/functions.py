"""实现函数调用对应的API接口，接收调用参数，返回函数调用的结果"""

import json
import traceback
from datetime import datetime
import pandas as pd
from actions import action_table_configs
from texttable import Texttable
from typing import List, Dict
from utils import *

import logger

table_meta_file = "devlop_home/knowledge/table_meta.json"
table_base_path = "devlop_data/data"


def get_text_table(result: dict) -> str:
    if not result:
        return

    table = Texttable()
    table.set_deco(Texttable.HEADER)

    column_widths = [
        10 if header not in ["csvTime", "current_status"] else 20
        for header in result.keys()
    ]
    table.set_cols_width(column_widths)

    table.set_cols_align(["c" for _ in result.keys()])

    headers = list(result.keys())
    table.add_row(headers)

    rows = zip(*[result[col] for col in headers])
    for row in rows:
        table.add_row(row)

    return table.draw()


def get_data_by_time_range(
    table_name,
    start_time: str,
    end_time: str,
    columns=None,
    conditions_logic: str = "AND",
    conditions: List[Dict[str, str]] = None,
):
    """
    根据数据表名、开始时间、结束时间、列名获取指定时间范围内的相关数据。返回值为包含指定列名和对应值的字典。

    参数:
    table_name (str): 数据表名
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    columns (list): 需要查询的列名列表，如果为None，则返回所有列
    conditions_logic (str): 过滤条件逻辑，支持AND、OR
    conditions (List[Dict[str, str]], 可选): 过滤条件，每个条件包含：
        - "column": 过滤列名
        - "operator": 过滤操作符（in, ==, >, <, >=, <=, !=）
        - "value": 过滤值
    返回:
    dict: 包含指定列名和对应值的字典，或错误信息
    """
    metadata = {
        "function_name": "get_data_by_time_range",
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "columns": columns,
        "conditions_logic": conditions_logic,
        "conditions": conditions,
    }

    try:
        df = pd.read_csv(f"{table_base_path}/{table_name}.csv")
    except FileNotFoundError:
        return {
            "error": f"数据表 {table_name} 不存在",
            "metadata": metadata,
        }

    df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")

    start_time = start_time.replace("24:00:00", "23:59:59")
    end_time = end_time.replace("24:00:00", "23:59:59")

    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    if (
        start_time.minute == end_time.minute
        and start_time.hour == end_time.hour
        and start_time.day == end_time.day
        and start_time.second != end_time.second
    ):
        start_time = start_time.replace(second=0)
        end_time = end_time.replace(second=59)

    if start_time == end_time:
        closest_data = df.iloc[(df["csvTime"] - start_time).abs().argsort()[:1]]
        if closest_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到时间点 {start_time} 附近的数据",
                "metadata": metadata,
            }
        filtered_data = closest_data
    else:
        filtered_data = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    if filtered_data.empty:
        return {
            "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 的数据",
            "metadata": metadata,
        }

    # filter_work_status = False

    if conditions:
        logic = conditions_logic.upper()
        if logic not in ["AND", "OR"]:
            return {"error": f"不支持的逻辑操作符: {logic}", "metadata": metadata}
        mask = None
        for condition in conditions:
            cond_col, operator, cond_value = (
                condition["column"],
                condition["operator"],
                condition["value"],
            )

            if cond_col not in filtered_data.columns:
                return {
                    "error": f"条件列 {cond_col} 不存在于数据表 {table_name}",
                    "metadata": metadata,
                }

            try:
                cond_value = float(cond_value)
                column_values = filtered_data[cond_col].astype(float)
            except ValueError:
                cond_value = str(cond_value)
                column_values = filtered_data[cond_col].astype(str)

            if operator == "==":
                condition_mask = column_values == cond_value
            elif operator == "!=":
                condition_mask = column_values != cond_value
            elif operator == ">":
                condition_mask = column_values > cond_value
            elif operator == "<":
                condition_mask = column_values < cond_value
            elif operator == ">=":
                condition_mask = column_values >= cond_value
            elif operator == "<=":
                condition_mask = column_values <= cond_value
            elif operator == "in":
                if isinstance(cond_value, str):
                    try:
                        cond_value = [v.strip() for v in cond_value.split(",")]
                    except Exception:
                        return {
                            "error": f"条件值 {cond_value} 解析失败，应为以逗号分隔的字符串列表（示例：value1,value2,value3）",
                            "metadata": metadata,
                        }
                else:
                    return {
                        "error": f"条件值 {cond_value} 格式错误，应为以逗号分隔的字符串列表（示例：value1,value2,value3）",
                        "metadata": metadata,
                    }
                condition_mask = column_values.isin(cond_value)
            else:
                return {"error": f"不支持的操作符: {operator}", "metadata": metadata}

            if mask is None:
                mask = condition_mask
            else:
                mask = (
                    mask & condition_mask if logic == "AND" else mask | condition_mask
                )

        if mask is not None:
            filtered_data = filtered_data[mask]

    if filtered_data.empty:
        return {"error": f"所有过滤条件应用后，没有匹配的数据", "metadata": metadata}

    if columns is None:
        columns = filtered_data.columns.tolist()

    missing_columns = [
        column for column in columns if column not in filtered_data.columns
    ]
    if missing_columns:
        return {
            "error": f"列名 {missing_columns} 在数据表 {table_name} 中不存在",
            "metadata": metadata,
        }

    if "csvTime" not in columns and "csvTime" in filtered_data.columns:
        columns.append("csvTime")

    result = {}
    for column in columns:
        if column == "csvTime":
            result[column] = (
                filtered_data[column].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            )
        else:
            result[column] = filtered_data[column].replace({pd.NA: None}).tolist()

    logger.special("\n", get_text_table(result))

    return {
        "result": result,
        "length": len(filtered_data),
        "column_desc": get_meta_by_table_columns(table_name, columns),
        "metadata": metadata,
    }


def get_meta_by_table_columns(table_name, columns):
    """
    根据数据表名和列名，获取数据表中指定列的元信息。

    参数:
    table_name (str): 数据表名
    columns (list): 需要查询的列名列表

    返回:
    dict: 包含列名和对应元信息的字典，或错误信息
    """

    with open(table_meta_file, "r", encoding="utf-8") as file:
        raw_table_data = json.load(file)

    table_meta = None

    for table in raw_table_data:
        if table["table_name"] == table_name:
            table_meta = table

    if table_meta is None:
        return {
            "error": f"数据表 {table_name} 的元信息不存在",
        }

    column_desc = {}
    for column in columns:
        for tmp in table_meta["columns"]:
            if tmp["name"] == column:
                column_desc[column] = tmp["desc"]

    return column_desc


def aggregate_data(
    table_name: str,
    start_time: str,
    end_time: str,
    column: str,
    method: str,
    conditions_logic: str = "AND",
    conditions: List[Dict[str, str]] = None,
):
    """
    根据数据表名、开始时间、结束时间对指定列进行聚合操作，并支持按条件过滤。

    参数：
    table_name (str): 数据表名
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    column (str): 需要进行聚合计算的列名
    method (str): 聚合方法，可选：
        - "avg"（平均值）
        - "max"（最大值）
        - "min"（最小值）
        - "mode"（众数）
        - "sum"（总和）
        - "count"（数据条数）
    conditions_logic (str): 过滤条件逻辑，支持AND、OR
    conditions (List[Dict[str, str]], 可选): 过滤条件，每个条件包含：
        - "column": 过滤列名
        - "operator": 过滤操作符（in, ==, >, <, >=, <=, !=）
        - "value": 过滤值

    返回：
    dict: 包含聚合结果的字典，或错误信息
    """
    metadata = {
        "function_name": "aggregate_data",
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "column": column,
        "method": method,
        "conditions": conditions,
    }

    try:
        df = pd.read_csv(f"{table_base_path}/{table_name}.csv")
    except FileNotFoundError:
        return {"error": f"数据表 {table_name} 不存在", "metadata": metadata}

    if "csvTime" not in df.columns:
        return {"error": "数据表缺少 csvTime 时间列", "metadata": metadata}

    df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")

    start_time = pd.to_datetime(start_time.replace("24:00:00", "23:59:59"))
    end_time = pd.to_datetime(end_time.replace("24:00:00", "23:59:59"))

    if (
        start_time.minute == end_time.minute
        and start_time.hour == end_time.hour
        and start_time.day == end_time.day
        and start_time.second != end_time.second
    ):
        start_time = start_time.replace(second=0)
        end_time = end_time.replace(second=59)

    if start_time == end_time:
        closest_data = df.iloc[(df["csvTime"] - start_time).abs().argsort()[:1]]
        if closest_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到时间点 {start_time} 附近的数据",
                "metadata": metadata,
            }
        filtered_data = closest_data
    else:
        filtered_data = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    if conditions:
        logic = conditions_logic.upper()
        if logic not in ["AND", "OR"]:
            return {"error": f"不支持的逻辑操作符: {logic}", "metadata": metadata}
        mask = None
        for condition in conditions:
            cond_col, operator, cond_value = (
                condition["column"],
                condition["operator"],
                condition["value"],
            )

            if cond_col not in filtered_data.columns:
                return {
                    "error": f"条件列 {cond_col} 不存在于数据表 {table_name}",
                    "metadata": metadata,
                }

            try:
                cond_value = float(cond_value)
                column_values = filtered_data[cond_col].astype(float)
            except ValueError:
                cond_value = str(cond_value)
                column_values = filtered_data[cond_col].astype(str)

            if operator == "==":
                condition_mask = column_values == cond_value
            elif operator == "!=":
                condition_mask = column_values != cond_value
            elif operator == ">":
                condition_mask = column_values > cond_value
            elif operator == "<":
                condition_mask = column_values < cond_value
            elif operator == ">=":
                condition_mask = column_values >= cond_value
            elif operator == "<=":
                condition_mask = column_values <= cond_value
            elif operator == "in":
                if isinstance(cond_value, str):
                    try:
                        cond_value = [v.strip() for v in cond_value.split(",")]
                    except Exception:
                        return {
                            "error": f"条件值 {cond_value} 解析失败，应为以逗号分隔的字符串列表（示例：value1,value2,value3）",
                            "metadata": metadata,
                        }
                else:
                    return {
                        "error": f"条件值 {cond_value} 格式错误，应为以逗号分隔的字符串列表（示例：value1,value2,value3）",
                        "metadata": metadata,
                    }
                condition_mask = column_values.isin(cond_value)
            else:
                return {"error": f"不支持的操作符: {operator}", "metadata": metadata}

            if mask is None:
                mask = condition_mask
            else:
                mask = (
                    mask & condition_mask if logic == "AND" else mask | condition_mask
                )
        if mask is not None:
            filtered_data = filtered_data[mask]

    if column not in filtered_data.columns:
        return {
            "error": f"列 {column} 不存在于数据表 {table_name}",
            "metadata": metadata,
        }

    values = filtered_data[column].dropna()

    try:
        if method == "avg":
            result = values.mean()
        elif method == "max":
            result = values.max()
        elif method == "min":
            result = values.min()
        elif method == "mode":
            result = values.mode()[0] if not values.mode().empty else None
        elif method == "sum":
            result = values.sum()
        elif method == "count":
            result = len(values)
        else:
            return {
                "error": f"不支持的聚合方法: {method}",
                "metadata": metadata,
            }
    except Exception as e:
        logger.error("聚合失败", e)
        logger.error(traceback.format_exc())
        return {
            "error": f"聚合错误: {e}",
            "metadata": metadata,
        }

    return {
        f"{column}_{method}": round(result, 2) if isinstance(result, float) else result,
        "column_desc": get_meta_by_table_columns(table_name, [column]),
        "metadata": metadata,
    }


def get_actions_by_time_range(start_time, end_time):
    """
    根据开始时间和结束时间，查询什么设备在进行什么动作。返回正在进行的设备动作列表。
    参数:
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'

    返回:
    dict: 包含设备状态变化的时间点和对应状态的字典，或错误信息
    """
    metadata = {
        "function_name": "get_actions_by_time_range",
        "start_time": start_time,
        "end_time": end_time,
    }

    # 确保两个时间的差值至少是一分钟，如果小于一分钟，则end_time为start_time后一分钟
    start_time = start_time.replace("24:00:00", "23:59:59")
    end_time = end_time.replace("24:00:00", "23:59:59")

    start_time_dt = pd.to_datetime(start_time)
    end_time_dt = pd.to_datetime(end_time)
    if (end_time_dt - start_time_dt).total_seconds() < 60:
        end_time_dt = start_time_dt + pd.Timedelta(minutes=1)

    def get_status_changes(table_name, device_name):
        """
        辅助函数：获取指定设备在指定时间范围内的状态变化。

        参数:
        table_name (str): 数据表名
        device_name (str): 设备名称

        返回:
        dict: 包含设备状态变化的时间点和对应状态的字典，或错误信息
        """
        metadata = {
            "table_name": table_name,
            "start_time": start_time,
            "end_time": end_time,
        }

        try:
            df = pd.read_csv(f"{table_base_path}/{table_name}.csv")
        except FileNotFoundError:
            return {"error": f"数据表 {table_name} 不存在", "metadata": metadata}

        df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")

        filtered_data = df[
            (df["csvTime"] >= start_time_dt)
            & (df["csvTime"] <= end_time_dt)
            & (df["key_action"] != "False")
        ]

        if filtered_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 且 status 不为 'False' 的数据",
                "metadata": metadata,
            }

        if "key_action" not in filtered_data.columns:
            return {
                "error": f"数据表 {table_name} 中不存在 'status' 列",
                "metadata": metadata,
            }

        status_changes = filtered_data[["csvTime", "key_action"]].copy()

        status_changes["csvTime"] = status_changes["csvTime"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return {
            "设备名称": device_name,
            "正在进行的关键动作": status_changes.to_dict(orient="records"),
        }

    result1 = get_status_changes("Ajia_plc_1", "A架")
    result2 = get_status_changes("device_13_11_meter_1311", "折臂吊车")
    result3 = get_status_changes("Port3_ksbg_9", "定位系统")

    results = [
        result for result in [result1, result2, result3] if "error" not in result
    ]

    return {
        "result": results,
        "metadata": metadata,
    }


def get_device_parameter_by_name(parameter_name_cn):
    """
    根据设备名，查询设备的参数值。
    :param device_name: 参数中文名
    :return: 返回包含参数信息的字典
    """
    metadata = {
        "function_name": "get_device_parameter_by_name",
        "parameter_name_cn": parameter_name_cn,
    }

    df = pd.read_csv(f"{table_base_path}/设备参数详情.csv")
    if not df["Channel_Text_CN"].str.contains(parameter_name_cn).any():
        return {
            "error": f"未找到包含 '{parameter_name_cn}' 的参数中文名",
            "metadata": metadata,
        }

    parameter_info = df[df["Channel_Text_CN"].str.contains(parameter_name_cn)].iloc[0]

    parameter_dict = {
        "参数名": parameter_info["Channel_Text"],
        "参数中文名": parameter_info["Channel_Text_CN"],
        "参数下限": parameter_info["Alarm_Information_Range_Low"],
        "参数上限": parameter_info["Alarm_Information_Range_High"],
        "报警值的单位": parameter_info["Alarm_Information_Unit"],
        "报警值": parameter_info["Parameter_Information_Alarm"],
        "屏蔽值": parameter_info["Parameter_Information_Inhibit"],
        "延迟值": parameter_info["Parameter_Information_Delayed"],
        "安全保护设定值": parameter_info["Safety_Protection_Set_Value"],
        "附注（达到安全保护设定值时的措施）": parameter_info["Remarks"],
    }

    parameter_dict = {
        key: (None if pd.isna(value) else value)
        for key, value in parameter_dict.items()
    }

    for key, value in parameter_dict.items():
        str_value = str(value).strip()
        if "↑" in str_value:
            parameter_dict[key] = "若超过 " + str_value.replace("↑", " 则触发 ")
        if "↓" in str_value:
            parameter_dict[key] = "若低于 " + str_value.replace("↓", " 则触发 ")

    if (
        parameter_dict["安全保护设定值"] is not None
        and parameter_info["Remarks"] is not None
    ):
        parameter_dict["安全保护设定值"] += parameter_info["Remarks"]
    if parameter_dict["报警值"] is not None:
        parameter_dict["报警值"] += "报警"

    return {
        "result": parameter_dict,
        "metadata": metadata,
    }


def load_and_filter_data(file_path, start_time, end_time, power_column):
    """
    加载 CSV 文件并筛选指定时间范围内的数据
    :param file_path: CSV 文件路径
    :param start_time: 开始时间
    :param end_time: 结束时间
    :param power_column: 功率列名
    :return: 筛选后的 DataFrame
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        return {
            "error": f"文件 {file_path} 未找到",
        }
    try:
        df["csvTime"] = pd.to_datetime(df["csvTime"])
    except Exception as e:
        return {
            "error": f"时间列转换失败: {e}",
        }

    if isinstance(start_time, str):
        start_time_dt = pd.to_datetime(start_time)
    if isinstance(end_time, str):
        end_time_dt = pd.to_datetime(end_time)

    filtered_data = df[
        (df["csvTime"] >= start_time_dt) & (df["csvTime"] <= end_time_dt)
    ].copy()

    if filtered_data.empty:
        return None

    filtered_data.loc[:, "diff_seconds"] = (
        filtered_data["csvTime"].diff().dt.total_seconds().shift(-1)
    )

    filtered_data.loc[:, "energy_kWh"] = (
        filtered_data["diff_seconds"] * filtered_data[power_column] / 3600
    )

    return filtered_data


def get_total_energy_consumption_by_time_range(start_time, end_time, device_name):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的总能耗。
    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :param device_name: 设备名称，默认为 '折臂吊车'
    :return: 总能耗（kWh，float 类型）
    """
    metadata = {
        "function_name": "get_total_energy_consumption_by_time_range",
        "start_time": start_time,
        "end_time": end_time,
        "device_name": device_name,
    }

    start_time = start_time.replace("24:00:00", "23:59:59")
    end_time = end_time.replace("24:00:00", "23:59:59")

    device_config = {
        "全船": ["甲板机械设备", "推进系统", "舵桨"],
        "甲板机械设备": ["折臂吊车", "A架", "绞车变频器"],
        "A架": ["一号门架", "二号门架"],
        "折臂吊车": ("device_13_11_meter_1311", "13-11-6_v"),
        "一号门架": ("device_1_5_meter_105", "1-5-6_v"),
        "二号门架": ("device_13_14_meter_1314", "13-14-6_v"),
        "绞车变频器": ("device_1_15_meter_115", "1-15-6_v"),
        "推进系统": ["主推", "可伸缩推", "侧推"],
        "主推": ["一号推进变频器", "二号推进变频器"],
        "一号推进变频器": ("Port3_ksbg_8", "P3_15"),
        "二号推进变频器": ("Port4_ksbg_7", "P4_16"),
        "可伸缩推": ("Port4_ksbg_8", "P4_21"),
        "侧推": ("Port3_ksbg_9", "P3_18"),
        "舵桨": ["一号舵桨转舵A", "一号舵桨转舵B", "二号舵桨转舵A", "二号舵桨转舵B"],
        "一号舵桨转舵A": ("device_1_2_meter_102", "1-2-6_v"),
        "一号舵桨转舵B": ("device_1_3_meter_103", "1-3-6_v"),
        "二号舵桨转舵A": ("device_13_2_meter_1302", "13-2-6_v"),
        "二号舵桨转舵B": ("device_13_3_meter_1303", "13-3-6_v"),
    }
    if device_name not in device_config.keys():
        return {
            "error": f"未知的设备名称: {device_name}",
            "metadata": metadata,
        }
    result = None
    if isinstance(device_config[device_name], list):
        total_energy = 0
        for sub_device in device_config[device_name]:
            try:
                energy = get_total_energy_consumption_by_time_range(
                    start_time, end_time, device_name=sub_device
                )["result"]
                if energy is not None:
                    total_energy += energy
            except Exception as e:
                print(f"计算设备 {sub_device} 能耗时出错: {e},{traceback.format_exc()}")
        result = total_energy
    else:
        table_name, power_column = device_config[device_name]
        file_path = f"{table_base_path}/{table_name}.csv"
        try:
            filtered_data = load_and_filter_data(
                file_path, start_time, end_time, power_column
            )
            if filtered_data is None:
                result = None
            total_energy_kWh = filtered_data["energy_kWh"].sum()
            result = total_energy_kWh
        except Exception as e:
            print(f"计算设备 {device_name} 能耗时出错: {e}")
    return {
        "result": result,
        "unit": "kWh",
        "metadata": metadata,
    }


def get_total_energy_generation_or_fuel_consumption_by_time_range(
    start_time: str,
    end_time: str,
    type: str,
    device_name: str,
    diesel_density=None,
    diesel_calorific_value=None,
):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的发电量或燃油消耗量

    :param start_time: 查询的开始时间（字符串类型）
    :param end_time: 查询的结束时间（字符串类型）
    :param type: 查询类型，'理论发电量'、'实际发电量'、'燃油消耗量'
    :param device_name: 设备名称，'一号柴油发电机'、'二号柴油发电机'、'三号柴油发电机'、'四号柴油发电机'、'整个柴油发电机组'
    :param diesel_density: 柴油密度，单位kg/L
    :param diesel_calorific_value: 柴油热值，单位MJ/kg
    :return: 发电量或燃油消耗量
    """
    metadata = {
        "function_name": "get_total_energy_generation_or_fuel_consumption_by_time_range",
        "start_time": start_time,
        "end_time": end_time,
        "type": type,
        "device_name": device_name,
        "diesel_density": diesel_density,
        "diesel_calorific_value": diesel_calorific_value,
    }

    device_config = {
        "燃油消耗量": {
            "一号柴油发电机": ("Port1_ksbg_1", "P1_3"),
            "二号柴油发电机": ("Port1_ksbg_1", "P1_25"),
            "三号柴油发电机": ("Port2_ksbg_1", "P2_3"),
            "四号柴油发电机": ("Port2_ksbg_1", "P2_25"),
            "整个柴油发电机组": [
                "一号柴油发电机",
                "二号柴油发电机",
                "三号柴油发电机",
                "四号柴油发电机",
            ],
        },
        "实际发电量": {
            "一号柴油发电机": ("Port1_ksbg_3", "P1_66"),
            "二号柴油发电机": ("Port1_ksbg_3", "P1_75"),
            "三号柴油发电机": ("Port2_ksbg_2", "P2_51"),
            "四号柴油发电机": ("Port2_ksbg_3", "P2_60"),
            "整个柴油发电机组": [
                "一号柴油发电机",
                "二号柴油发电机",
                "三号柴油发电机",
                "四号柴油发电机",
            ],
        },
        "理论发电量": {
            "一号柴油发电机": ("Port1_ksbg_1", "P1_3"),
            "二号柴油发电机": ("Port1_ksbg_1", "P1_25"),
            "三号柴油发电机": ("Port2_ksbg_1", "P2_3"),
            "四号柴油发电机": ("Port2_ksbg_1", "P2_25"),
            "整个柴油发电机组": [
                "一号柴油发电机",
                "二号柴油发电机",
                "三号柴油发电机",
                "四号柴油发电机",
            ],
        },
    }

    if type not in device_config.keys():
        return {
            "error": f"未知的类型: {type}",
            "metadata": metadata,
        }

    if device_name not in device_config[type].keys():
        return {
            "error": f"未知的设备名称: {device_name}",
            "metadata": metadata,
        }

    if type == "理论发电量" and (
        diesel_density is None or diesel_calorific_value is None
    ):
        return {
            "error": f"柴油密度或柴油热值不能为None",
            "metadata": metadata,
        }

    result = None
    mj_result = None
    if isinstance(device_config[type][device_name], list):
        total_energy = 0
        total_mj_energy = 0
        for sub_device in device_config[type][device_name]:
            try:
                sub_result = (
                    get_total_energy_generation_or_fuel_consumption_by_time_range(
                        start_time,
                        end_time,
                        type,
                        sub_device,
                        diesel_density,
                        diesel_calorific_value,
                    )
                )
                energy = sub_result["result"]
                mj_energy = sub_result["mj_result"]
                if energy is not None:
                    total_energy += energy
                if mj_energy is not None:
                    total_mj_energy += mj_energy
            except Exception as e:
                print(f"计算设备 {sub_device} {type}时出错: {e}")
        result = total_energy
        mj_result = total_mj_energy
    else:
        file_name, field_name = device_config[type][device_name]
        file_path = f"{table_base_path}/{file_name}.csv"
        try:
            filtered_data = load_and_filter_data(
                file_path, start_time, end_time, field_name
            )
            if filtered_data is None:
                result = None
            total_energy_kWh = filtered_data["energy_kWh"].sum()
            if type == "理论发电量":
                result = (
                    total_energy_kWh * diesel_density * diesel_calorific_value / 3.6
                )

                mj_result = total_energy_kWh * diesel_density * diesel_calorific_value

            else:
                result = total_energy_kWh

        except Exception as e:
            print(f"计算设备 {device_name} {type}时出错: {e}")
    return {
        "result": result,
        "unit": "L" if type == "燃油消耗量" else "kWh",
        "mj_result": mj_result,
        "mj_result_desc": "mj_result表示转换为MJ单位的值",
        "metadata": metadata,
    }


def calculate_action_proportion(
    start_time: str, end_time: str, key_action: str, time_point: str
):
    """
    计算指定时间段内指定动作在指定时间点前发生的比例

    :param start_time: 时间段的起始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    :param end_time: 时间段的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    :param action: 需要计算比例的动作名称，如 '起吊'、'入水' 等
    :param time_point: 指定时间点，格式为 'HH:MM'

    :return: 动作在指定时间点前发生的比例，返回百分比
    """
    metadata = {
        "function_name": "calculate_action_proportion",
        "start_time": start_time,
        "end_time": end_time,
        "action": key_action,
        "time_point": time_point,
    }

    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    time_point_dt = datetime.strptime(time_point, "%H:%M")
    time_point_dt = time_point_dt.replace(
        year=start_dt.year, month=start_dt.month, day=start_dt.day
    )

    if key_action not in action_table_configs.keys():
        return {
            "error": f"动作 {key_action} 不存在",
            "metadata": metadata,
        }

    get_data_result = get_data_by_time_range(
        action_table_configs[key_action],
        start_time,
        end_time,
        columns=["csvTime"],
        conditions=[{"column": "key_action", "operator": "==", "value": key_action}],
    )

    try:
        logger.info("【calculate_action_proportion中间结果】", get_data_result)
        table_data = get_data_result["result"]
    except:
        return {
            "result": 0,
            "unit": "%",
            "metadata": metadata,
        }

    before_count = 0
    total_count = 0
    day_map = {}
    for res_time in table_data["csvTime"]:
        res_time_dt = datetime.strptime(res_time, "%Y-%m-%d %H:%M:%S")
        res_day = datetime.strftime(res_time_dt, "%Y-%m-%d")
        if not day_map.get(res_day):
            day_map[res_day] = {
                "performed": True,
                "filtered": False,
            }
        time_point_dt = time_point_dt.replace(
            year=res_time_dt.year, month=res_time_dt.month, day=res_time_dt.day
        )
        if res_time_dt < time_point_dt:
            day_map[res_day] = {
                "performed": True,
                "filtered": True,
            }

    for key in day_map:
        if day_map[key]["filtered"]:
            before_count += 1

    total_count = len(day_map)

    if total_count == 0:
        return 0

    proportion = (before_count / total_count) * 100
    return {
        "result": proportion,
        "unit": "%",
        "metadata": metadata,
    }


def calculate_math_operations(operation, operands):
    """
    进行数学运算，包括加法、减法、乘法、除法、求和、求绝对值和求平均值。

    参数:
        operation (str): 运算类型，支持 '加法'、'减法'、'乘法'、'除法'、'求和'、'求平均值'、'求绝对值'、'求最大值'、'求最小值'。
        operands (list): 数值列表，所有元素必须为数字。

    返回:
        float: 运算结果。

    异常:
        ValueError: 如果遇到不支持的运算类型或者在除法中除数为0。
    """
    try:
        metadata = {
            "function_name": "calculate_math_operations",
            "operation": operation,
            "operands": operands,
        }

        if not operands:
            return {
                "error": "操作数不能为空",
                "metadata": metadata,
            }

        if operation == "加法":
            result = sum(operands)
        elif operation == "减法":
            result = operands[0]
            for num in operands[1:]:
                result -= num
        elif operation == "乘法":
            if len(operands) == 1:
                return {
                    "error": "乘法错误：操作数至少为2个",
                    "metadata": metadata,
                }
            result = 1
            for num in operands:
                result *= num
        elif operation == "除法":
            if len(operands) == 1:
                return {
                    "error": "除法错误：操作数至少为2个",
                    "metadata": metadata,
                }
            result = operands[0]
            for num in operands[1:]:
                if num == 0:
                    return {
                        "error": "除法错误：除数不能为0",
                        "metadata": metadata,
                    }
                result /= num
        elif operation == "求和":
            result = sum(operands)
        elif operation == "求平均值":
            result = sum(operands) / len(operands)
        elif operation == "求最大值":
            result = max(operands)
        elif operation == "求最小值":
            result = min(operands)
        elif operation == "求绝对值":
            result = [abs(num) for num in operands]
        else:
            return {
                "error": "不支持的运算类型: {}".format(operation),
                "metadata": metadata,
            }

        return {
            "result": result,
            "metadata": metadata,
        }
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "metadata": metadata,
        }


def calculate_time_interval(start_time: str, end_time: str):
    """
    计算两个时间点之间的时间间隔。

    参数:
        start_time (str): 起始时间，格式为 'YYYY-MM-DD HH:MM:SS'。
        end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'。

    返回:
        计算得到的时间间隔
    """

    metadata = {
        "function_name": "calculate_time_interval",
        "start_time": start_time,
        "end_time": end_time,
    }
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        start_dt = datetime.strptime(start_time, fmt)
        end_dt = datetime.strptime(end_time, fmt)

        seconds = (end_dt - start_dt).total_seconds()
        return {
            "result": convert_seconds(seconds),
            "metadata": metadata,
            "range": (
                "时间范围为{}到{}".format(start_time, end_time)
                if seconds > 0
                else "时间范围为{}到{}".format(end_time, start_time)
            ),
            "desc": (
                f"{start_time}在{end_time}之前"
                if seconds > 0
                else f"{start_time}在{end_time}之后"
            ),
        }
    except ValueError as e:
        return {
            "error": f"时间格式错误或无效输入: {e}",
            "metadata": metadata,
        }


def sort_by_datetime(
    input_list: List[str],
    order: str,
    conditions_logic: str = "AND",
    conditions: List[Dict[str, str]] = None,
):
    """
    对列表按完整日期时间（格式为 'YYYY-MM-DD HH:MM:SS'）进行排序，支持升序或降序。
    :param input_list (list[str]): 需要排序的列表，元素必须是日期字符串（格式为 'YYYY-MM-DD HH:MM:SS'）。
    :param order (str): 排序方式，'asc' 表示升序，'desc' 表示降序。
    :param conditions_logic (str): 过滤条件逻辑，支持AND、OR。
    :param conditions (List[Dict[str, str]], 可选): 过滤条件，每个条件包含：
            - "operator": 过滤操作符（in, ==, >, <, >=, <=, !=）
            - "value": 过滤值
    :return: 排序后的列表及相关信息。
    """
    metadata = {
        "function_name": "sort_by_datetime",
        "input_list": input_list,
        "order": order,
        "conditions_logic": conditions_logic,
        "conditions": conditions,
    }
    try:

        def parse_value(value):
            """解析日期字符串，确保可以正确排序"""
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        sorted_list = sorted(input_list, key=parse_value, reverse=(order == "desc"))
        if conditions:
            logic = conditions_logic.upper()
            if logic not in ["AND", "OR"]:
                return {"error": f"不支持的逻辑操作符: {logic}", "metadata": metadata}
            mask = (
                [False] * len(sorted_list)
                if logic == "OR"
                else [True] * len(sorted_list)
            )
            for condition in conditions:
                operator, value = (
                    condition["operator"],
                    condition["value"],
                )
                if operator not in ["in", "==", ">", "<", ">=", "<=", "!="]:
                    return {
                        "error": f"不支持的操作符: {operator}",
                        "metadata": metadata,
                    }
                try:
                    parsed_value = parse_value(value)
                except ValueError as e:
                    return {
                        "error": str(e),
                        "metadata": metadata,
                    }
                condition_mask = []
                for item in sorted_list:
                    try:
                        parsed_item = parse_value(item)
                    except ValueError:
                        condition_mask.append(False)
                        continue
                    if operator == "==":
                        condition_mask.append(parsed_item == parsed_value)
                    elif operator == "!=":
                        condition_mask.append(parsed_item != parsed_value)
                    elif operator == ">":
                        condition_mask.append(parsed_item > parsed_value)
                    elif operator == "<":
                        condition_mask.append(parsed_item < parsed_value)
                    elif operator == ">=":
                        condition_mask.append(parsed_item >= parsed_value)
                    elif operator == "<=":
                        condition_mask.append(parsed_item <= parsed_value)
                    elif operator == "in":
                        if isinstance(value, str):
                            value_list = [
                                parse_value(v.strip()) for v in value.split(",")
                            ]
                        else:
                            return {
                                "error": f"条件值 {value} 格式错误，in 操作符需要以逗号分隔的字符串",
                                "metadata": metadata,
                            }
                        condition_mask.append(parsed_item in value_list)
                if logic == "AND":
                    mask = [m1 & m2 for m1, m2 in zip(mask, condition_mask)]
                else:
                    mask = [m1 | m2 for m1, m2 in zip(mask, condition_mask)]
            sorted_list = [item for item, keep in zip(sorted_list, mask) if keep]
        dates = sorted(
            {
                datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                for x in sorted_list
            }
        )
        return {
            "result": sorted_list,
            "filted_dates": f"符合筛选条件的所有日期：{dates}",
            "metadata": metadata,
            "desc": f"列表已按日期+时间进行 {'升序' if order == 'asc' else '降序'} 排序；并返回",
        }
    except ValueError as e:
        return {
            "error": f"排序失败: {e}",
            "metadata": metadata,
        }


def sort_only_by_time(
    input_list: List[str],
    order: str,
    conditions_logic: str = "AND",
    conditions: List[Dict[str, str]] = None,
):
    """
    对日期时间列表仅按时间（格式为 'HH:MM:SS'）进行排序，支持升序或降序。
    :param input_list (list[str]): 需要排序的列表，元素必须是日期字符串（格式为 'YYYY-MM-DD HH:MM:SS'）。
    :param order (str): 排序方式，'asc' 表示升序，'desc' 表示降序。
    :param conditions_logic (str): 过滤条件逻辑，支持AND、OR。
    :param conditions (List[Dict[str, str]], 可选): 过滤条件，每个条件包含：
            - "operator": 过滤操作符（in, ==, >, <, >=, <=, !=）
            - "value": 过滤值
    :return: 排序后的列表及相关信息。
    """
    metadata = {
        "function_name": "sort_only_by_time",
        "input_list": input_list,
        "order": order,
        "conditions_logic": conditions_logic,
        "conditions": conditions,
    }
    try:

        def parse_value_date(value):
            """解析日期时间字符串，提取时间部分"""
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return dt.time()

        def parse_value_time(value):
            """解析时间字符串"""
            return datetime.strptime(value, "%H:%M:%S").time()

        # 按时间部分排序
        sorted_list = sorted(
            input_list, key=parse_value_date, reverse=(order == "desc")
        )

        if conditions:
            logic = conditions_logic.upper()
            if logic not in ["AND", "OR"]:
                return {"error": f"不支持的逻辑操作符: {logic}", "metadata": metadata}

            mask = (
                [False] * len(sorted_list)
                if logic == "OR"
                else [True] * len(sorted_list)
            )

            for condition in conditions:
                operator, value = (
                    condition["operator"],
                    condition["value"],
                )
                if operator not in ["in", "==", ">", "<", ">=", "<=", "!="]:
                    return {
                        "error": f"不支持的操作符: {operator}",
                        "metadata": metadata,
                    }

                try:
                    parsed_value = parse_value_time(value)  # 解析条件中的时间
                except ValueError as e:
                    return {
                        "error": str(e),
                        "metadata": metadata,
                    }

                condition_mask = []
                for item in sorted_list:
                    try:
                        parsed_item = parse_value_date(item)  # 解析输入列表中的时间
                    except ValueError:
                        condition_mask.append(False)
                        continue

                    if operator == "==":
                        condition_mask.append(parsed_item == parsed_value)
                    elif operator == "!=":
                        condition_mask.append(parsed_item != parsed_value)
                    elif operator == ">":
                        condition_mask.append(parsed_item > parsed_value)
                    elif operator == "<":
                        condition_mask.append(parsed_item < parsed_value)
                    elif operator == ">=":
                        condition_mask.append(parsed_item >= parsed_value)
                    elif operator == "<=":
                        condition_mask.append(parsed_item <= parsed_value)
                    elif operator == "in":
                        if isinstance(value, str):
                            value_list = [
                                parse_value_time(v.strip()) for v in value.split(",")
                            ]
                        else:
                            return {
                                "error": f"条件值 {value} 格式错误，in 操作符需要以逗号分隔的字符串",
                                "metadata": metadata,
                            }
                        condition_mask.append(parsed_item in value_list)

                if logic == "AND":
                    mask = [m1 & m2 for m1, m2 in zip(mask, condition_mask)]
                else:
                    mask = [m1 | m2 for m1, m2 in zip(mask, condition_mask)]

            sorted_list = [item for item, keep in zip(sorted_list, mask) if keep]

        dates = sorted(
            {
                datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                for x in sorted_list
            }
        )
        return {
            "result": sorted_list,
            "filted_dates": f"符合筛选条件的所有日期：{dates}",
            "metadata": metadata,
            "desc": f"列表已按时间进行 {'升序' if order == 'asc' else '降序'} 排序；并返回",
        }
    except ValueError as e:
        return {
            "error": f"排序失败: {e}",
            "metadata": metadata,
        }


def get_list_length(input_list: list):
    """
    统计列表长度。
    :param input_list: 需要统计的列表
    :return: 天数
    """
    return {
        "result": len(input_list),
        "metadata": {
            "input_list": input_list,
        },
    }


def convert_seconds(seconds):
    """
    将秒转换为三种格式的时间表示：
    1. by_seconds: 以秒显示
    2. by_minutes: 以分钟+秒显示
    3. by_hours: 以小时+分钟+秒显示

    :param seconds: 需要转换的时间（单位：秒）
    :return: 包含三种格式的字典
    """
    metadata = {
        "function_name": "convert_seconds",
        "seconds": seconds,
    }

    is_negative = False

    if seconds < 0:
        is_negative = True
        seconds = -seconds
    minutes = seconds // 60
    demical_minutes = seconds / 60
    remaining_seconds = seconds % 60

    hours = seconds // 3600
    remaining_minutes = (seconds % 3600) // 60
    demical_hours = seconds / 3600

    return {
        "result": {
            "by_seconds": f"{seconds}秒",
            "by_minutes": f"{minutes}分钟{remaining_seconds}秒",
            "by_integer_minutes": f"{int(demical_minutes)}分钟",
            "by_demical_minutes": f"{demical_minutes}分钟",
            "by_hours": f"{hours}小时{remaining_minutes}分钟{remaining_seconds}秒",
            "by_demical_hours": f"{demical_hours}小时",
            "is_negative": is_negative,
        },
        "metadata": metadata,
    }


def generate_simple_python_code(task_description: str):
    """
    调用大模型生成简单的 Python 代码。

    :param task_description: str，任务描述，包括输入、输出和注意事项。
    :return: str，生成的 Python 代码。
    """

    from utils import parse_code

    metadata = {
        "function_name": "generate_simple_python_code",
        "task_description": task_description,
    }
    CODE_GENERATE_PROMPT = f"""
    # 任务描述  
    {task_description}

    # 代码要求
    1. 生成的代码应该能够实现任务描述中的功能。
    2. 返回结果存在变量 `result` 中。

    # 输出要求  
    适当的思考过程是有益的，但最终必须输出代码。确保输出格式如下，并且只包含一个代码块：

    ```python  
    你的代码
    ```
    """
    messages = [
        {
            "role": "system",
            "content": "你是一个精通 Python 的编程助手，能够生成简洁且高效准确的 Python 代码。",
        },
        {"role": "user", "content": CODE_GENERATE_PROMPT},
    ]

    response = get_completion(messages)

    try:
        python_code = parse_code(response)
        return {
            "result": python_code,
            "metadata": metadata,
        }
    except Exception as e:
        return {
            "error": f"生成代码失败: {e}",
            "metadata": metadata,
        }


# coderesult = generate_simple_python_code('''二号柴油发电机组各温度相关参数的报警阈值如下：
#     缸套水温度> 102℃ 触发报警，
#     左排气温度> 730℃ 触发报警，
#     右排气温度> 730℃ 触发报警，
#     滑油温度> 110℃ 触发报警，
#     冷却液温度> 60℃ 触发报警，
#     冷风温度> 55℃ 触发报警，
#     热风温度> 100℃ 触发报警，
#     非驱动轴轴承温度> 90℃ 触发报警，
#     驱动轴轴承温度> 90℃ 触发报警，
#     U 相绕组温度显示> 145℃ 触发报警，
#     V 相绕组温度显示> 145℃ 触发报警，
#     W 相绕组温度显示> 145℃ 触发报警。
# 统计若实际温度超过 160 ，触发报警的参数数量''')

# if "result" in coderesult:
#     generated_code = coderesult["result"]
#     print("生成的代码：\n", generated_code)
#     local_scope = {}
#     exec(generated_code, {}, local_scope)
#     # 直接执行生成的代码
#     result=local_scope["result"]

#     try:
#         print("调用结果：",result)
#     except NameError:
#         print("生成的代码运行错误。")

function_map: dict[str, callable] = {
    "get_data_by_time_range": get_data_by_time_range,
    "get_actions_by_time_range": get_actions_by_time_range,
    "get_device_parameter_by_name": get_device_parameter_by_name,
    "get_total_energy_consumption_by_time_range": get_total_energy_consumption_by_time_range,
    "get_total_energy_generation_or_fuel_consumption_by_time_range": get_total_energy_generation_or_fuel_consumption_by_time_range,
    "calculate_action_proportion": calculate_action_proportion,
    "calculate_math_operations": calculate_math_operations,
    "calculate_time_interval": calculate_time_interval,
    "convert_seconds": convert_seconds,
    "aggregate_data": aggregate_data,
    "sort_by_datetime": sort_by_datetime,
    "sort_only_by_time": sort_only_by_time,
    "generate_simple_python_code": generate_simple_python_code,
    "get_list_length": get_list_length,
}

if __name__ == "__main__":
    print(
        get_data_by_time_range(
            "Port1_ksbg_3", "2024-08-19 13:34:27", "2024-08-19 13:34:27", ["P1_66"]
        )
    )
    # print(get_total_energy_consumption_by_time_range('2024-06-10 00:00:00', '2024-06-15 00:00:00', '舵桨'))
    # print(sort_only_by_time(['2024-08-17 09:38:27', '2024-08-18 09:08:27', '2024-08-19 08:54:27', '2024-08-20 06:25:09', '2024-08-21 08:51:09', '2024-08-22 00:00:09', '2024-08-23 10:30:08', '2024-08-24 09:09:08'], 'asc', 'AND', [{'operator': '<', 'value': '14:00:00'}] ))
    # print(
    #     aggregate_data(
    #         "device_1_2_meter_102",
    #         "2024-05-17 00:00:00",
    #         "2024-05-17 23:59:59",
    #         "1-2-10_v",
    #         "avg",
    #     )
    # )
    # for table in ["Ajia_plc_1", "Jiaoche_plc_1", "Port1_ksbg_1"]:
    #     for day in range(17, 31):
    #         date = f"2024-05-{day:02d}"
    #         missing_count = (
    #             1440
    #             - aggregate_data(
    #                 table, f"{date} 00:00:00", f"{date} 23:59:59", "csvTime", "count"
    #             )["csvTime_count"]
    #         )
    #         print(table, date, ":", missing_count, missing_count / 1440 * 100, "%")
