"""试卷管理 API：随机组卷（频率/难度比例）、查看增删、按简历异步派生新试卷。"""
import asyncio
import random
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from models import (GenerateFromResumeRequest, PaperFromResumeRequest, PaperGenerateRequest,
                     PaperUpdateRequest, derive_section)
from services import llm
from storage import delete_paper, list_papers, load_paper, load_questions, new_id, now_iso, save_paper

router = APIRouter(prefix="/api/papers", tags=["papers"])

# 按简历生成新试卷的异步任务状态表（内存态，重启即清空）
_GEN_TASKS: dict = {}

FREQ_NAMES = ["高频", "中频", "低频"]
DIFF_NAMES = ["简单", "中等", "困难"]


def _pick_with_difficulty_quota(pool: list, sp, freq_ratio: dict, warnings: list) -> list:
    """先按难度勾选与难度比例分配名额，再在每个难度子池内按频率比例抽题。

    - 未勾选难度：整池按频率比例抽
    - 勾选单一难度：该难度池按频率比例抽
    - 勾选多个难度：按 difficulty_ratio（留空则均分）分配各难度名额；某难度不足自动用其他已勾选难度补足
    """
    count = min(sp.count, len(pool))
    if count <= 0:
        return []
    selected = sp.difficulty or []
    if len(selected) <= 1:
        return _pick_by_frequency(pool, count, freq_ratio, warnings, sp.section)

    weights = (sp.difficulty_ratio.model_dump() if sp.difficulty_ratio else {"简单": 1, "中等": 1, "困难": 1})
    by_diff = {d: [q for q in pool if q.get("difficulty") == d] for d in selected}
    eff = {d: max(0, weights.get(d, 1)) for d in selected}
    total_w = sum(eff.values()) or 1

    quotas = {}
    assigned = 0
    for d in selected[:-1]:
        quotas[d] = min(round(count * eff[d] / total_w), len(by_diff[d]))
        assigned += quotas[d]
    quotas[selected[-1]] = count - assigned

    picked = []
    debts = []
    for d in selected:
        need = quotas.get(d, 0)
        take = min(max(need, 0), len(by_diff[d]))
        if need > take:
            debts.append(need - take)
        picked += _pick_by_frequency(by_diff[d], take, freq_ratio, [], sp.section)
        by_diff[d] = by_diff[d][take:]
    for debt in debts:
        rest = [q for v in by_diff.values() for q in v]
        if debt > len(rest):
            warnings.append(f"{sp.section}部分：题量不足以完全满足难度比例要求，已纳入全部可用题目")
            picked += rest
            break
        picked += _pick_by_frequency(rest, debt, freq_ratio, [], sp.section)
        picked_ids = {q["id"] for q in picked}
        for d in selected:
            by_diff[d] = [q for q in by_diff[d] if q["id"] not in picked_ids]
    return picked[:count]


def _pick_by_frequency(pool: list, count: int, ratio: dict, warnings: list, section: str) -> list:
    """在题池内按 高:中:低 权重分配名额随机抽题；某档不足时自动向其他档补足。"""
    by_freq = {name: [] for name in FREQ_NAMES}
    for q in pool:
        by_freq.setdefault(q.get("frequency") or "高频", []).append(q)

    total_w = sum(ratio.get(name, 0) for name in FREQ_NAMES) or 1
    quotas = {}
    assigned = 0
    for name in FREQ_NAMES[:-1]:
        quotas[name] = min(int(count * ratio.get(name, 0) / total_w), len(by_freq.get(name, [])))
        assigned += quotas[name]
    quotas[FREQ_NAMES[-1]] = count - assigned

    picked = []
    # 先按配额抽取；缺口（配额>库存 或 配额为负）转移到还有库存的档位
    debts = []
    for name in FREQ_NAMES:
        need = quotas.get(name, 0)
        have = by_freq.get(name, [])
        take = min(max(need, 0), len(have))
        if need > take:
            debts.append(need - take)
        picked += random.sample(have, take)
        by_freq[name] = have[take:]
    for debt in debts:
        rest = [q for v in by_freq.values() for q in v]
        if debt > len(rest):
            warnings.append(f"{section}部分：题量不足以满足频率比例要求，已纳入全部可用题目")
            picked += rest
            break
        picked += random.sample(rest, debt)
        for name in FREQ_NAMES:
            by_freq[name] = [q for q in by_freq[name] if q not in picked]
    return picked[:count]


