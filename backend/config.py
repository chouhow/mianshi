"""全局配置（data/config.json），含火山 ASR / 方舟 LLM 凭据。"""
import copy

from storage import DATA_DIR, load_json, save_json

CONFIG_PATH = DATA_DIR / "config.json"

DEFAULT_CONFIG = {
    # Electron 启动后端用的 Python 命令；留空则自动检测项目内 .venv，再退回系统 python
    "python_cmd": "",
    # 火山引擎流式语音识别（豆包大模型 ASR）
    "asr": {
        "ws_url": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel",
        "resource_id": "volc.bigasr.sauc.duration",
        # 旧版控制台：app_id + access_token；新版控制台：api_key（二选一）
        "app_id": "",
        "access_token": "",
        "api_key": "",
        "uid": "mianshi_user",
    },
    # 火山方舟 LLM（OpenAI 兼容）
    "ark": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "",
        "model": "",
        "temperature": 0.1,
    },
    # 评分模式：per_question 逐题评判 / whole_paper 整卷评判
    "judge_mode": "per_question",
    # 无密钥联调开关：mock 模式下 LLM 调用返回确定性模拟结果
    "llm_mock": False,
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def get_config() -> dict:
    stored = load_json(CONFIG_PATH, {})
    return _deep_merge(DEFAULT_CONFIG, stored)


def save_config(partial: dict) -> dict:
    merged = _deep_merge(get_config(), partial or {})
    save_json(CONFIG_PATH, merged)
    return merged


def asr_config() -> dict:
    return get_config()["asr"]


def ark_config() -> dict:
    return get_config()["ark"]


def asr_auth_headers() -> dict | None:
    """返回 ASR 鉴权 header；未配置返回 None。"""
    cfg = asr_config()
    headers = {
        "X-Api-Resource-Id": cfg.get("resource_id") or DEFAULT_CONFIG["asr"]["resource_id"],
        "X-Api-Request-Id": "",
        "X-Api-Sequence": "-1",
    }
    import uuid

    headers["X-Api-Request-Id"] = str(uuid.uuid4())
    if cfg.get("api_key"):
        headers["X-Api-Key"] = cfg["api_key"]
    elif cfg.get("app_id") and cfg.get("access_token"):
        headers["X-Api-App-Key"] = cfg["app_id"]
        headers["X-Api-Access-Key"] = cfg["access_token"]
    else:
        return None
    return headers
