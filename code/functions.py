"""定义与tools.py中的函数对应的API接口，用于返回函数调用的结果"""

import json
import traceback
import pandas as pd


def get_data_by_time_range(table_name, start_time, end_time, columns=None, status=None):
    """
    根据数据表名、开始时间、结束时间、列名获取指定时间范围内的相关数据。返回值为包含指定列名和对应值的字典。

    参数:
    table_name (str): 数据表名
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'
    columns (list): 需要查询的列名列表，如果为None，则返回所有列
    status (str): 需要筛选的状态（例如 '开机'、'关机'），如果为None，则不筛选状态

    返回:
    dict: 包含指定列名和对应值的字典，或错误信息
    """
    metadata = {
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "columns": columns,
        "status": status,
    }

    try:
        df = pd.read_csv(f"data/{table_name}.csv")
    except FileNotFoundError:
        return {
            "error": f"数据表 {table_name} 不存在",
            "metadata": metadata,
        }

    df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")

    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    if (
        start_time.minute == end_time.minute
        and start_time.hour == end_time.hour
        and start_time.day == end_time.day
    ):
        start_time = start_time.replace(second=0)
        end_time = end_time.replace(second=59)
    filtered_data = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]
    if filtered_data.empty:
        return {
            "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 的数据",
            "metadata": metadata,
        }

    if status is not None:
        filtered_data = filtered_data[filtered_data["status"] == status]
        if filtered_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到状态为 {status} 的数据",
                "metadata": metadata,
            }

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

    result = {}
    for column in columns:
        if column == "csvTime":
            result[column] = (
                filtered_data[column].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            )
        else:
            result[column] = filtered_data[column].values.tolist()

    return {
        "result": result,
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

    with open("prompts/table_meta.json", "r", encoding="utf-8") as file:
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


def get_actions_by_time_range(start_time, end_time):
    """
    根据开始时间和结束时间，查询什么设备在进行什么动作。返回正在进行的设备动作列表。
    参数:
    start_time (str): 开始时间，格式为 'YYYY-MM-DD HH:MM:SS'
    end_time (str): 结束时间，格式为 'YYYY-MM-DD HH:MM:SS'

    返回:
    dict: 包含设备状态变化的时间点和对应状态的字典，或错误信息
    """

    # 确保两个时间的差值至少是一分钟，如果小于一分钟，则end_time为start_time后一分钟
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
            df = pd.read_csv(f"data/{table_name}.csv")
        except FileNotFoundError:
            return {"error": f"数据表 {table_name} 不存在", "metadata": metadata}

        df["csvTime"] = pd.to_datetime(df["csvTime"], unit="ns")  # 假设时间戳是纳秒级别

        filtered_data = df[
            (df["csvTime"] >= start_time_dt)
            & (df["csvTime"] <= end_time_dt)
            & (df["status"] != "False")
        ]

        if filtered_data.empty:
            return {
                "error": f"在数据表 {table_name} 中未找到时间范围 {start_time} 到 {end_time} 且 status 不为 'False' 的数据",
                "metadata": metadata,
            }

        if "status" not in filtered_data.columns:
            return {
                "error": f"数据表 {table_name} 中不存在 'status' 列",
                "metadata": metadata,
            }

        status_changes = filtered_data[["csvTime", "status"]].copy()

        status_changes.loc[:, "csvTime"] = status_changes["csvTime"].dt.strftime(
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
        "metadata": {"start_time": start_time, "end_time": end_time},
    }


def get_device_parameter_by_name(parameter_name_cn):
    """
    根据设备名，查询设备的参数值。
    :param device_name: 参数中文名
    :return: 返回包含参数信息的字典
    """
    df = pd.read_csv("data/设备参数详情表.csv")
    if not df["Channel_Text_CN"].str.contains(parameter_name_cn).any():
        return {
            "error": f"未找到包含 '{parameter_name_cn}' 的参数中文名",
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
    return parameter_dict


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
        raise FileNotFoundError(f"文件 {file_path} 未找到")

    try:
        df["csvTime"] = pd.to_datetime(df["csvTime"])
    except Exception as e:
        raise ValueError(f"时间列转换失败: {e}")

    filtered_data = df[
        (df["csvTime"] >= start_time) & (df["csvTime"] < end_time)
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
        "start_time": start_time,
        "end_time": end_time,
        "device_name": device_name,
    }

    device_config = {
        "全船": ["甲板机械设备", "推进系统", "舵桨"],
        "甲板机械设备": ["折臂吊车", "一号门架", "二号门架", "绞车变频器"],
        "折臂吊车": ("device_13_11_meter_1311", "13-11-6_v"),
        "一号门架": ("device_1_5_meter_105", "1-5-6_v"),
        "二号门架": ("device_13_14_meter_1314", "13-14-6_v"),
        "绞车变频器": ("device_1_15_meter_115", "1-15-6_v"),
        "推进系统": ["一号推进变频器", "二号推进变频器", "可伸缩推", "侧推"],
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
        result = round(total_energy, 2)
    else:
        table_name, power_column = device_config[device_name]
        file_path = f"data/{table_name}.csv"
        try:
            filtered_data = load_and_filter_data(
                file_path, start_time, end_time, power_column
            )
            if filtered_data is None:
                result = None
            total_energy_kWh = filtered_data["energy_kWh"].sum()
            result = round(total_energy_kWh, 2)
        except Exception as e:
            print(f"计算设备 {device_name} 能耗时出错: {e}")
    return {
        "result": result,
        "unit": "kWh",
        "metadata": metadata,
    }


def get_running_duration_by_time_range(start_time, end_time, type):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的'折臂吊车开机时长'、'A架开机时长'、'A架实际运行时长'、'作业时长'。

    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :param type: 查询类型，'折臂吊车开机时长'、'A架开机时长'、'A架实际运行时长'、'作业时长'
    :return: 包含三种格式开机时长的字符串
    """
    metadata = {
        "start_time": start_time,
        "end_time": end_time,
        "type": type,
    }

    device_config = {
        "折臂吊车开机时长": (
            "data/device_13_11_meter_1311.csv",
            "status",
            "折臂吊车开机",
            "折臂吊车关机",
        ),
        "A架开机时长": (
            "data/Ajia_plc_1.csv",
            "status",
            "A架开机",
            "A架关机",
        ),
        "作业时长": (
            "data/Port3_ksbg_9.csv",
            "status",
            "ON_DP",
            "OFF_DP",
        ),
        "A架实际运行时长": (
            "data/Ajia_plc_1.csv",
            "check_current_presence",
            "有电流",
            "无电流",
        ),
    }

    if type not in device_config:
        raise ValueError(f"未知的类型: {type}")

    file_path, check_field_name, start_status, end_status = device_config[type]

    df = pd.read_csv(file_path)

    df["csvTime"] = pd.to_datetime(df["csvTime"])

    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    df_filtered = df[(df["csvTime"] >= start_time) & (df["csvTime"] <= end_time)]

    total_duration = pd.Timedelta(0)
    start_uptime = None

    for index, row in df_filtered.iterrows():
        if row[check_field_name] == start_status:
            start_uptime = row["csvTime"]
        elif row[check_field_name] == end_status and start_uptime is not None:
            end_uptime = row["csvTime"]
            total_duration += end_uptime - start_uptime
            start_uptime = None

    seconds = total_duration.total_seconds()

    return {
        "result": convert_seconds(seconds),
        "metadata": metadata,
    }


def get_total_energy_generation_or_fuel_consumption_by_time_range(
    start_time,
    end_time,
    type,
    device_name,
    diesel_density=None,
    diesel_calorific_value=None,
):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的发电量或燃油消耗量

    :param start_time: 查询的开始时间（字符串或 datetime 类型）
    :param end_time: 查询的结束时间（字符串或 datetime 类型）
    :param type: 查询类型，'理论发电量'、'实际发电量'、'燃油消耗量'
    :param device_name: 设备名称，'一号柴油发电机'、'二号柴油发电机'、'三号柴油发电机'、'四号柴油发电机'、'柴油发电机组'
    :param diesel_density: 柴油密度，单位kg/L
    :param diesel_calorific_value: 柴油热值，单位MJ/kg
    :return: 发电量或燃油消耗量
    """
    metadata = {
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
            "柴油发电机组": [
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
            "柴油发电机组": [
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
            "柴油发电机组": [
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
        result = round(total_energy, 2)
        mj_result = round(total_mj_energy, 2)
    else:
        file_name, field_name = device_config[type][device_name]
        file_path = f"data/{file_name}.csv"
        try:
            filtered_data = load_and_filter_data(
                file_path, start_time, end_time, field_name
            )
            if filtered_data is None:
                result = None
            total_energy_kWh = filtered_data["energy_kWh"].sum()
            if type == "理论发电量":
                result = round(
                    total_energy_kWh * diesel_density * diesel_calorific_value / 3.6, 2
                )
                mj_result = round(
                    total_energy_kWh * diesel_density * diesel_calorific_value, 2
                )
            else:
                result = round(total_energy_kWh, 2)

        except Exception as e:
            print(f"计算设备 {device_name} {type}时出错: {e}")
    return {
        "result": result,
        "unit": "L" if type == "燃油消耗量" else "Kwh",
        "mj_result": mj_result,
        "mj_result_desc": "mj_result表示转换为MJ单位的值",
        "metadata": metadata,
    }


def calculate_math_operations(operation, operands):
    """
    进行数学运算，包括加法、减法、乘法、除法、求和和求平均值。

    参数:
        operation (str): 运算类型，支持 '加法'、'减法'、'乘法'、'除法'、'求和'、'求平均值'、求最大值、求最小值。
        operands (list): 数值列表，所有元素必须为数字。

    返回:
        float: 运算结果。

    异常:
        ValueError: 如果遇到不支持的运算类型或者在除法中除数为0。
    """
    metadata = {
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
        result = 1
        for num in operands:
            result *= num
    elif operation == "除法":
        result = operands[0]
        for num in operands[1:]:
            if num == 0:
                raise ValueError("除法错误：除数不能为0")
            result /= num
    elif operation == "求和":
        result = sum(operands)
    elif operation == "求平均值":
        result = sum(operands) / len(operands)
    elif operation == "求最大值":
        result = max(operands)
    elif operation == "求最小值":
        result = min(operands)
    else:
        return {
            "error": "不支持的运算类型: {}".format(operation),
            "metadata": metadata,
        }

    return {
        "result": result,
        "metadata": metadata,
    }


from datetime import datetime


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
        }
    except ValueError as e:
        return {
            "error": f"时间格式错误或无效输入: {e}",
            "metadata": metadata,
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
    if seconds < 0:
        raise ValueError("时间不能为负数")

    minutes = seconds // 60
    demical_minutes = seconds / 60
    remaining_seconds = seconds % 60

    hours = seconds // 3600
    remaining_minutes = (seconds % 3600) // 60
    demical_hours = seconds / 3600

    return {
        "by_seconds": f"{seconds}秒",
        "by_minutes": f"{minutes}分钟{remaining_seconds}秒",
        "by_demical_minutes": f"{demical_minutes}分钟",
        "by_hours": f"{hours}小时{remaining_minutes}分钟{remaining_seconds}秒",
        "by_demical_hours": f"{demical_hours}小时",
    }


function_map: dict[str, callable] = {
    "get_data_by_time_range": get_data_by_time_range,
    "get_actions_by_time_range": get_actions_by_time_range,
    "get_device_parameter_by_name": get_device_parameter_by_name,
    "get_total_energy_consumption_by_time_range": get_total_energy_consumption_by_time_range,
    "get_running_duration_by_time_range": get_running_duration_by_time_range,
    "get_total_energy_generation_or_fuel_consumption_by_time_range": get_total_energy_generation_or_fuel_consumption_by_time_range,
    "calculate_math_operations": calculate_math_operations,
    "calculate_time_interval": calculate_time_interval,
    "convert_seconds": convert_seconds,
}
