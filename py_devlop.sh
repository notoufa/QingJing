#!/bin/bash

tar -xzf /app/devlop_home/复赛数据.tar.gz -C /app/devlop_data/assets/
python3 /app/devlop_home/data_process.py
python3 /app/devlop_home/main.py $1 $2