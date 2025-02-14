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
                        "description": "需要筛选的状态。如果未提供，则不筛选状态。支持以下值：A架开机、ON DP、征服者起吊、征服者入水、缆绳解除、A架摆回、小艇落座、A架关机、OFF DP、折臂吊车开机、A架摆出、小艇检查完毕、小艇入水、缆绳挂妥、征服者出水、折臂吊车关机、征服者落座",
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
            "name": "get_running_time_by_time_range",
            "description": "查询指定时间段内设备的运行时长或实际运行时长。返回三种格式（秒，分，时）的运行时长。",
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
                    "is_actual": {
                        "type": "boolean",
                        "description": "是否查询实际运行时长，如果为 True，则查询实际运行时长，否则查询运行时长。",
                    },
                    "device_name": {
                        "type": "string",
                        "description": "设备名称，支持以下值：'折臂吊车'、'A架' 和 'DP'。",
                        "enum": ["折臂吊车", "A架", "DP"],
                    },
                },
                "required": ["start_time", "end_time", "is_actual", "device_name"],
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
            "name": "calculate_math_operations",
            "description": "进行数学运算，包括加法、减法、乘法、除法、求和和求平均值。",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "指定运算类型，支持以下值： '加法'、'减法'、'乘法'、'除法'、'求和'、'求平均值'。",
                        "enum": [
                            "加法",
                            "减法",
                            "乘法",
                            "除法",
                            "求和",
                            "求平均值",
                        ],
                    },
                    "operands": {
                        "type": "array",
                        "description": "参与运算的数值列表，所有元素必须为数字。",
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
            "description": "计算两个时间点之间的时间间隔，支持秒、分钟、小时、天的计算。返回值为按秒、分钟、小时、天计算的时间间隔。",
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
]
