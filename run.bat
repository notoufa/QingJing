@echo off
chcp 65001 >nul
echo 正在运行数据预处理...
jupyter nbconvert --to script data_process.ipynb
python data_process.py
if %errorlevel% neq 0 (
    echo 数据预处理失败, 终止运行
    exit /b %errorlevel%
)

echo 数据预处理完成, 开始运行主程序...
python main.py -p
if %errorlevel% neq 0 (
    echo 主程序运行失败
    exit /b %errorlevel%
)

echo
