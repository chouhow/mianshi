"""全局配置（data/config.json），含火山 ASR / 方舟 LLM 凭据。

凭据类配置支持在项目根目录 .env 中提供（页面留空时自动回退读取，页面显式配置优先）。
"""
import copy
from pathlib import Path

from storage import DATA_DIR, load_json, save_json

CONFIG_PATH = DATA_DIR / "config.json"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# .env 变量名 → 配置键路径
ENV_MAP = {
    "ASR_WS_URL": ("asr", "ws_url"),
    "ASR_RESOURCE_ID": ("asr", "resource_id"),
    "ASR_APP_ID": ("asr", "app_id"),
    "ASR_ACCESS_TOKEN": ("asr", "access_token"),
    "ASR_API_KEY": ("asr", "api_key"),
    "ASR_UID": ("asr", "uid"),
    "ARK_BASE_URL": ("ark", "base_url"),
    "ARK_API_KEY": ("ark", "api_key"),
    "ARK_MODEL": ("ark", "model"),
}

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


def _load_env(path: Path = ENV_PATH) -> dict:
    """解析 .env（KEY=VALUE，支持注释与引号包裹），无需额外依赖。"""
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            out[key] = val
    return out


def _apply_env_fallback(cfg: dict, env: dict | None = None) -> dict:
    """页面未配置（留空）的字段，用 .env 中的值补齐。"""
    env = env if env is not None else _load_env()
    for var, (section, key) in ENV_MAP.items():
        if env.get(var) and not cfg.get(section, {}).get(key):
            cfg.setdefault(section, {})[key] = env[var]
    return cfg


def get_config() -> dict:
    stored = load_json(CONFIG_PATH, {})
    cfg = _deep_merge(DEFAULT_CONFIG, stored)
    return _apply_env_fallback(cfg)


def save_config(partial: dict) -> dict:
    merged = _deep_merge(get_config(), partial or {})
    # 与 .env 完全一致的值不落盘，保持 .env 为这些字段的唯一来源
    env = _load_env()
    for var, (section, key) in ENV_MAP.items():
        if env.get(var) and merged.get(section, {}).get(key) == env[var]:
            merged.setdefault(section, {})[key] = ""
    save_json(CONFIG_PATH, merged)
    return get_config()


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
