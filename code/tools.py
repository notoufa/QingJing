"""函数调用列表的描述信息"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_data_by_time_range",
            "description": "根据数据表名、开始时间、结束时间、列名和状态获取指定时间范围内的相关数据。返回值为包含指定列名和对应值的字典。",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "数据表名，例如 'device_logs'。",
                    },
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 00:00:00'。",
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 12:00:00'。",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要查询的列名列表。如果未提供，则返回所有列。",
                        "default": [],
                    },
                    "status": {
                        "type": "string",
                        "description": "需要筛选的状态。如果未提供，则不筛选状态。支持以下值：A架开机、ON_DP、征服者起吊、征服者入水、缆绳解除、A架摆回、小艇落座、A架关机、OFF_DP、折臂吊车开机、A架摆出、小艇检查完毕、小艇入水、缆绳挂妥、征服者出水、折臂吊车关机、征服者落座",
                        "default": "",
                    },
                },
                "required": ["table_name", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_actions_by_time_range",
            "description": "根据开始时间和结束时间，查询什么设备在进行什么动作。返回正在进行的设备及动作列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 00:00:00'。",
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 12:00:00'。",
                    },
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_parameter_by_name",
            "description": "根据参数中文名称查询设备参数信息，包括参数上下限范围、何时触发何种机制/事件。返回包含参数信息的字典。",
            "parameters": {
                "type": "object",
                "properties": {
                    "parameter_name_cn": {
                        "type": "string",
                        "description": "参数中文名，用于查询设备参数信息。",
                    }
                },
                "required": ["parameter_name_cn"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_total_energy_consumption_by_time_range",
            "description": "查询指定时间段内指定设备的总能耗。返回值为总能耗（kWh，float 类型）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 00:00:00'。",
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 12:00:00'。",
                    },
                    "device_name": {
                        "type": "string",
                        "description": "设备名称，支持以下值：'全船'、'甲板机械设备'（包括折臂吊车、门架、绞车等）、'折臂吊车'、'一号门架'、'二号门架'、'绞车变频器'、'推进系统'（推进相关设备）、'一号推进变频器'、'二号推进变频器'、'可伸缩推'、'侧推'、'舵桨'（整体舵桨系统）、'一号舵桨转舵A'、'一号舵桨转舵B'、'二号舵桨转舵A'、'二号舵桨转舵B'。",
                        "enum": [
                            "全船",
                            "甲板机械设备",
                            "折臂吊车",
                            "一号门架",
                            "二号门架",
                            "绞车变频器",
                            "推进系统",
                            "一号推进变频器",
                            "二号推进变频器",
                            "可伸缩推",
                            "侧推",
                            "舵桨",
                            "一号舵桨转舵A",
                            "一号舵桨转舵B",
                            "二号舵桨转舵A",
                            "二号舵桨转舵B",
                        ],
                    },
                },
                "required": ["start_time", "end_time", "device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_duration_by_time_range",
            "description": "查询指定时间段内折臂吊车运行时长、A架运行时长、A架实际运行时长或作业时长。返回三种格式（秒，分，时）的时长结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 00:00:00'。",
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 12:00:00'。",
                    },
                    "type": {
                        "type": "string",
                        "description": "查询类型，支持以下值：'折臂吊车运行时长'、'A架运行时长'、'A架实际运行时长'、'作业时长'。",
                        "enum": [
                            "折臂吊车运行时长",
                            "A架运行时长",
                            "A架实际运行时长",
                            "作业时长",
                        ],
                    },
                },
                "required": ["start_time", "end_time", "type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_total_energy_generation_or_fuel_consumption_by_time_range",
            "description": "查询指定时间段内的理论发电量、实际发电量或燃油消耗量。返回值为理论发电量（kWh，float 类型）、实际发电量（kWh，float 类型）或燃油消耗量（L，float 类型）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 00:00:00'。",
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'，例如 '2024-08-23 12:00:00'。",
                    },
                    "type": {
                        "type": "string",
                        "description": "查询的类型，支持以下值：'理论发电量'、'实际发电量'、'燃油消耗量'。",
                        "enum": [
                            "理论发电量",
                            "实际发电量",
                            "燃油消耗量",
                        ],
                    },
                    "device_name": {
                        "type": "string",
                        "description": "设备名称，支持以下值：'一号柴油发电机'、'二号柴油发电机'、'三号柴油发电机'、'四号柴油发电机'、'柴油发电机组'。",
                        "enum": [
                            "一号柴油发电机",
                            "二号柴油发电机",
                            "三号柴油发电机",
                            "四号柴油发电机",
                            "柴油发电机组",
                        ],
                    },
                    "diesel_density": {
                        "type": "number",
                        "description": "柴油密度，单位 kg/L。当 type 为 '理论发电量' 时需要提供。",
                    },
                    "diesel_calorific_value": {
                        "type": "number",
                        "description": "柴油热值，单位 MJ/kg。当 type 为 '理论发电量' 时需要提供。",
                    },
                },
                "required": ["start_time", "end_time", "type", "device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_action_proportion",
            "description": "计算指定时间段内指定动作在指定时间点前发生的比例，返回值为百分比。示例问题：统计2024/8/24-8/30在9点前开始作业的比例（%，保留2位小数）",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "时间段起始时间，格式为 'YYYY-MM-DD HH:MM:SS'。",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "时间段结束时间，格式为 'YYYY-MM-DD HH:MM:SS'。",
                    },
                    "action": {
                        "type": "string",
                        "description": "需要计算比例的动作名称，支持以下值：A架开机、ON_DP、征服者起吊、征服者入水、缆绳解除、A架摆回、小艇落座、A架关机、OFF_DP、折臂吊车开机、A架摆出、小艇检查完毕、小艇入水、缆绳挂妥、征服者出水、折臂吊车关机、征服者落座",
                    },
                    "time_point": {
                        "type": "string",
                        "description": "指定时间点，格式为 'HH:MM'，表示该时间点前的比例。",
                    },
                },
                "required": ["start_time", "end_time", "action", "time_point"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_math_operations",
            "description": "进行数学运算，包括加法、减法、乘法、除法、求和、求平均值、求最大值、求最小值。返回运算结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "指定运算类型，支持以下值： '加法'、'减法'、'乘法'、'除法'、'求和'、'求平均值'、'求最大值'、'求最小值'。",
                        "enum": [
                            "加法",
                            "减法",
                            "乘法",
                            "除法",
                            "求和",
                            "求平均值",
                            "求最大值",
                            "求最小值",
                        ],
                    },
                    "operands": {
                        "type": "array",
                        "description": "参与运算的数值列表，所有元素必须为数字。减法、除法的操作数至少为2个",
                        "items": {"type": "number"},
                    },
                },
                "required": ["operation", "operands"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_time_interval",
            "description": "计算两个时间点之间的时间间隔，支持秒、分钟、小时的计算。返回值为按秒、分钟、小时计算的时间间隔。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "起始时间，格式为 'YYYY-MM-DD HH:MM:SS'。",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，格式为 'YYYY-MM-DD HH:MM:SS'。",
                    },
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_seconds",
            "description": "将秒转换为分钟、小时，并返回对应的数值。",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "number",
                        "description": "时间间隔（秒），必须是非负数值。",
                    }
                },
                "required": ["seconds"],
            },
        },
    },
]


tools_description = [
    {
        "function_name": "get_data_by_time_range",
        "description": "输入：数据表名、开始时间、结束时间、列名和状态，   输出：从开始时间到结束时间内的对应列或特定状态（A架开机、ON_DP、征服者起吊、征服者入水、缆绳解除、A架摆回、小艇落座、A架关机、OFF_DP、折臂吊车开机、A架摆出、小艇检查完毕、小艇入水、缆绳挂妥、征服者出水、折臂吊车关机、征服者落座）的列数据。",
    },
    {
        "function_name": "get_actions_by_time_range",
        "description": "输入：开始时间、结束时间，     输出：从开始时间到结束时间内正在进行关键动作的全部设备及动作列表。",
    },
    {
        "function_name": "get_device_parameter_by_name",
        "description": "输入：参数中文名称，    输出：参数上下限范围、何时触发何种机制/事件(如报警值、屏蔽值、延迟值、安全保护设定值、达到安全保护设定值时的措施)。",
    },
    {
        "function_name": "get_total_energy_consumption_by_time_range",
        "description": "输入：开始时间、结束时间、设备名称，     输出：从开始时间到结束时间内指定设备('全船'、'甲板机械设备'（包括折臂吊车、门架、绞车等）、'折臂吊车'、'一号门架'、'二号门架'、'绞车变频器'、'推进系统'（推进相关设备）、'一号推进变频器'、'二号推进变频器'、'可伸缩推'、'侧推'、'舵桨'（整体舵桨系统）、'一号舵桨转舵A'、'一号舵桨转舵B'、'二号舵桨转舵A'、'二号舵桨转舵B')的总能耗。",
    },
    {
        "function_name": "get_running_duration_by_time_range",
        "description": "输入：开始时间、结束时间、查询类型('折臂吊车运行时长'、'A架运行时长'、'A架实际运行时长'、'作业时长')，     输出：从开始时间到结束时间内动作类型的时长结果（秒、分、时）。",
    },
    {
        "function_name": "get_total_energy_generation_or_fuel_consumption_by_time_range",
        "description": "输入：开始时间、结束时间、设备名称('一号柴油发电机'、'二号柴油发电机'、'三号柴油发电机'、'四号柴油发电机'、'柴油发电机组')，     输出：从开始时间到结束时间内设备的理论发电量、实际发电量或燃油消耗量。",
    },
    {
        "function_name": "calculate_math_operations",
        "description": "输入：运算类型('加法'、'减法'、'乘法'、'除法'、'求和'、'求平均值'、'求最大值'、'求最小值')，操作数列表，     输出：运算结果。",
    },
    {
        "function_name": "calculate_time_interval",
        "description": "输入：起始时间、结束时间，     输出：两个时间点之间的时间间隔（秒、分钟、小时）。",
    },
    {
        "function_name": "convert_seconds",
        "description": "输入：时间间隔（秒），     输出：时间间隔对应的分钟、小时。",
    },
    {
        "function_name": "calculate_action_proportion",
        "description": "输入：开始时间、结束时间、动作名称、时间点，     输出：指定时间段内指定动作在指定时间点前发生的比例（%）。",
    }
]
