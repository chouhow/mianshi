"""面试流程 API：创建（题目快照）、作答/不会标记、结束、LLM 评分、报告导出。"""
import asyncio
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response

from config import get_config
from models import CreateInterviewRequest, ItemUpdateRequest, default_scoring_mode, derive_section
from services import llm
from services.scoring import compute_scores, counted_question_stats
from storage import (audio_dir, delete_interview, list_interviews, load_interview,
                     load_paper, load_questions, new_id, now_iso, save_interview)

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

SECTION_ORDER = {"基础": 0, "应用": 1, "简历": 2}


def _make_item(question: dict, order: int, source: str, section: str | None = None) -> dict:
    """把题库题目（或 LLM 生成题）快照为面试条目，后续题库改动不影响历史记录。
    所属部分优先取试卷中该题所属部分；否则按 类型/难度 派生（简历类→简历；困难→应用；其余→基础）。"""
    return {
        "id": new_id("item"),
        "order": order,
        "source": source,
        "question_id": question.get("id"),
        "stem": question["stem"],
        "reference_answer": question["reference_answer"],
        "scoring_points": question.get("scoring_points") or "",
        "explanation": question.get("explanation") or "",
        "category": question.get("category") or "简历",
        "difficulty": question.get("difficulty") or "中等",
        "frequency": question.get("frequency") or "高频",
        "scoring_mode": question.get("scoring_mode") or default_scoring_mode(question.get("category") or "简历"),
        "section": section or derive_section(question.get("category") or "简历", question.get("difficulty") or "中等"),
        "state": "pending",
        "answer_text": "",
        "audio_file": None,
        "score": None,
        "comment": None,
    }


@router.post("")
def create_interview(payload: CreateInterviewRequest):
    paper_ids = payload.effective_paper_ids()
    if not paper_ids:
        raise HTTPException(422, "请至少选择一份试卷")
    papers = []
    for pid in paper_ids:
        paper = load_paper(pid)
        if not paper:
            raise HTTPException(404, f"试卷不存在：{pid}")
        papers.append(paper)
    bank = {q["id"]: q for q in load_questions()}

    # 合并多卷题目（如随机卷 + 简历卷），按 基础→应用→简历 稳定排序（保留卷内顺序）
    collected = []
    for paper in papers:
        for sec in sorted(paper.get("sections", []), key=lambda s: SECTION_ORDER.get(s["section"], 9)):
            for qid in sec.get("question_ids", []):
                if qid in bank:
                    collected.append((sec["section"], bank[qid], "bank"))
            # 试卷内嵌的简历题（简历卷生成时固化，不依赖题库）
            for emb in sec.get("embedded_questions", []):
                collected.append(("简历", emb, "resume"))
    for extra in payload.extra_questions:
        collected.append(("简历", extra.model_dump(), "llm"))
    collected.sort(key=lambda row: SECTION_ORDER.get(row[0], 9))

    items = []
    for order, (section, q, source) in enumerate(collected):
        items.append(_make_item(q, order, source, section=section))

    if not items:
        raise HTTPException(400, "所选试卷中没有可用题目（题目可能已被删除），无法开始面试")

    interview = {
        "id": new_id("iv"),
        "paper_id": papers[0]["id"],
        "paper_ids": [p["id"] for p in papers],
        "paper_title": " + ".join(p["title"] for p in papers),
        "candidate_name": payload.candidate_name.strip(),
        "resume_text": (payload.resume_text or "").strip(),
        "status": "ongoing",
        "judge_mode": get_config().get("judge_mode", "per_question"),
        "items": items,
        "scores": None,
        "resume_comment": None,
        "score_error": None,
        "created_at": now_iso(),
        "finished_at": None,
        "scored_at": None,
    }
    audio_dir(interview["id"])  # 预建录音目录
    save_interview(interview)
    return interview


