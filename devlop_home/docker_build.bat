@echo off
REM 检查 ZHIPUAI_API_KEY 是否已设置
IF "%ZHIPUAI_API_KEY%"=="" (
    echo 错误：未找到 ZHIPUAI_API_KEY 环境变量
    pause
    exit /b 1
)

REM 构建 Docker 镜像
docker build --build-arg ZHIPUAI_API_KEY=%ZHIPUAI_API_KEY% -t my-image .

REM 提示完成
echo Docker 镜像构建完成
pause