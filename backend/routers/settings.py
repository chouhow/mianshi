"""设置 API：配置读写、方舟/ASR 连通性测试、简历题生成。"""
from fastapi import APIRouter
from pydantic import BaseModel

from config import get_config, save_config
from services import llm
from services.asr import test_asr_connection

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    # 允许整体提交，字段与 DEFAULT_CONFIG 对齐；忽略未知字段
    python_cmd: str | None = None
    asr: dict | None = None
    ark: dict | None = None
    judge_mode: str | None = None
    llm_mock: bool | None = None


@router.get("")
def read_settings():
    return get_config()


@router.put("")
def update_settings(payload: SettingsUpdate):
    partial = {k: v for k, v in payload.model_dump().items() if v is not None}
    if partial.get("judge_mode") not in (None, "per_question", "whole_paper"):
        return {"error": "judge_mode 必须是 per_question 或 whole_paper"}
    return save_config(partial)


@router.post("/test_ark")
async def test_ark():
    if llm.is_mock():
        return {"ok": True, "message": "当前为 Mock 模式，未真实调用方舟"}
    try:
        reply = await llm.chat(
            [{"role": "user", "content": "请只回复四个字：连接成功"}],
            temperature=0,
            timeout=60,
        )
        return {"ok": True, "message": f"方舟连接成功，模型回复：{reply[:50]}"}
    except llm.LLMError as e:
        return {"ok": False, "message": str(e)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "message": f"连接失败: {e}"}


@router.post("/test_asr")
async def test_asr():
    return await test_asr_connection()
