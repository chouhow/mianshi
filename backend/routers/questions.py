"""题库管理 API。"""
from fastapi import APIRouter, HTTPException

from models import QuestionIn, default_scoring_mode, derive_section
from storage import load_questions, new_id, now_iso, save_questions

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("")
def list_questions(category: str = "", difficulty: str = "", section: str = "",
                   frequency: str = "", q: str = "", favorite: bool = False):
    """section 参数按派生规则过滤（简历类→简历；困难→应用；其余→基础）。"""
    questions = load_questions()
    kw = q.strip().lower()
    out = []
    for item in questions:
        if favorite and not item.get("favorite"):
            continue
        if category and item.get("category") != category:
            continue
        if difficulty and item.get("difficulty") != difficulty:
            continue
        if frequency and item.get("frequency") != frequency:
            continue
        if section and derive_section(item.get("category", ""), item.get("difficulty", "")) != section:
            continue
        if kw and kw not in (item.get("stem", "").lower() + item.get("reference_answer", "").lower()):
            continue
        # 附带派生部分，便于前端展示
        out.append({**item, "derived_section": derive_section(item.get("category", ""), item.get("difficulty", ""))})
    out.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"questions": out}


@router.get("/categories")
def list_categories():
    return {"categories": sorted({q.get("category", "") for q in load_questions() if q.get("category")})}


@router.post("")
def create_question(payload: QuestionIn):
    questions = load_questions()
    question = payload.model_dump()
    question["scoring_mode"] = question.get("scoring_mode") or default_scoring_mode(question["category"])
    question["id"] = new_id("q")
    question["created_at"] = now_iso()
    question["updated_at"] = now_iso()
    questions.append(question)
    save_questions(questions)
    return question


@router.put("/{question_id}")
def update_question(question_id: str, payload: QuestionIn):
    questions = load_questions()
    for i, item in enumerate(questions):
        if item["id"] == question_id:
            updated = payload.model_dump()
            updated["scoring_mode"] = updated.get("scoring_mode") or default_scoring_mode(updated["category"])
            updated["favorite"] = item.get("favorite", False)
            updated["id"] = question_id
            updated["created_at"] = item.get("created_at")
            updated["updated_at"] = now_iso()
            questions[i] = updated
            save_questions(questions)
            return updated
    raise HTTPException(404, "题目不存在")


@router.put("/{question_id}/favorite")
def set_favorite(question_id: str, favorite: bool):
    questions = load_questions()
    for question in questions:
        if question["id"] == question_id:
            question["favorite"] = favorite
            save_questions(questions)
            return question
    raise HTTPException(404, "题目不存在")


@router.delete("/{question_id}")
def delete_question(question_id: str):
    questions = load_questions()
    remaining = [q for q in questions if q["id"] != question_id]
    if len(remaining) == len(questions):
        raise HTTPException(404, "题目不存在")
    save_questions(remaining)
    return {"ok": True}
