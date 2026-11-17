"""面试流程 API：创建（题目快照）、作答/不会标记、结束、报告导出。"""

from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response
from models import CreateInterviewRequest, ItemUpdateRequest, WrittenResultIn, WRITTEN_CATEGORY, derive_section
from services import llm
from services.resume_questions import resume_key, sample_questions
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
        "question_id": question.get("bank_question_id") or question.get("id"),
        "stem": question["stem"],
        "reference_answer": question["reference_answer"],
        "explanation": question.get("explanation") or "",
        "category": question.get("category") or "简历",
        "difficulty": question.get("difficulty") or "中等",
        "frequency": question.get("frequency") or "高频",
        "section": section or derive_section(question.get("category") or "简历", question.get("difficulty") or "中等"),
        "state": "pending",
        "answer_text": "",
        "audio_file": None,
    }


@router.post("")
async def create_interview(payload: CreateInterviewRequest):
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
    # 同一技术题同时出现在所选试卷和简历卷时，保留简历卷快照。
    resume_ids = {q.get("bank_question_id") for _, q, _ in collected if q.get("bank_question_id")}
    collected = [row for row in collected if row[2] != "bank" or row[1]["id"] not in resume_ids]
    text = (payload.resume_text or "").strip()
    extras = [q.model_dump() for q in payload.extra_questions]
    has_resume = text and any(p.get("resume_key") == resume_key(text) for p in papers)
    if text and not has_resume:
        if not extras:
            try:
                extras = (await llm.generate_resume_questions(text, 3))[:3]
            except llm.LLMError as exc:
                raise HTTPException(502, f"简历题生成失败：{exc}") from exc
        stems = {q["stem"] for _, q, _ in collected} | {q["stem"] for q in extras}
        for question in sample_questions(text, bank.values(), stems):
            collected.append(("简历", question, "resume"))
    for extra in extras:
        collected.append(("简历", {**extra, "category": "简历"}, "llm"))
    collected = [row for row in collected if row[1].get("category") != WRITTEN_CATEGORY]
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
        "items": items,
        "created_at": now_iso(),
        "finished_at": None,
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


@router.post("/{interview_id}/items/{question_id}")
async def append_question(interview_id: str, question_id: str):
    interview = get_interview(interview_id)
    if interview["status"] != "ongoing":
        raise HTTPException(400, "面试已结束")
    if any(item.get("question_id") == question_id for item in interview["items"]):
        return interview
    question = next((q for q in load_questions() if q["id"] == question_id), None)
    if not question:
        raise HTTPException(404, "题目不存在")
    if question.get("category") == WRITTEN_CATEGORY:
        raise HTTPException(400, "算法笔试题仅用于登记机测结果")
    interview["items"].append(_make_item(question, len(interview["items"]), "bank"))
    save_interview(interview)
    return interview


@router.put("/{interview_id}/written/{question_id}")
async def record_written_result(interview_id: str, question_id: str, payload: WrittenResultIn):
    interview = get_interview(interview_id)
    results = interview.setdefault("written_results", {})
    if question_id not in results:
        question = next((q for q in load_questions() if q["id"] == question_id
                         and q.get("category") == WRITTEN_CATEGORY), None)
        if not question:
            raise HTTPException(404, "算法笔试题不存在")
        results[question_id] = {"title": question["stem"].splitlines()[0]}
    results[question_id]["passed"] = payload.passed
    save_interview(interview)
    return interview


@router.delete("/{interview_id}/written/{question_id}")
async def remove_written_result(interview_id: str, question_id: str):
    interview = get_interview(interview_id)
    interview.get("written_results", {}).pop(question_id, None)
    save_interview(interview)
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


@router.get("/{interview_id}/export")
def export_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    return {"markdown": _build_markdown(interview), "filename": f"面试报告_{interview['candidate_name']}_{interview_id}.md"}


@router.get("/{interview_id}/export_pdf")
def export_interview_pdf(interview_id: str):
    """导出 PDF 报告：姓名/时间、逐题题干、难度和类型。"""
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
    lines = [f"# 面试报告 · {iv['candidate_name']}", "", f"试卷：{iv['paper_title']}", f"面试时间：{iv['created_at']}", ""]
    for index, item in enumerate(iv["items"], 1):
        lines.extend([f"{index}. {item['stem']}", f"   难度：{item.get('difficulty') or '—'} · 类型：{item.get('category') or '—'}", ""])
    lines.extend(["## 算法笔试", ""])
    for result in iv.get("written_results", {}).values():
        lines.append(f"- {result['title']}　{'通过' if result['passed'] else '未通过'}")
    if not iv.get("written_results"):
        lines.append("未登记")
    return "\n".join(lines)


@router.delete("/{interview_id}")
def remove_interview(interview_id: str):
    interview = load_interview(interview_id)
    if not interview:
        raise HTTPException(404, "面试记录不存在")
    delete_interview(interview_id)
    return {"ok": True}
