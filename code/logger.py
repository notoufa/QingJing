"""日志模块"""

import sys
import datetime
import os
import time

COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "reset": "\033[0m",
}
log_dir = "logs"
date_str=time.strftime("%Y-%m-%d", time.localtime())
log_path = os.path.join(log_dir, "log_"+date_str+".log")

def color_print(color, *args, sep=" ", end="\n", file=sys.stdout):
    """通用彩色打印函数，带时间戳"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(
        f"{timestamp} {COLORS[color]}{sep.join(map(str, args))}{COLORS['reset']}",
        end=end,
        file=file,
    )
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} {sep.join(map(str, args))}{end}")


def info(*args, sep=" ", end="\n"):
    """打印普通信息（蓝色）"""
    color_print("blue", *args, sep=sep, end=end)


def success(*args, sep=" ", end="\n"):
    """打印成功信息（绿色）"""
    color_print("green", *args, sep=sep, end=end)


def warning(*args, sep=" ", end="\n"):
    """打印警告信息（黄色）"""
    color_print("yellow", *args, sep=sep, end=end)


def error(*args, sep=" ", end="\n"):
    """打印错误信息（红色）"""
    color_print("red", *args, sep=sep, end=end, file=sys.stderr)


def debug(*args, sep=" ", end="\n"):
    """打印调试信息（紫色）"""
    color_print("magenta", *args, sep=sep, end=end)


def special(*args, sep=" ", end="\n"):
    """打印特殊信息（青色）"""
    color_print("cyan", *args, sep=sep, end=end)
