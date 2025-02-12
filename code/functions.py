# 定义与tools.py中的函数对应的API接口，用于返回函数调用的结果。

def get_data_by_time_range(table_name, start_time, end_time, columns=[]):
    """
    根据数据表名、开始时间、结束时间、列名获取指定时间范围内的相关数据。返回值为包含指定列名和对应值的字典。
    """
    return {
        "table_name": table_name,
        "start_time": start_time,
        "end_time": end_time,
        "columns": columns,
    }


def get_actions_by_time_range(start_time, end_time):
    """
    根据开始时间和结束时间，查询什么设备在进行什么动作。返回正在进行的设备动作列表。
    """
    return {
        "start_time": start_time,
        "end_time": end_time,
    }


def get_device_parameter_by_name(device_name):
    """
    根据设备名，查询设备的参数值。
    """
    return {
        "device_name": device_name,
    }


def get_total_energy_consumption_by_time_range(start_time, end_time, device_name):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的总能耗。
    """
    return {
        "start_time": start_time,
        "end_time": end_time,
        "device_name": device_name,
    }


def get_startup_time_by_time_range(start_time, end_time, device_name):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的启动时间。
    """
    return {
        "start_time": start_time,
        "end_time": end_time,
        "device_name": device_name,
    }


def get_running_time_by_time_range(start_time, end_time, device_name):
    """
    根据开始时间和结束时间，查询设备在指定时间范围内的运行时间。
    """
    return {
        "start_time": start_time,
        "end_time": end_time,
        "device_name": device_name,
    }


function_map: dict[str, callable] = {
    "get_data_by_time_range": get_data_by_time_range,
    "get_actions_by_time_range": get_actions_by_time_range,
    "get_device_parameter_by_name": get_device_parameter_by_name,
    "get_total_energy_consumption_by_time_range": get_total_energy_consumption_by_time_range,
    "get_startup_time_by_time_range": get_startup_time_by_time_range,
    "get_running_time_by_time_range": get_running_time_by_time_range,
}
