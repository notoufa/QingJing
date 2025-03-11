@echo off
chcp 65001 >nul

IF "%ZHIPUAI_API_KEY%"=="" (
    echo 错误：未找到 ZHIPUAI_API_KEY 环境变量
    pause
    exit /b 1
)

IF "%1"=="" (
    echo 错误：未指定用户
    pause
    exit /b 1
)

set ACCOUNT=%1

IF "%2"=="" (
    echo 错误：未指定镜像标签
    pause
    exit /b 1
)

set TAG=%2

echo 生成数据处理脚本
jupyter nbconvert --to script devlop_home/data_process.ipynb

echo 构建 Docker 镜像
docker build --build-arg ZHIPUAI_API_KEY=%ZHIPUAI_API_KEY% -t hubdocker.aminer.cn/%ACCOUNT%/%TAG% .

echo Docker 镜像构建完成
docker push hubdocker.aminer.cn/%ACCOUNT%/%TAG%