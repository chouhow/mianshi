"""火山引擎豆包大模型流式语音识别（v3 二进制协议）封装。

协议参考：wss://openspeech.bytedance.com/api/v3/sauc/bigmodel
- 4 字节头：0x11 | (消息类型<<4|flags) | (序列化<<4|压缩) | 0x00，后接大端 4 字节 payload 长度
- full client request / audio only 的 payload 为 gzip(JSON / PCM)
- 服务端响应：0b1001 正常响应（gzip JSON）、0b1111 错误响应
"""
import asyncio
import gzip
import json
import struct
from typing import Optional

import websockets

from config import asr_auth_headers, asr_config


class AsrError(Exception):
    pass


# 消息类型
MSG_FULL_CLIENT = 0b0001
MSG_AUDIO_ONLY = 0b0010
MSG_SERVER_ACK = 0b1011
MSG_SERVER_RESPONSE = 0b1001
MSG_ERROR = 0b1111
# 音频包 flags：0b0010 表示最后一包（负包）
FLAG_LAST_PACKET = 0b0010

# 序列化/压缩
SER_JSON = 0b0001
COMP_GZIP = 0b0001


def _header(msg_type: int, flags: int = 0, serialization: int = SER_JSON, compression: int = COMP_GZIP) -> bytes:
    return bytes([0x11, (msg_type << 4) | flags, (serialization << 4) | compression, 0x00])


def _frame(msg_type: int, payload: bytes, flags: int = 0) -> bytes:
    header = _header(msg_type, flags)
    return header + struct.pack(">I", len(payload)) + payload


def parse_response_frame(data: bytes):
    """解析服务端帧。

    实测帧结构：[4字节头][4字节序号或错误码][4字节payload长度][payload]。
    正常响应(0b1001)中该 4 字节是递增序号；错误帧(0b1111)中是错误码
    （如 45000151 音频格式错误）。payload 为 JSON（按头的压缩标志可能 gzip）。
    返回 (msg_type, seq_or_code, payload_dict)。
    """
    if len(data) < 12:
        raise AsrError(f"响应帧过短: {len(data)} 字节")
    msg_type = data[1] >> 4
    compression = data[2] & 0x0F
    (seq_or_code,) = struct.unpack(">I", data[4:8])
    (size,) = struct.unpack(">I", data[8:12])
    payload = data[12:12 + size]
    if compression == COMP_GZIP and payload:
        try:
            payload = gzip.decompress(payload)
        except gzip.BadGzipFile:
            pass
    obj = {}
    if payload:
        try:
            obj = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            obj = {}
    return msg_type, seq_or_code, obj


class VolcanoAsrSession:
    """一次录音对应一个会话：连接、喂音频、收结果。"""

    def __init__(self):
        self._ws = None
        self.last_text = ""
        self._reader_task: Optional[asyncio.Task] = None
        self._on_partial = None  # async callback(text)
        self.error: Optional[str] = None
        self._closed = asyncio.Event()

    async def connect(self):
        cfg = asr_config()
        headers = asr_auth_headers()
        if headers is None:
            raise AsrError("未配置语音识别凭据，请在设置页填写 ASR AppID/Token 或 ApiKey")
        url = cfg.get("ws_url") or "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
        kwargs = {}
        # websockets 新版本参数名为 additional_headers（旧版 extra_headers）
        try:
            self._ws = await websockets.connect(url, additional_headers=headers, open_timeout=15)
        except TypeError:
            self._ws = await websockets.connect(url, extra_headers=headers, open_timeout=15)
        full_request = {
            "user": {"uid": cfg.get("uid") or "mianshi_user"},
            "audio": {"format": "pcm", "rate": 16000, "bits": 16, "channel": 1},
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "result_type": "full",
            },
        }
        payload = gzip.compress(json.dumps(full_request, ensure_ascii=False).encode("utf-8"))
        await self._ws.send(_frame(MSG_FULL_CLIENT, payload))

    def start_reader(self, on_partial):
        """启动后台读取任务，每收到识别文本回调一次。"""
        self._on_partial = on_partial

        async def _read_loop():
            try:
                async for msg in self._ws:
                    msg_type, seq_or_code, obj = parse_response_frame(msg)
                    if msg_type == MSG_ERROR:
                        detail = obj.get("error") or obj.get("message") or str(obj)
                        self.error = f"ASR 错误 {seq_or_code}: {detail}"
                        break
                    if msg_type in (MSG_SERVER_RESPONSE, MSG_SERVER_ACK):
                        text = (obj.get("result") or {}).get("text", "")
                        # 服务端对每个音频包都会回全量文本，仅在变化时回调，避免刷屏
                        if text and text != self.last_text:
                            self.last_text = text
                            if self._on_partial:
                                try:
                                    await self._on_partial(text)
                                except Exception:
                                    pass
            except websockets.ConnectionClosed:
                pass
            except Exception as e:  # noqa: BLE001
                if self.error is None:
                    self.error = f"ASR 连接异常: {e}"
            finally:
                self._closed.set()

        self._reader_task = asyncio.get_event_loop().create_task(_read_loop())

    async def send_audio(self, pcm: bytes, last: bool = False):
        if self._ws is None:
            return
        payload = gzip.compress(pcm)
        flags = FLAG_LAST_PACKET if last else 0
        await self._ws.send(_frame(MSG_AUDIO_ONLY, payload, flags))

    async def finish(self, timeout: float = 8.0) -> str:
        """发送结束标记并等待服务端返回最终结果。"""
        if self._ws is not None:
            try:
                await self.send_audio(b"", last=True)
            except Exception:
                pass
        # 只有 reader 已启动才需要等最终结果；连接失败时直接返回
        if self._reader_task is not None:
            try:
                await asyncio.wait_for(self._closed.wait(), timeout)
            except asyncio.TimeoutError:
                pass
        await self.close()
        return self.last_text

    async def close(self):
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
            self._reader_task = None
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None


async def test_asr_connection() -> dict:
    """仅做握手连通性测试。"""
    cfg = asr_config()
    headers = asr_auth_headers()
    if headers is None:
        return {"ok": False, "message": "未配置 ASR 凭据（AppID/Token 或 ApiKey）"}
    url = cfg.get("ws_url") or "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
    ws = None
    try:
        try:
            ws = await websockets.connect(url, additional_headers=headers, open_timeout=15)
        except TypeError:
            ws = await websockets.connect(url, extra_headers=headers, open_timeout=15)
        # 鉴权失败通常在握手或首个响应即报错；等一小段时间观察是否被服务端拒绝
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            msg_type, seq_or_code, obj = parse_response_frame(msg)
            if msg_type == MSG_ERROR:
                detail = obj.get("error") or obj.get("message") or str(obj)
                return {"ok": False, "message": f"服务端拒绝（{seq_or_code}）: {detail}"}
        except asyncio.TimeoutError:
            pass  # 未收到任何数据也说明握手已成功
        return {"ok": True, "message": "ASR 连接成功"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "message": f"ASR 连接失败: {e}"}
    finally:
        if ws:
            try:
                await ws.close()
            except Exception:
                pass
