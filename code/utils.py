"""工具函数"""


def parse_res(response):
    """
    解析结果
    """
    try:
        res = response.choices[0].message.content
        if "</think>" in res:
            res = res.split("</think>", 1)[1]
        if "```json" in res and "```" in res:
            res = res.split("```json", 1)[1]
            res = res.split("```", 1)[0]
        res = res.strip().replace("\n", "")
        return res
    except Exception:
        return res
