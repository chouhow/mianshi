"""根据简历中出现的技术，抽取并固化本次面试的题库题。"""
import hashlib
import random
import re
import unicodedata


TECHNOLOGIES = {
    "FastAPI": r"fast\s*api", "Docker": r"docker(?:file)?", "Linux": "linux",
    "Git": "git", "LangGraph": r"lang\s*graph", "LangChain": r"lang\s*chain",
    "MCP": "mcp", "RAG": "rag", "PostgreSQL": r"postgres(?:ql)?",
    "Redis": "redis", "PyTorch": r"py\s*torch", "Transformer": r"transformers?",
    "vLLM": "vllm", "LoRA": r"q?lora",
}


def resume_key(text):
    normalized = "".join(unicodedata.normalize("NFKC", text).split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def sample_questions(text, bank, excluded_stems=(), limit=6):
    text = unicodedata.normalize("NFKC", text)
    pools = {}
    used = set(excluded_stems)
    for category, pattern in TECHNOLOGIES.items():
        if re.search(r"(?<![a-z0-9])(?:" + pattern + r")(?![a-z0-9])", text, re.I):
            pool = [q for q in bank if q["category"] == category and q["stem"] not in used]
            if pool:
                pools[category] = pool
    picked = []
    while pools and len(picked) < limit:
        categories = list(pools)
        random.shuffle(categories)
        for category in categories:
            available = [q for q in pools[category] if q["stem"] not in used]
            if not available:
                del pools[category]
                continue
            question = random.choice(available)
            used.add(question["stem"])
            picked.append({**question, "id": None, "bank_question_id": question["id"],
                           "technology": category, "category": "简历"})
            if len(picked) == limit:
                break
    return picked