def _resolve_questions(paper: dict) -> dict:
    """把试卷中的 question_ids 解析为题目快照列表（题库中已删除的自动跳过），
    并合入内嵌的简历题（embedded_questions，不依赖题库）。"""
    questions = {q["id"]: q for q in load_questions()}
    missing = []
    sections = []
    for sec in paper.get("sections", []):
        items = []
        for qid in sec.get("question_ids", []):
            if qid in questions:
                items.append(questions[qid])
            else:
                missing.append(qid)
        for emb in sec.get("embedded_questions", []):
            items.append({**emb, "embedded": True})
        sections.append({**sec, "questions": items})
    return {"sections": sections, "missing_ids": missing}


@router.get("")
def get_papers():
    out = []
    for p in list_papers():
        total = sum(len(s.get("question_ids", [])) for s in p.get("sections", []))
        embedded = sum(len(s.get("embedded_questions", [])) for s in p.get("sections", []))
        out.append(
            {
                "id": p["id"],
                "title": p["title"],
                "created_at": p.get("created_at"),
                "question_count": total,
                "resume_question_count": embedded,  # 内嵌简历题数（按简历生成）
            }
        )
    out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"papers": out}


@router.post("/generate")
def generate_paper(payload: PaperGenerateRequest):
    """根据参数从题库随机抽题组卷：每部分可设难度多选+难度比例，并按频率比例抽题。"""
    bank = load_questions()
    ratio = (payload.frequency_ratio.model_dump() if payload.frequency_ratio
             else {"高频": 7, "中频": 2, "低频": 1})
    warnings = []
    sections = []
    used_ids = set()  # 各部分之间不重复抽题
    for sp in payload.sections:
        # 部分（基础/应用）只是试卷的组织结构；候选池 = 全库按难度/类型筛选，去重已抽题目
        pool = [q for q in bank if q["id"] not in used_ids]
        if sp.difficulty:
            pool = [q for q in pool if q.get("difficulty") in sp.difficulty]
        if sp.categories:
            pool = [q for q in pool if q.get("category") in sp.categories]
        if sp.count > 0 and len(pool) < sp.count:
            cond = []
            if sp.difficulty:
                cond.append("难度=" + "、".join(sp.difficulty))
            if sp.categories:
                cond.append("类型=" + "、".join(sp.categories))
            cond_text = f"（{'，'.join(cond)}）" if cond else ""
            warnings.append(
                f"{sp.section}部分：符合条件{cond_text}的题目只有 "
                f"{len(pool)} 道，少于要求的 {sp.count} 道，已全部纳入"
            )
        picked = _pick_with_difficulty_quota(pool, sp, ratio, warnings)
        used_ids.update(q["id"] for q in picked)
        sections.append(
            {
                "section": sp.section,
                "question_ids": [q["id"] for q in picked],
                "llm_gen_count": sp.llm_gen_count,
            }
        )

    title = (payload.title or "").strip()
    if not title:
        title = f"试卷 {now_iso()[:16].replace('T', ' ')}"
    paper = {
        "id": new_id("paper"),
        "title": title,
        "created_at": now_iso(),
        "params": payload.model_dump(mode="json"),
        "sections": sections,
        "warnings": warnings,
    }
    save_paper(paper)
    return paper


@router.get("/{paper_id}")
def get_paper(paper_id: str):
    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    return {**paper, "resolved": _resolve_questions(paper)}


@router.get("/{paper_id}/export_sheet")
def export_paper_sheet(paper_id: str):
    """导出线下评分表 PDF：题目列表 + 空白得分/评语栏（无电脑、无麦克风时面试官手写评分）。"""
    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    from services.pdf_report import build_scoring_sheet_pdf

    try:
        data = build_scoring_sheet_pdf({**paper, "resolved": _resolve_questions(paper)})
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"PDF 生成失败: {e}")
    filename = f"线下评分表_{paper['title']}_{paper_id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename=sheet.pdf; filename*=UTF-8''{quote(filename)}"
    }
    return Response(content=data, media_type="application/pdf", headers=headers)


