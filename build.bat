@echo off
chcp 65001 >nul
echo 检查 ZHIPUAI_API_KEY 是否已设置
IF "%ZHIPUAI_API_KEY%"=="" (
    echo 错误：未找到 ZHIPUAI_API_KEY 环境变量
    pause
    exit /b 1
)

@REM echo 生成数据处理脚本
@REM jupyter nbconvert --to script devlop_home/data_process.ipynb

echo 构建 Docker 镜像
docker build --build-arg ZHIPUAI_API_KEY=%ZHIPUAI_API_KEY% -t hubdocker.aminer.cn/013861b58d084a79866ded8df8801da1/qingjing:0.0.1 .

echo Docker 镜像构建完成
pause