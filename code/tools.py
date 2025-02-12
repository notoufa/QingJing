tools = [
    {
        "type": "function",
        "function": {
            "name": "get_data_by_time_range",
            "description": "根据数据表名、开始时间、结束时间、列名获取指定时间范围内的相关数据。返回值为包含指定列名和对应值的字典。",
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
                },
                "required": ["table_name", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_actions_by_time_range",
            "description": "根据开始时间和结束时间，查询什么设备在进行什么动作。返回正在进行的设备动作列表。",
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
            "description": "通过参数的中文名称查询设备参数信息。返回包含参数信息的字典。",
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
            "description": "计算指定时间段内指定设备的总能耗。返回值为总能耗（kWh，float 类型）。",
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
                        "description": "设备名称，支持以下值：'折臂吊车'、'一号门架'、'二号门架'、'绞车'、'甲板机械设备'。",
                        "enum": ["折臂吊车", "一号门架", "二号门架", "绞车", "甲板机械设备"],
                    },
                },
                "required": ["start_time", "end_time", "device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_startup_time_by_time_range",
            "description": "计算指定时间段内设备的开机时长，并返回三种格式的开机时长。设备名称支持 '折臂吊车'、'A架' 和 'DP'。",
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
                    "shebeiname": {
                        "type": "string",
                        "enum": ["折臂吊车", "A架", "DP"],
                        "description": "设备名称，支持 '折臂吊车'、'A架' 和 'DP'，默认为 '折臂吊车'。",
                        "default": "折臂吊车",
                    },
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_time_by_time_range",
            "description": "计算指定时间段内设备的运行时长，并返回三种格式的运行时长。设备名称支持 'A架'。",
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
                        "enum": ["A架"],
                        "description": "设备名称，支持 'A架'，默认为 'A架'。",
                        "default": "A架",
                    },
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
]
