"""评分规则计算（纯函数，便于测试）。

加权两段式记分（Top-K 主导 + 剩余题辅助 + 答题数量折扣）：
- 每题满分 5 分，"不会"计 0 分，"未问"不计入；计分题按得分降序排列
- 计分题数 n ≥ 阈值 K：得分最高的 K 题折算平均分占 80%，剩余题折算平均分占 20%，加权求和
  （表现好的题主导分数，个别失手/不会只通过两成权重轻微拉低，多答的差题不会大幅惩罚）
- 计分题数 n < K：无剩余题，按 Top 平均折算后乘数量折扣 n/K
  （少答按比例少得分，多答且答好才拿满分）
- 全部答对即满分；完全不会自然低分
- 基础部分 40 分（K=8）、应用部分 30 分（K=6）、简历题 15 分（K=3）
- 简历熟悉度 15 分：LLM 整体评价（0-15）
- 简历部分 = 简历题 + 熟悉度（上限 30）；总分 = 三部分之和（上限 100）
"""

BASIC_THRESHOLD = 8   # 40 / 5
APPLIED_THRESHOLD = 6  # 30 / 5
RESUME_Q_THRESHOLD = 3  # 15 / 5

BASIC_MAX = 40.0
APPLIED_MAX = 30.0
RESUME_Q_MAX = 15.0
RESUME_FAMILIAR_MAX = 15.0
QUESTION_MAX = 5.0
TOP_WEIGHT = 0.8  # 最好 K 题的权重；剩余题占 1 - TOP_WEIGHT = 0.2


def part_score(item_scores: list, threshold: int) -> float:
    """加权两段式记分：Top-K 占 80% + 剩余题占 20%。

    - n ≥ K：0.8 × (Top-K 平均分折算) + 0.2 × (剩余题平均分折算)
    - n < K：直接求和（每题满分 5 分，答几题算几分，不足满分的差距就是少答的代价）
    """
    n = len(item_scores)
    if n == 0:
        return 0.0
    full = threshold * QUESTION_MAX
    srt = sorted(item_scores, reverse=True)
    top = srt[:threshold]
    rest = srt[threshold:]
    if rest:
        top_avg = sum(top) / len(top)
        rest_avg = sum(rest) / len(rest)
        base = (TOP_WEIGHT * top_avg + (1 - TOP_WEIGHT) * rest_avg) / QUESTION_MAX * full
    else:
        base = sum(item_scores)  # 答题数不足 K：直接求和
    return round(min(base, full), 1)


def _counted_scores(items: list, section: str) -> list:
    """某部分计分题目（已回答 + 不会）的得分列表，不会 = 0。"""
    return [
        float(it.get("score") or 0.0)
        for it in items
        if it.get("section") == section and it.get("state") in ("answered", "unknown")
    ]


def compute_scores(items: list, resume_familiar_score: float = 0.0) -> dict:
    basic = min(part_score(_counted_scores(items, "基础"), BASIC_THRESHOLD), BASIC_MAX)
    applied = min(part_score(_counted_scores(items, "应用"), APPLIED_THRESHOLD), APPLIED_MAX)
    resume_q = min(part_score(_counted_scores(items, "简历"), RESUME_Q_THRESHOLD), RESUME_Q_MAX)
    familiar = round(min(float(resume_familiar_score or 0.0), RESUME_FAMILIAR_MAX), 1)
    resume = round(min(resume_q + familiar, 30.0), 1)
    total = round(min(basic + applied + resume, 100.0), 1)
    return {
        "basic": basic,
        "applied": applied,
        "resume_q": resume_q,
        "resume_familiar": familiar,
        "resume": resume,
        "total": total,
    }


def counted_question_stats(items: list, section: str) -> dict:
    """某部分计分题数统计（用于报告展示）。"""
    answered = sum(1 for it in items if it.get("section") == section and it.get("state") == "answered")
    unknown = sum(1 for it in items if it.get("section") == section and it.get("state") == "unknown")
    unasked = sum(1 for it in items if it.get("section") == section and it.get("state") in ("pending", "unasked"))
    return {"answered": answered, "unknown": unknown, "unasked": unasked}