@router.put("/{paper_id}")
def update_paper(paper_id: str, payload: PaperUpdateRequest):
    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    if payload.title is not None:
        paper["title"] = payload.title.strip() or paper["title"]
    if payload.sections is not None:
        # 校验题目存在即可；部分归属由试卷决定（题目可属任意部分）
        questions = {q["id"]: q for q in load_questions()}
        new_sections = []
        for sec in paper["sections"]:
            key = sec["section"]
            ids = payload.sections.get(key)
            if ids is None:
                new_sections.append(sec)
                continue
            clean = []
            for qid in ids:
                if qid not in questions:
                    raise HTTPException(400, f"题目 {qid} 不存在")
                clean.append(qid)
            new_sections.append({**sec, "question_ids": clean})
        paper["sections"] = new_sections
    if payload.llm_gen_count is not None:
        for sec in paper["sections"]:
            if sec["section"] == "简历":
                sec["llm_gen_count"] = payload.llm_gen_count
    save_paper(paper)
    return {**paper, "resolved": _resolve_questions(paper)}


@router.delete("/{paper_id}")
def remove_paper(paper_id: str):
    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    delete_paper(paper_id)
    return {"ok": True}


def _create_paper_from_questions(paper_id: str, title, questions: list) -> dict:
    """把简历题以内嵌形式固化进派生的新试卷（原卷保留，简历题不入题库）。"""
    from storage import new_id as _new_id, now_iso as _now

    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")

    now = _now()
    embedded = []
    for q in questions:
        item = dict(q) if isinstance(q, dict) else q.model_dump()
        item["category"] = "简历"  # 简历题固定归简历部分
        embedded.append(item)

    new_paper = {
        "id": _new_id("paper"),
        "title": (title or "").strip() or f"{paper['title']}·含简历题",
        "created_at": now,
        "params": paper.get("params"),
        "sections": [],
        "warnings": [],
    }
    resume_found = False
    for sec in paper.get("sections", []):
        new_sec = {**sec, "question_ids": list(sec.get("question_ids", []))}
        if sec.get("section") == "简历":
            resume_found = True
            new_sec["embedded_questions"] = list(sec.get("embedded_questions", [])) + embedded
            new_sec["llm_gen_count"] = 0
        new_paper["sections"].append(new_sec)
    if not resume_found:
        new_paper["sections"].append(
            {"section": "简历", "question_ids": [], "embedded_questions": embedded, "llm_gen_count": 0}
        )
    save_paper(new_paper)
    return new_paper


@router.post("/{paper_id}/from_resume")
def paper_from_resume(paper_id: str, payload: PaperFromResumeRequest):
    """在已有试卷基础上固化简历题，派生一份新试卷（原卷保留）。"""
    new_paper = _create_paper_from_questions(paper_id, payload.title, payload.questions)
    return {**new_paper, "resolved": _resolve_questions(new_paper)}


async def _run_resume_generation(task_id: str, paper_id: str, payload: GenerateFromResumeRequest):
    """后台任务：LLM 按简历生成题目 → 自动创建新试卷。"""
    try:
        questions = await llm.generate_resume_questions(payload.resume_text.strip(), payload.max_count)
        paper2 = _create_paper_from_questions(paper_id, payload.title, questions)
        _GEN_TASKS[task_id] = {"status": "done", "paper_id": paper2["id"], "title": paper2["title"]}
    except Exception as e:  # noqa: BLE001
        _GEN_TASKS[task_id] = {"status": "error", "error": str(e)}


@router.post("/{paper_id}/generate_from_resume")
async def generate_paper_from_resume(paper_id: str, payload: GenerateFromResumeRequest):
    """异步按简历派生新试卷：立即返回任务 id，后台生成并自动建卷，前端轮询任务状态。"""
    paper = load_paper(paper_id)
    if not paper:
        raise HTTPException(404, "试卷不存在")
    from storage import new_id as _new_id

    task_id = _new_id("task")
    _GEN_TASKS[task_id] = {"status": "running"}
    asyncio.get_event_loop().create_task(_run_resume_generation(task_id, paper_id, payload))
    return {"task_id": task_id}


@router.get("/tasks/{task_id}")
def get_generation_task(task_id: str):
    task = _GEN_TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "任务不存在（可能服务已重启），请重新发起")
    return task
