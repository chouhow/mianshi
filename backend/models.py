"""Pydantic 请求/数据模型。"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Difficulty = Literal["简单", "中等", "困难"]
Section = Literal["基础", "应用", "简历"]
Frequency = Literal["高频", "中频", "低频"]
ScoringMode = Literal["points", "holistic"]  # 按点给分 / 综合评价
ItemState = Literal["pending", "answered", "unknown", "unasked"]


def default_scoring_mode(category: str) -> str:
    """评分方式默认值：简历类（开放型）综合评价，其余按点给分。"""
    return "holistic" if category == "简历" else "points"


def derive_section(category: str, difficulty: str) -> str:
    """所属部分由题目属性派生：简历类 → 简历；困难 → 应用；其余 → 基础。"""
    if category == "简历":
        return "简历"
    return "应用" if difficulty == "困难" else "基础"


WRITTEN_CATEGORY = "算法笔试"


class WrittenResultIn(BaseModel):
    passed: bool


class QuestionIn(BaseModel):
    stem: str = Field(min_length=1)
    reference_answer: str = Field(min_length=1)
    # 评分标准（采分点）：每行一个点及分值，合计 5 分（综合评价题可作参考要点）
    scoring_points: Optional[str] = ""
    explanation: Optional[str] = ""
    category: str = Field(min_length=1)
    difficulty: Difficulty = "中等"
    # 出现频率：组卷时可控制高/中/低频比例
    frequency: Frequency = "高频"
    # 评分方式：points 按点给分（答案确定）/ holistic 综合评价（开放型）；留空按类型派生（简历→综合）
    scoring_mode: Optional[ScoringMode] = None

    @field_validator("stem", "reference_answer", "category")
    @classmethod
    def _strip_not_empty(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("字段不能为空")
        return v

    @field_validator("explanation", "scoring_points")
    @classmethod
    def _strip_optional(cls, v):
        return (v or "").strip()


class Question(QuestionIn):
    id: str
    created_at: str
    updated_at: str


# ---------- 试卷 ----------

class DifficultyRatio(BaseModel):
    """组卷时简单/中等/困难题的抽题权重（比例），仅对已勾选的难度生效。"""
    简单: int = Field(default=1, ge=0, le=10)
    中等: int = Field(default=1, ge=0, le=10)
    困难: int = Field(default=1, ge=0, le=10)


class SectionParam(BaseModel):
    """组卷参数：某一部分抽几题、难度与类型过滤（均支持多选，空=不限）。"""
    section: Section
    count: int = Field(default=6, ge=0, le=50)
    difficulty: List[Literal["简单", "中等", "困难"]] = []  # 空 = 任意难度
    # 难度抽题权重（勾选多个难度时按比例分配名额；留空则均分）
    difficulty_ratio: Optional[DifficultyRatio] = None
    categories: List[str] = []  # 空 = 任意类型
    llm_gen_count: int = Field(default=0, ge=0, le=10)  # 仅简历部分：面试开始时按简历生成


class FrequencyRatio(BaseModel):
    """组卷时高/中/低频题的抽题权重（比例）。"""
    高频: int = Field(default=7, ge=0, le=10)
    中频: int = Field(default=2, ge=0, le=10)
    低频: int = Field(default=1, ge=0, le=10)


class PaperGenerateRequest(BaseModel):
    title: Optional[str] = None
    sections: List[SectionParam]
    frequency_ratio: Optional[FrequencyRatio] = None


class ManualPaperRequest(BaseModel):
    title: str = Field(min_length=1)


class PaperUpdateRequest(BaseModel):
    title: Optional[str] = None
    # {section: [question_id, ...]}
    sections: Optional[dict] = None
    llm_gen_count: Optional[int] = None


class GenerateFromResumeRequest(BaseModel):
    """异步按简历生成独立简历试卷（仅含简历题，不基于其他试卷）。"""
    resume_text: str = Field(min_length=10)
    max_count: int = Field(default=10, ge=3, le=10)  # 题量上限，模型在 3~上限间自行决定
    title: Optional[str] = None


# ---------- 面试 ----------

class CreateInterviewRequest(BaseModel):
    # 多卷面试：随机卷 + 简历卷等可同时勾选；paper_id 为单卷兼容写法
    paper_ids: List[str] = []
    paper_id: Optional[str] = None
    candidate_name: str = Field(min_length=1)
    resume_text: Optional[str] = ""
    # 简历部分的 LLM 生成题（前端可预览编辑后传入）
    extra_questions: List[QuestionIn] = []

    def effective_paper_ids(self) -> list:
        ids = [p for p in (self.paper_ids or []) if p]
        if not ids and self.paper_id:
            ids = [self.paper_id]
        return ids

    @field_validator("candidate_name")
    @classmethod
    def _name_not_empty(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("候选人姓名不能为空")
        return v


class ItemUpdateRequest(BaseModel):
    state: Optional[ItemState] = None
    answer_text: Optional[str] = None


# ---------- LLM ----------

class GenerateResumeQuestionsRequest(BaseModel):
    resume_text: str = Field(min_length=10)
    max_count: int = Field(default=10, ge=3, le=10)  # 题量上限，模型在 3~上限间自行决定
