# 清竞

- 赛事名称：GLM深远海船舶作业大模型应用赛
- 队伍编号：5ed89b27e7b84c47b6196611d6f20753
- 队伍名称：试试又不会怎样

### 一、环境准备

- Python版本：3.11.11
- 安装依赖库：`pip install -r requirements.txt`
- 将数据集放置在`assets/初赛数据`文件夹下

### 二、运行代码

任选 1 种方式运行代码：

#### 2.1 批处理脚本

- 运行`run.bat`，将自动完成数据预处理、问题回答、结果输出等操作

#### 2.2 手动运行

1. 运行`data_process.py`，预处理数据集至`data`文件夹
2. 运行`main.py -p`，依次回答问题，得到结果

#### 三、目录结构

```plaintext
根目录
├── data/               预处理后的数据集
├── prompts/            提示词、外部知识、表格元信息
├── questions/          问题数据
├── results/            运行结果
├── solutions/          运行结果对应的解决方案
├── submits/            最终提交结果
├── tests/              提交测试的中间结果
├── tmp/                临时文件夹
├── tools/              工具代码
|
├── actions.py          设备关键动作对应的表、字段和判断规则
├── api.py              与GLM的API交互，获得问题答案
├── data_process.py     数据预处理与标注
├── functions.py        函数调用的实现
├── logger.py           日志模块
├── main.py             主程序
├── prompts.py          提示词处理
├── solution.py         相关数据Model
├── tools.py            函数调用的定义
├── utils.py            工具函数
```
