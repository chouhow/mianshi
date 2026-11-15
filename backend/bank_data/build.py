# -*- coding: utf-8 -*-
"""构建正式题库：清空旧题，写入约 100 道高频真题（Python 40 / 数据库 30 / 智能体 30 + 简历通用 2）。

用法：在 backend 目录执行  python bank_data/build.py [--dry]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/
sys.path.insert(0, str(Path(__file__).resolve().parent))          # bank_data/

from part_python import PYTHON  # noqa: E402
from extend_python import PYTHON_EXT  # noqa: E402
from part_db import DB  # noqa: E402
from extend_db import DB_EXT  # noqa: E402
from part_ai import AI  # noqa: E402
from extend_ai import AI_EXT  # noqa: E402
from part_extras import EXPLANATIONS  # noqa: E402
from part_extras2 import EXPLANATIONS2  # noqa: E402
from part_extras3 import EXPLANATIONS3  # noqa: E402
from part_freq import FREQUENCY  # noqa: E402
from extend_freq import FREQUENCY_EXT  # noqa: E402
from extend_exp import EXPLANATIONS_EXT  # noqa: E402
from extend_simple import SIMPLE_MORE  # noqa: E402
from extend_simple2 import SIMPLE_MORE2  # noqa: E402

EXPLANATIONS = {**EXPLANATIONS, **EXPLANATIONS2, **EXPLANATIONS3, **EXPLANATIONS_EXT}


# 难度重标定：原标注偏难的"简单"题升为中等，偏简单的"中等"题降为简单
REGRADE = {
    # 简单 -> 中等（准备型知识，不刻意准备答不好）
    "Transformer 里的 Attention": "中等",
    "什么是模型量化": "中等",
    "什么是慢查询？如何定位慢查询": "中等",
    "round(2.5)": "中等",
    "如何判断一个对象是可迭代的": "中等",
    "如何去除列表中的重复元素": "中等",       # 保序去重是八股细节
    "for 循环的 else": "中等",               # 少有人知
    "dict.get、setdefault": "中等",
    "dict 的 keys()/values()/items()": "中等",  # 视图机制
    "Python 命名中的单下划线": "中等",          # 名称改写是八股
    "json.dumps 和 json.loads": "中等",        # ensure_ascii 是踩坑知识
    "EXISTS 和 IN 子查询": "中等",
    "MySQL 的 datetime 和 timestamp": "中等",
    "什么是评测集": "中等",
    # 中等 -> 困难（准备了也难答好：深层机制）
    "InnoDB 的行锁、间隙锁": "困难",
    "InnoDB 的内存结构 buffer pool": "困难",
    "什么是 KV Cache": "困难",
    "大模型的结构化输出（JSON mode": "困难",   # 约束解码底层
    # 困难 -> 中等（高频刷题，准备了能答）
    "不使用 functools，手写一个 LRU": "中等",
    # 中等 -> 简单（有经验即常识）
    "str 和 bytes 的区别": "简单",
    "什么场景用枚举（Enum）": "简单",
    "dataclass 装饰器": "简单",
    "logging 模块的基本用法": "简单",
}

_ALL_FREQ = {**FREQUENCY, **FREQUENCY_EXT}


def _frequency_for(stem: str) -> str:
    for prefix, freq in _ALL_FREQ.items():
        if stem.startswith(prefix):
            return freq
    return "中频"
from storage import DATA_DIR, load_questions, new_id, now_iso, save_questions  # noqa: E402


def _explanation_for(stem: str, default: str) -> str:
    """优先用补充讲解（按题干前缀匹配），否则用数据文件自带讲解。"""
    for prefix, text in EXPLANATIONS.items():
        if stem.startswith(prefix):
            return text
    return default


def main():
    dry = "--dry" in sys.argv
    # 简历题不入题库：由具体简历在派生试卷或面试时生成
    all_questions = PYTHON + PYTHON_EXT + DB + DB_EXT + AI + AI_EXT + SIMPLE_MORE + SIMPLE_MORE2

    # 校验字段完整性与分布
    for row in all_questions:
        assert len(row) == 7, f"字段数错误: {row[0][:30]}"
        stem, answer, scoring, explanation, category, difficulty, _section = row
        assert stem and answer and scoring, f"必填为空: {stem[:30]}"
        assert difficulty in ("简单", "中等", "困难"), f"难度非法: {stem[:30]}"

    tech = all_questions
    by_cat, by_diff, by_freq = {}, {}, {}
    for stem, *_rest, category, difficulty, _section in all_questions:
        for prefix, new_diff in REGRADE.items():
            if stem.startswith(prefix):
                difficulty = new_diff
        by_cat[category] = by_cat.get(category, 0) + 1
        by_diff[difficulty] = by_diff.get(difficulty, 0) + 1
        freq = _frequency_for(stem)
        by_freq[freq] = by_freq.get(freq, 0) + 1

    print(f"总计 {len(all_questions)} 题（技术题，简历题不入库）")
    print("按类型:", by_cat)
    print("按难度:", by_diff)
    print("按频率:", by_freq)

    if dry:
        print("--dry 模式，未写入")
        return

    old = load_questions()
    if old:
        import json as _json

        backup = DATA_DIR / "questions.backup.json"
        if backup.exists():  # 已有备份则带时间戳另存，避免覆盖历史备份
            backup = DATA_DIR / f"questions.backup.{now_iso()[:16].replace(':', '')}.json"
        backup.write_text(_json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"旧题库 {len(old)} 道已备份到 {backup}")

    now = now_iso()
    questions = []
    for stem, answer, scoring, explanation, category, difficulty, _section in all_questions:
        for prefix, new_diff in REGRADE.items():
            if stem.startswith(prefix):
                difficulty = new_diff
        questions.append({
            "id": new_id("q"),
            "stem": stem,
            "reference_answer": answer,
            "scoring_points": scoring,
            "explanation": _explanation_for(stem, explanation),
            "category": category,
            "difficulty": difficulty,
            "frequency": _frequency_for(stem),
            "created_at": now,
            "updated_at": now,
        })
    save_questions(questions)
    n_exp = sum(1 for q in questions if q["explanation"])
    n_hard_exp = sum(1 for q in questions if q["difficulty"] == "困难" and q["explanation"])
    print(f"已写入新题库 {len(questions)} 道（旧库已清空）")
    n_hard_total = sum(1 for q in questions if q["difficulty"] == "困难")
    print(f"含讲解: {n_exp}/{len(questions)}（其中困难题 {n_hard_exp}/{n_hard_total}）")


if __name__ == "__main__":
    main()