def _summary(iv: dict) -> dict:
    counted = [it for it in iv.get("items", []) if it.get("state") in ("answered", "unknown")]
    return {
        "id": iv["id"],
        "candidate_name": iv.get("candidate_name"),
        "paper_title": iv.get("paper_title"),
        "status": iv.get("status"),
        "created_at": iv.get("created_at"),
        "finished_at": iv.get("finished_at"),
        "scored_at": iv.get("scored_at"),
        "total": (iv.get("scores") or {}).get("total"),
        "answered": sum(1 for it in counted if it["state"] == "answered"),
        "unknown": sum(1 for it in counted if it["state"] == "unknown"),
        "total_items": len(iv.get("items", [])),
    }


@router.get("")
def get_interviews():
    out = [_summary(iv) for iv in list_interviews()]
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"interviews": out}


@router.get("/{interview_id}")
def get_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    return interview


@router.put("/{interview_id}/items/{item_id}")
def update_item(interview_id: str, item_id: str, payload: ItemUpdateRequest):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    if interview.get("status") not in ("ongoing",):
        raise HTTPException(400, "面试已结束，不能再修改作答")
    for item in interview["items"]:
        if item["id"] != item_id:
            continue
        if payload.answer_text is not None:
            item["answer_text"] = payload.answer_text
        if payload.state is not None:
            if payload.state == "answered" and not (item.get("answer_text") or "").strip():
                raise HTTPException(400, "回答内容为空，不能保存为已回答")
            item["state"] = payload.state
            if payload.state != "answered":
                item["score"] = None if payload.state == "pending" else item.get("score")
        save_interview(interview)
        return item
    raise HTTPException(404, "题目条目不存在")


@router.post("/{interview_id}/finish")
def finish_interview(interview_id: str):
    """结束面试：剩余未问（pending）的题目标记为 unasked，不计分。"""
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    for item in interview["items"]:
        if item["state"] == "pending":
            item["state"] = "unasked"
    interview["status"] = "finished"
    interview["finished_at"] = now_iso()
    save_interview(interview)
    return interview


async def _run_scoring(interview_id: str):
    """后台评分任务：逐题或整卷 LLM 评判 + 简历熟悉度 + 规则汇总。逐题模式下增量保存以供进度展示。"""
    interview = load_interview(interview_id)
    if not interview:
        return
    try:
        items = interview["items"]
        # 面试者表示"不会"的题直接 0 分，不调 LLM
        for it in items:
            if it["state"] == "unknown":
                it["score"] = 0.0
                it["comment"] = "面试者表示不会，计 0 分。"
        answered = [it for it in items if it["state"] == "answered"]
        # 正常情况下 score 前已 finish；若直接评分，未问的题按不计分处理
        for it in items:
            if it["state"] == "pending":
                it["state"] = "unasked"

        if interview.get("judge_mode") == "whole_paper" and answered:
            results = await llm.judge_whole_paper(answered)
            for it, r in zip(answered, results):
                it["score"] = r["score"]
                it["comment"] = r["comment"]
            save_interview(interview)
        else:
            for it in answered:
                r = await llm.judge_question(it)
                it["score"] = r["score"]
                it["comment"] = r["comment"]
                save_interview(interview)  # 增量保存，前端轮询可见进度

        familiar = 0.0
        resume_items = [it for it in items if it["section"] == "简历" and it["state"] in ("answered", "unknown")]
        if interview.get("resume_text") or resume_items:
            r = await llm.judge_resume_familiarity(interview.get("resume_text", ""), resume_items)
            familiar = r["score"]
            interview["resume_comment"] = r["comment"]

        interview["scores"] = compute_scores(items, familiar)
        interview["overall_comment"] = await llm.generate_overall_comment(items, interview["scores"])
        interview["scored_at"] = now_iso()
        interview["status"] = "scored"
        interview["score_error"] = None
        save_interview(interview)
    except Exception as e:  # noqa: BLE001
        interview["status"] = "score_error"
        interview["score_error"] = str(e)
        save_interview(interview)


