# 清竞

- 赛事名称：GLM 深远海船舶作业大模型应用赛
- 队伍编号：5ed89b27e7b84c47b6196611d6f20753
- 队伍名称：试试又不会怎样

### 一、环境准备

- Python 版本：3.11.11
- Jupter 版本：
  - IPython : 8.30.0
  - ipykernel : 6.29.5
  - jupyter_client : 8.6.3
  - jupyter_core : 5.7.2
  - traitlets : 5.14.3
- 安装依赖：`pip install -r requirements.txt`
- 数据集：将数据集放置在`devlop_data/assets/复赛数据`文件夹下
- 环境变量：设置 GLM 的 API KEY，环境变量名为`ZHIPUAI_API_KEY`

### 二、运行代码

任选 1 种方式运行代码：

#### 2.1 批处理脚本

- 运行`run.bat`，将自动完成数据预处理、问题回答、结果输出等操作

#### 2.2 手动运行

1. 生成`devlop_home/data_process.py`文件：`jupyter nbconvert --to script devlop_home/data_process.ipynb`
2. 运行`devlop_home/data_process.py`文件，预处理数据集至`data`文件夹：`python devlop_home/data_process.py`
3. 运行`devlop_home/main.py`文件，依次回答问题，得到结果：`python devlop_home/main.py -p`
   - 可以修改相关配置，查看`config.json`文件

#### 三、目录结构

```plaintext
devlop_home目录
├── data/               预处理后的数据集(运行代码后才有)
├── knowledge/          外部知识、表格元信息、函数调用的定义
├── prompts/            提示词
├── questions/          问题数据
├── results/            运行结果(运行代码后才有)
├── solutions/          运行结果对应的解决方案(运行代码后才有)
├── submits/            最终提交结果(运行代码后才有)
├── tools/              工具代码
|
├── actions.py          设备关键动作对应的表、字段和判断规则
├── api.py              与GLM的API交互，获得问题答案
├── data_process.ipynb  数据预处理与标注
├── data_process.py     数据预处理与标注(运行命令行后才有)
├── functions.py        函数调用的实现
├── logger.py           日志模块
├── main.py             主程序
├── prompts.py          提示词处理
├── solution.py         相关数据Model
├── tools.py            函数调用的定义
├── utils.py            工具函数
├── run.bat             运行脚本
```
