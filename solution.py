"""
定义投票、问题、子问题、分解、API响应等类
"""

import copy

import logger


class ReasoningAnswer:
    """
    带有推理过程的答案
    """

    def __init__(self):
        self.reasoning: str = None
        self.correct: str = None
        self.answer: str = None
        self.vote: str = None

    def __repr__(self):
        return f"思维过程：{self.reasoning}\n\n纠错步骤：\n{self.correct}\n\n最终答案：\n{self.answer}"

    def to_dict(self):
        return {
            "reasoning": self.reasoning,
            "correct": self.correct,
            "answer": self.answer,
            "vote": self.vote,
        }

    def __json__(self):
        return self.to_dict()

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.reasoning = data.get("reasoning", None)
        instance.correct = data.get("correct", None)
        instance.answer = data.get("answer", None)
        instance.vote = data.get("vote", None)
        return instance

    def clone(self):
        return copy.deepcopy(self)


class FunctionResult:
    """
    函数调用结果
    """

    def __init__(self, function_name, args):
        self.function_name = function_name
        self.args = args
        self.result = None
        self.error = None

    def __repr__(self):
        return (
            f"FunctionResult(FunctionName={self.function_name}, Result={self.result})"
        )

    def to_dict(self):
        return {
            "function_name": self.function_name,
            "args": self.args,
            "result": self.result,
            "error": self.error,
        }

    def clone(self):
        return copy.deepcopy(self)


class ApiResponse:
    """
    单次请求
    """

    def __init__(self, messages, response):
        self.messages = messages
        self.response = response

    def __repr__(self):
        return f"ApiResponse(Messages={self.messages}, Responses={self.response})"

    def to_dict(self):
        """Converts the ApiResponse object into a dictionary for serialization."""
        usage = self.response.usage
        choices = self.response.choices
        return {
            "messages": [
                str(message) if message is not None else None
                for message in self.messages
            ],
            "response": [str(choice) for choice in choices],
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    def clone(self):
        """Creates a deep copy of the ApiResponse instance."""
        return copy.deepcopy(self)


class Subtask:
    def __init__(self, task_id, level, question, parent_ids):
        self.task_id: int = task_id
        self.level: int = level
        self.question: str = question
        self.parent_ids: list[int] = parent_ids
        self.answer: str = None
        self.function_results = None
        self.parent_tasks: list[Subtask] = None
        self.api_response: ApiResponse = None
        self.need_tables: list[str] = None
        self.need_tools: list[str] = None

    def __repr__(self):
        return f"Subtask(ID={self.task_id}, Question={self.question}, ParentIDs={self.parent_ids})"

    def completed(self) -> bool:
        return self.answer is not None

    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data["task_id"],
            level=data["level"],
            question=data["question"],
            parent_ids=data["parent_ids"],
        )

    def to_dict(self, export_api_response: bool = True):
        """返回一个字典表示，用于数据存储或转换"""
        res = {
            "task_id": self.task_id,
            "level": self.level,
            "question": self.question,
            "parent_ids": self.parent_ids,
            "answer": self.answer,
            "function_results": self.function_results,
            "need_tables": self.need_tables,
            "need_tools": self.need_tools,
        }
        if export_api_response:
            res["api_response"] = (
                self.api_response.to_dict() if self.api_response is not None else None
            )
        return res

    def to_simple_dict(self):
        """返回一个字典表示，不包含api_response"""
        return {
            "task_id": self.task_id,
            "level": self.level,
            "question": self.question,
            "parent_ids": self.parent_ids,
            "answer": self.answer,
            "function_results": self.function_results,
        }

    def to_update_dict(self):
        """返回一个字典表示，不包含api_response，用于更新任务分解树"""
        return {
            "task_id": self.task_id,
            "level": self.level,
            "question": self.question,
            "parent_ids": self.parent_ids,
            "answer": self.answer,
        }

    def get_parent_tasks_desc(self) -> str:
        if not self.parent_tasks or len(self.parent_tasks) == 0:
            return ""
        return [task.to_simple_dict() for task in self.parent_tasks]

    def clone(self):
        return copy.deepcopy(self)

    def get_initial_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "level": self.level,
            "question": self.question,
            "parent_ids": self.parent_ids,
        }


