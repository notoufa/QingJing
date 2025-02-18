import copy


class Subtask:
    def __init__(self, task_id, question, parent_ids):
        self.task_id: int = task_id
        self.question: str = question
        self.parent_ids: list[int] = parent_ids
        self.answer: str = None
        self.function_results = None
        self.parent_tasks: list[Subtask] = None

    def __repr__(self):
        return f"Subtask(ID={self.task_id}, Question={self.question}, ParentIDs={self.parent_ids})"

    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data["task_id"],
            question=data["question"],
            parent_ids=data["parent_ids"],
        )

    def to_dict(self):
        """返回一个字典表示，用于数据存储或转换"""
        return {
            "task_id": self.task_id,
            "question": self.question,
            "parent_ids": self.parent_ids,
            "answer": self.answer,
            "function_results": self.function_results,
        }

    def get_parent_tasks_desc(self) -> str:
        if not self.parent_tasks or len(self.parent_tasks) == 0:
            return ""
        return [task.to_dict() for task in self.parent_tasks]

    def clone(self):
        return copy.deepcopy(self)


class Decomposition:
    def __init__(self, contains_time, format_requirement, assumption, subtasks):
        self.contains_time: bool = contains_time
        self.format_requirement: str = format_requirement
        self.assumption: str = assumption
        self.subtasks: list[Subtask] = subtasks

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
            contains_time=data["contains_time"],
            format_requirement=data["format_requirement"],
            assumption=data["assumption"],
            subtasks=subtasks,
        )

    def to_dict(self):
        """返回一个字典表示，用于数据存储或转换"""
        return {
            "contains_time": self.contains_time,
            "format_requirement": self.format_requirement,
            "assumption": self.assumption,
            "subtasks": [subtask.to_dict() for subtask in self.subtasks],
        }


class ProblemSolution:
    def __init__(self, problem_id, question):
        self.id: str = problem_id
        self.question: str = question
        self.decomposition: Decomposition = None
        self.reasoning: str = None
        self.answer: str = None
        self.error_message: str = None
        self.traceback: str = None

    def __repr__(self):
        return f"ProblemSolution(ID={self.id}, Question={self.question})"

    def to_dict(self):
        """返回一个字典表示，用于数据存储或转换"""
        if self.is_error():
            return {
                "id": self.id,
                "question": self.question,
                "error_message": self.error_message,
                "traceback": self.traceback,
            }
        else:
            return {
                "id": self.id,
                "question": self.question,
                "decomposition": self.decomposition.to_dict(),
                "reasoning": self.reasoning,
                "answer": self.answer,
            }

    def to_submit_json(self):
        """返回一个字典表示，用于提交"""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.get_submit_answer(),
        }

    def get_submit_answer(self) -> str:
        return f"{self.reasoning}{self.answer}"

    def to_summary_json(self):
        """返回一个字典表示，用于问题总结"""
        return {
            "id": self.id,
            "question": self.question,
            "decomposition": self.decomposition.to_dict(),
            "answer": self.answer,
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
        self.final_answer: str = None

    def __repr__(self):
        return (
            f"VoteResult(Solutions={self.solutions}, FinalAnswer={self.final_answer})"
        )

    def to_dict(self):
        """返回一个字典表示，用于数据存储或转换"""
        return {
            "id": self.id,
            "question": self.question,
            "vote_times": self.vote_times,
            "solutions": [solution.to_dict() for solution in self.solutions],
            "final_answer": self.final_answer,
        }

    def get_answers(self) -> list[str]:
        return [solution.answer for solution in self.solutions]

    def clone(self):
        return copy.deepcopy(self)

    def to_submit_json(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.final_answer,
        }
