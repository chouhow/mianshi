"""面试系统 Python 后端入口。

Electron 以 `python main.py --port 18742`（cwd=backend）方式拉起；
也可手动运行用于调试：python main.py
"""
import argparse

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import asr, interviews, llm_api, papers, questions, settings

app = FastAPI(title="面试系统后端", version="0.1.0")

# 本地应用：允许任意来源（前端可能从 vite:5173 或 file:// 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "mianshi-backend"}


app.include_router(questions.router)
app.include_router(papers.router)
app.include_router(interviews.router)
app.include_router(settings.router)
app.include_router(llm_api.router)
app.include_router(asr.router)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18742)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