@router.post("/{interview_id}/score")
async def score_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    if interview.get("status") == "scoring":
        raise HTTPException(400, "正在评分中")
    if not any(it["state"] in ("answered", "unknown") for it in interview["items"]):
        raise HTTPException(400, "没有已回答或标记不会的题目，无法评分")
    # 未结束时直接评分，先把 pending 归为 unasked
    for it in interview["items"]:
        if it["state"] == "pending":
            it["state"] = "unasked"
    interview["status"] = "scoring"
    interview["judge_mode"] = get_config().get("judge_mode", "per_question")
    interview["score_error"] = None
    save_interview(interview)
    asyncio.get_event_loop().create_task(_run_scoring(interview_id))
    return {"ok": True, "status": "scoring"}


@router.get("/{interview_id}/export")
def export_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    return {"markdown": _build_markdown(interview), "filename": f"面试报告_{interview['candidate_name']}_{interview_id}.md"}


@router.get("/{interview_id}/export_pdf")
def export_interview_pdf(interview_id: str):
    """导出 PDF 报告：姓名/时间、逐题（题干/回答/得分/评语）、三部分成绩与总分、整体评价。"""
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    from services.pdf_report import build_report_pdf

    try:
        data = build_report_pdf(interview)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"PDF 生成失败: {e}")
    filename = f"面试报告_{interview['candidate_name']}_{interview_id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename=report.pdf; filename*=UTF-8''{quote(filename)}"
    }
    return Response(content=data, media_type="application/pdf", headers=headers)


def _build_markdown(iv: dict) -> str:
    scores = iv.get("scores") or {}
    lines = [
        f"# 面试报告 - {iv.get('candidate_name', '')}",
        "",
        f"- 试卷：{iv.get('paper_title', '')}",
        f"- 面试时间：{iv.get('created_at', '')}",
        f"- 评分模式：{'整卷评判' if iv.get('judge_mode') == 'whole_paper' else '逐题评判'}",
        "",
        "## 总分",
        "",
        f"**{scores.get('total', '-')} / 100**",
        "",
        "| 部分 | 得分 | 满分 |",
        "| --- | --- | --- |",
        f"| 基础 | {scores.get('basic', 0)} | 40 |",
        f"| 应用 | {scores.get('applied', 0)} | 30 |",
        f"| 简历（题目） | {scores.get('resume_q', 0)} | 15 |",
        f"| 简历（熟悉度） | {scores.get('resume_familiar', 0)} | 15 |",
        f"| 简历（小计） | {scores.get('resume', 0)} | 30 |",
        "",
    ]
    for section in ("基础", "应用", "简历"):
        items = [it for it in iv.get("items", []) if it.get("section") == section]
        if not items:
            continue
        stats = counted_question_stats(iv.get("items", []), section)
        lines += [
            f"## {section}部分",
            "",
            f"已答 {stats['answered']} 题、不会 {stats['unknown']} 题、未问 {stats['unasked']} 题",
            "",
        ]
        for i, it in enumerate(items, 1):
            state_text = {"answered": "已回答", "unknown": "不会", "unasked": "未问", "pending": "未问"}[it["state"]]
            score_text = "-" if it.get("score") is None else f"{it['score']} / 5"
            lines += [f"### {i}. [{state_text}] {it['stem']}", ""]
            if it["state"] in ("answered", "unknown"):
                lines += [
                    f"- 考生回答：{(it.get('answer_text') or '（空）')[:500]}",
                    f"- 得分：{score_text}",
                    f"- 评语：{it.get('comment') or '-'}",
                    "",
                ]
        lines.append("")
    if iv.get("resume_comment"):
        lines += ["## 简历熟悉度评价", "", iv["resume_comment"], ""]
    return "\n".join(lines)


@router.delete("/{interview_id}")
def remove_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    delete_interview(interview_id)
    return {"ok": True}
