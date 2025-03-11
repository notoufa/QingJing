### base镜像设计, `/app/` 为工作目录，下方默认目录结构

```text

devlop_data: 平台提供的数据目录：只读，包含数据集、模型等
devlop_home: 用户代码目录
devlop_result: 用户结果目录，用户代码生成的结果文件存放在此目录
main.py：默认存在一个，可自己定义此文件
py_devlop.sh：执行入口，默认执行main.py，传入两个参数 `[input_param]` `[result_path]`


```

### py_devlop.sh：执行入口参数的解释如下：
```text
[input_param]：输入参数，用户代码执行时传入的参数, input_param输入的是json信息，包含了 一些平台配置的数据，如赛题的评测问题

[result_path]: 输出的路径，内容为需要评测的答案，输出内容与赛题要求有关

```

### input_param输入示例
```json
{
  "fileData":{
    "questionFilePath":"/app/devlop_data/question.json"
  }
}

```