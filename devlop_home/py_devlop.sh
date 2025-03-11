#!/bin/bash

export LANG=C.UTF-8

jupyter nbconvert --to script data_process.ipynb
python3 /app/devlop_home/data_process.py >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "数据预处理失败，终止运行"
    exit 1
fi

python3 /app/devlop_home/main.py $1 $2
if [ $? -ne 0 ]; then
    echo "主程序运行失败"
    exit 1
fi