class Decomposition:
    def __init__(
        self, contains_time, format_requirement, assumption, subtasks, chain_of_subtasks
    ):
        self.contains_time: bool = contains_time
        self.format_requirement: str = format_requirement
        self.assumption: str = assumption
        self.subtasks: list[Subtask] = subtasks
        self.chain_of_subtasks: str = chain_of_subtasks
        self.need_tools: list[str] = None

    def __repr__(self):
        return (
            f"Decomposition(ContainsTime={self.contains_time}, FormatRequirement={self.format_requirement}, "
            f"Assumption={self.assumption}, Subtasks={self.subtasks})"
        )

    def get_task_by_id(self, task_id) -> Subtask:
        for subtask in self.subtasks:
            if subtask.task_id == task_id:
                return subtask
        return None

    @classmethod
    def from_dict(cls, data):
        subtasks = (
            [Subtask.from_dict(subtask) for subtask in data["subtasks"]]
            if "subtasks" in data
            else []
        )
        return cls(
            contains_time=data.get("contains_time", False),
            format_requirement=data.get("format_requirement", ""),
            assumption=data.get("assumption", ""),
            subtasks=subtasks,
            chain_of_subtasks=data.get("chain_of_subtasks", ""),
        )

    def to_dict(self, export_api_response: bool = True):
        """返回一个字典表示，用于数据存储或转换"""
        return {
            "contains_time": self.contains_time,
            "format_requirement": self.format_requirement,
            "assumption": self.assumption,
            "subtasks": [
                subtask.to_dict(export_api_response) for subtask in self.subtasks
            ],
            "chain_of_subtasks": self.chain_of_subtasks,
            "need_tools": self.need_tools,
        }

    def to_update_dict(self):
        """返回一个字典表示，不包含api_response"""
        return {
            "contains_time": self.contains_time,
            "format_requirement": self.format_requirement,
            "assumption": self.assumption,
            "subtasks": [subtask.to_update_dict() for subtask in self.subtasks],
            "chain_of_subtasks": self.chain_of_subtasks,
        }

    def to_simple_dict(self):
        """返回一个字典表示，不包含api_response"""
        return {
            "contains_time": self.contains_time,
            "format_requirement": self.format_requirement,
            "assumption": self.assumption,
            "subtasks": [subtask.to_simple_dict() for subtask in self.subtasks],
            "chain_of_subtasks": self.chain_of_subtasks,
            "need_tools": self.need_tools,
        }

    def get_initial_dict(self) -> dict:
        return {
            "contains_time": self.contains_time,
            "format_requirement": self.format_requirement,
            "assumption": self.assumption,
            "subtasks": [subtask.get_initial_dict() for subtask in self.subtasks],
            "chain_of_subtasks": self.chain_of_subtasks,
        }

    def draw_table(self):
        """以表格形式打印任务分解"""
        from texttable import Texttable

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["c", "c", "c", "c", "l", "l"])
        table.set_cols_width([5, 5, 10, 10, 68, 68])
        table.add_row(
            [
                "ID",
                "Level",
                "Parent IDs",
                "Completed",
                "Question",
                "Answer",
            ]
        )
        for task in self.subtasks:
            table.add_row(
                [
                    task.task_id,
                    task.level,
                    str(task.parent_ids),
                    task.completed(),
                    task.question,
                    task.answer,
                ]
            )
        logger.special(
            "\n",
            f"假设条件：{self.assumption}\n",
            f"格式要求：{self.format_requirement}",
            "\n",
            table.draw(),
        )


class ProblemSolution:
    def __init__(self, problem_id, question):
        self.id: str = problem_id
        self.question: str = question
        self.decomposition: Decomposition = None
        self.reasoning_answer: ReasoningAnswer = None
        self.error_message: str = None
        self.traceback: str = None
        self.decomposition_api_response: ApiResponse = None
        self.summary_api_response: ApiResponse = None

    def __repr__(self):
        return f"ProblemSolution(ID={self.id}, Question={self.question})"

    def to_dict(self, export_api_response: bool = True):
        """返回一个字典表示，用于数据存储或转换"""
        res = {
            "id": self.id,
            "question": self.question,
            "initial_decomposition": self.decomposition.get_initial_dict(),
            "decomposition": self.decomposition.to_dict(export_api_response),
            "reasoning_answer": self.reasoning_answer.to_dict(),
        }
        if export_api_response:
            res["decomposition_api_response"] = (
                self.decomposition_api_response.to_dict()
                if self.decomposition_api_response
                else None
            )
            res["summary_api_response"] = (
                self.summary_api_response.to_dict()
                if self.summary_api_response
                else None
            )
        return res

    def to_submit_json(self):
        """返回一个字典表示，用于提交"""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.reasoning_answer.answer,
        }

    def to_summary_json(self):
        """返回一个字典表示，用于问题总结"""
        return {
            "id": self.id,
            "question": self.question,
            "decomposition": self.decomposition.to_simple_dict(),
        }

    def is_error(self) -> bool:
        return self.error_message is not None or self.traceback is not None

    def clone(self):
        return copy.deepcopy(self)


class VoteResult:
    def __init__(self, id, question, vote_times):
        self.id: str = id
        self.question: str = question
        self.vote_times: int = vote_times
        self.solutions: list[ProblemSolution] = []
        self.final_reasoning_answer: ReasoningAnswer = None

    def __repr__(self):
        return f"VoteResult(Solutions={self.solutions}, FinalAnswer={self.final_reasoning_answer.answer})"

    def to_dict(self, export_api_response: bool = True):
        """
        返回一个字典表示，用于数据存储或转换

        :param export_api_response: 是否导出api_response
        """
        return {
            "id": self.id,
            "question": self.question,
            "vote_times": self.vote_times,
            "solutions": [
                solution.to_dict(export_api_response) for solution in self.solutions
            ],
            "final_reasoning_answer": self.final_reasoning_answer.to_dict(),
        }

    def get_answers(self) -> list[str]:
        return [solution.final_reasoning_answer.answer for solution in self.solutions]

    def clone(self):
        return copy.deepcopy(self)

    def to_submit_json(self):
        """返回一个字典表示，用于提交"""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.final_reasoning_answer.answer,
        }
