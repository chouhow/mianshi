"""LLM 相关独立接口：简历 PDF 解析、根据简历生成个性化面试题。"""
import io

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from models import GenerateResumeQuestionsRequest
from services import llm

router = APIRouter(prefix="/api/llm", tags=["llm"])

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/generate_resume_questions")
async def generate_resume_questions(payload: GenerateResumeQuestionsRequest):
    try:
        questions = await llm.generate_resume_questions(payload.resume_text.strip(), payload.max_count)
        return {"questions": questions}
    except llm.LLMError as e:
        return {"error": str(e)}


@router.post("/parse_resume_pdf")
async def parse_resume_pdf(file: UploadFile = File(...)):
    """上传简历 PDF：提取全文文本 + LLM 提取候选人姓名。"""
    import pypdf

    if not (file.filename or "").lower().endswith(".pdf"):
        return {"error": "只支持 PDF 文件"}
    data = await file.read()
    if len(data) > MAX_PDF_SIZE:
        return {"error": "文件超过 10MB，请精简后重试"}
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001 单页失败不影响整体
                continue
        text = "\n".join(pages).strip()
    except Exception as e:  # noqa: BLE001
        return {"error": f"PDF 解析失败: {e}"}

    if len(text) < 30:
        return {"error": "未能从 PDF 提取到文本（可能是扫描件或图片型简历），请直接粘贴简历文本"}

    name = await llm.extract_candidate_name(text)
    return {
        "candidate_name": name,
        "resume_text": text,
        "chars": len(text),
        "pages": len(reader.pages),
    }
