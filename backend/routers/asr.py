"""ASR 中继：浏览器麦克风 PCM → 火山流式识别 → 实时文本回传浏览器。

浏览器侧协议：
  → 文本 {"type":"start","interview_id":...,"item_id":...}  开始本次录音
  → 二进制 PCM16/16kHz/单声道 分块（约 100ms/包）
  → 文本 {"type":"stop"}                                     结束录音
  ← {"type":"started"} / {"type":"partial","text":...}（实时全量文本）
  ← {"type":"final","text":...} / {"type":"done"} / {"type":"error","message":...}
"""
import json
import wave
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.asr import AsrError, VolcanoAsrSession
from storage import DATA_DIR, audio_dir, load_interview, save_interview

router = APIRouter(tags=["asr"])


def _save_wav(pcm: bytes, interview_id: str, item_id: str):
    path = audio_dir(interview_id) / f"{item_id}.wav"
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(pcm)
    rel = Path("audio") / interview_id / f"{item_id}.wav"
    # 回填面试记录中的音频路径（尽力而为）
    interview = load_interview(interview_id)
    if interview:
        for item in interview["items"]:
            if item["id"] == item_id:
                item["audio_file"] = str(rel).replace("\\", "/")
                save_interview(interview)
                break
    return rel


@router.websocket("/ws/asr")
async def asr_relay(ws: WebSocket):
    await ws.accept()
    session: VolcanoAsrSession | None = None
    pcm_buf = bytearray()
    meta: dict = {}
    started = False
    error_message = None

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            data = msg.get("bytes") if "bytes" in msg else msg.get("text")
            if data is None:
                continue
            if isinstance(data, str):
                try:
                    cmd = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if cmd.get("type") == "start" and session is None:
                    meta = {"interview_id": cmd.get("interview_id"), "item_id": cmd.get("item_id")}
                    session = VolcanoAsrSession()

                    async def _on_partial(text: str):
                        try:
                            await ws.send_json({"type": "partial", "text": text})
                        except Exception:
                            pass

                    try:
                        await session.connect()
                        session.start_reader(_on_partial)
                        started = True
                        await ws.send_json({"type": "started"})
                    except AsrError as e:
                        error_message = str(e)
                        break
                    except Exception as e:  # noqa: BLE001
                        error_message = f"ASR 连接失败: {e}"
                        break
                elif cmd.get("type") == "stop":
                    break
            elif started and session is not None:
                pcm_buf.extend(data)
                try:
                    await session.send_audio(bytes(data))
                except Exception as e:  # noqa: BLE001
                    if not session.error:
                        session.error = f"发送音频失败: {e}"
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001
        error_message = error_message or f"中继异常: {e}"

    # ---- 收尾：等最终结果、存录音、回传 ----
    final_text = ""
    if session is not None:
        try:
            final_text = await session.finish()
        except Exception:  # noqa: BLE001
            pass
        if session.error and not error_message:
            error_message = session.error

    if pcm_buf and meta.get("interview_id") and meta.get("item_id"):
        try:
            _save_wav(bytes(pcm_buf), meta["interview_id"], meta["item_id"])
        except Exception:  # noqa: BLE001
            pass

    try:
        if error_message:
            await ws.send_json({"type": "error", "message": error_message})
        if started:
            await ws.send_json({"type": "final", "text": final_text})
            await ws.send_json({"type": "done"})
    except Exception:  # noqa: BLE001
        pass
    try:
        await ws.close()
    except Exception:  # noqa: BLE001
        pass
