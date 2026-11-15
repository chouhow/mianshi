"""本地 JSON 文件存储层。

数据布局（项目根 data/ 目录）：
  questions.json          题库（列表）
  papers/{id}.json        试卷
  interviews/{id}.json    面试记录
  audio/{面试id}/{题目id}.wav   每题录音
  config.json             全局配置
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.environ.get("MIANSHI_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "papers").mkdir(exist_ok=True)
    (DATA_DIR / "interviews").mkdir(exist_ok=True)
    (DATA_DIR / "audio").mkdir(exist_ok=True)


_ensure_dirs()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(path: Path, data) -> None:
    """原子写入：先写临时文件再替换，避免写一半损坏数据。"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ---------- 题库 ----------

def load_questions() -> list:
    return load_json(DATA_DIR / "questions.json", [])


def save_questions(questions: list) -> None:
    save_json(DATA_DIR / "questions.json", questions)


# ---------- 试卷 ----------

def paper_path(paper_id: str) -> Path:
    return DATA_DIR / "papers" / f"{paper_id}.json"


def save_paper(paper: dict) -> None:
    save_json(paper_path(paper["id"]), paper)


def load_paper(paper_id: str):
    return load_json(paper_path(paper_id), None)


def list_papers() -> list:
    out = []
    for p in sorted((DATA_DIR / "papers").glob("*.json")):
        out.append(load_json(p, None))
    return [x for x in out if x]


def delete_paper(paper_id: str) -> None:
    p = paper_path(paper_id)
    if p.exists():
        p.unlink()


# ---------- 面试记录 ----------

def interview_path(interview_id: str) -> Path:
    return DATA_DIR / "interviews" / f"{interview_id}.json"


def save_interview(interview: dict) -> None:
    save_json(interview_path(interview["id"]), interview)


def load_interview(interview_id: str):
    return load_json(interview_path(interview_id), None)


def list_interviews() -> list:
    out = []
    for p in sorted((DATA_DIR / "interviews").glob("*.json")):
        out.append(load_json(p, None))
    return [x for x in out if x]


def delete_interview(interview_id: str) -> None:
    p = interview_path(interview_id)
    if p.exists():
        p.unlink()


def audio_dir(interview_id: str) -> Path:
    d = DATA_DIR / "audio" / interview_id
    d.mkdir(parents=True, exist_ok=True)
    return d
