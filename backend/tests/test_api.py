"""端到端 API 测试（使用临时数据目录 + LLM mock 模式，不需要任何密钥）。"""
import time

from fastapi.testclient import TestClient

from config import save_config


def make_client():
    from main import app

    return TestClient(app)


def _mk_question(client, stem, section="基础", difficulty="中等", category="Python", i=0):
    r = client.post(
        "/api/questions",
        json={
            "stem": f"{stem}-{i}",
            "reference_answer": f"参考答案-{i}",
            "explanation": "" if i % 2 else f"讲解-{i}",
            "category": category,
            "difficulty": difficulty,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_question_crud_and_validation():
    client = make_client()
    q = _mk_question(client, "Python 的 GIL 是什么", i=0)
    assert q["id"].startswith("q_")

    # 缺少必填字段报 422
    r = client.post("/api/questions", json={"stem": "", "reference_answer": "a", "category": "Python"})
    assert r.status_code == 422

    # 空白讲解允许（可选字段）
    q2 = _mk_question(client, "题", i=1)
    assert q2["explanation"] == ""

    # 更新
    r = client.put(f"/api/questions/{q['id']}", json={
        "stem": "更新后的题干", "reference_answer": "答案", "category": "数据库",
        "difficulty": "困难", "section": "应用", "explanation": "讲解",
    })
    assert r.json()["stem"] == "更新后的题干"

    # 筛选
    r = client.get("/api/questions", params={"category": "数据库"})
    assert len(r.json()["questions"]) == 1

    # 删除
    assert client.delete(f"/api/questions/{q['id']}").status_code == 200
    assert client.get("/api/questions").json()["questions"]


def test_paper_generation_insufficient_warning():
    client = make_client()
    # 清掉其他测试遗留的题目，保证题量可控
    for q in client.get("/api/questions").json()["questions"]:
        client.delete("/api/questions/" + q["id"])
    _mk_question(client, "基础题", section="基础", i=0)
    r = client.post("/api/papers/generate", json={
        "sections": [{"section": "基础", "count": 5}]
    })
    paper = r.json()
    assert len(paper["sections"][0]["question_ids"]) == 1
    assert any("少于" in w for w in paper["warnings"])


def test_full_interview_flow_with_mock_scoring():
    client = make_client()
    save_config({"llm_mock": True, "judge_mode": "per_question"})

    # 建题库：基础 10 题、应用 6 题（简历题不入库，由简历生成）
    for i in range(10):
        _mk_question(client, "基础题", section="基础", i=i)
    for i in range(6):
        _mk_question(client, "应用题", section="应用", difficulty="困难", category="数据库", i=i)

    paper = client.post("/api/papers/generate", json={
        "title": "测试卷",
        "sections": [
            {"section": "基础", "count": 8},
            {"section": "应用", "count": 6},
            {"section": "简历", "count": 0, "llm_gen_count": 2},
        ],
    }).json()
    assert [len(s["question_ids"]) for s in paper["sections"]] == [8, 6, 0]

    # 创建面试：附 2 道 LLM 生成的简历题
    iv = client.post("/api/interviews", json={
        "paper_id": paper["id"],
        "candidate_name": "张三",
        "resume_text": "三年 Python 后端经验，熟悉 FastAPI 与 MySQL 优化",
        "extra_questions": [
            {"stem": "介绍简历中的项目", "reference_answer": "讲清职责与技术选型",
             "explanation": "", "category": "简历", "difficulty": "中等", "section": "简历"},
            {"stem": "你在项目中如何做数据库优化", "reference_answer": "索引/慢查询",
             "explanation": "", "category": "简历", "difficulty": "困难", "section": "简历"},
        ],
    }).json()
    assert len(iv["items"]) == 8 + 6 + 0 + 2
    assert iv["status"] == "ongoing"

    items = iv["items"]
    answered = [it for it in items if it["section"] == "基础"][:6] \
        + [it for it in items if it["section"] == "应用"][:4] \
        + [it for it in items if it["section"] == "简历"][:2]

    # 回答 12 题，其中 2 题标"不会"
    for it in answered[:10]:
        r = client.put(f"/api/interviews/{iv['id']}/items/{it['id']}",
                       json={"answer_text": "这是一个比较完整的回答。" * 10, "state": "answered"})
        assert r.status_code == 200, r.text
    for it in answered[10:]:
        r = client.put(f"/api/interviews/{iv['id']}/items/{it['id']}",
                       json={"state": "unknown"})
        assert r.status_code == 200

    # 空回答不能保存为已回答
    r = client.put(f"/api/interviews/{iv['id']}/items/{items[0]['id']}",
                   json={"answer_text": "", "state": "answered"})
    assert r.status_code == 400

    # 结束面试：剩余 pending → unasked
    iv = client.post(f"/api/interviews/{iv['id']}/finish").json()
    assert all(it["state"] != "pending" for it in iv["items"])
    unasked_count = sum(1 for it in iv["items"] if it["state"] == "unasked")
    assert unasked_count == 16 - 12

    # 评分（mock），轮询直至完成
    assert client.post(f"/api/interviews/{iv['id']}/score").status_code == 200
    deadline = time.time() + 30
    while time.time() < deadline:
        iv = client.get(f"/api/interviews/{iv['id']}").json()
        if iv["status"] in ("scored", "score_error"):
            break
        time.sleep(0.2)
    assert iv["status"] == "scored", iv.get("score_error")

    s = iv["scores"]
    assert s["applied"] <= 30 and s["resume"] <= 30 and s["total"] <= 100
    # 基础 10 题计分（6答4未问→6计分），均分按mock长度规则；只验证边界
    assert 0 <= s["basic"] <= 40
    assert iv["resume_comment"]

    # 不会的题 0 分且不调 LLM
    unknown = [it for it in iv["items"] if it["state"] == "unknown"]
    assert all(it["score"] == 0.0 for it in unknown)

    # 导出
    exp = client.get(f"/api/interviews/{iv['id']}/export").json()
    assert "面试报告" in exp["markdown"] and "张三" in exp["markdown"]

    # 记录列表
    rows = client.get("/api/interviews").json()["interviews"]
    assert any(x["id"] == iv["id"] and x["status"] == "scored" for x in rows)


def test_paper_from_resume_embeds_questions():
    """按简历派生新试卷：简历题内嵌进试卷，不入题库。"""
    client = make_client()
    for i in range(4):
        _mk_question(client, "基础题", i=i)
    paper = client.post("/api/papers/generate", json={
        "sections": [{"section": "基础", "count": 3}],
    }).json()
    bank_count = len(client.get("/api/questions").json()["questions"])

    r = client.post(f"/api/papers/{paper['id']}/from_resume", json={
        "questions": [
            {"stem": "介绍简历中的项目", "reference_answer": "讲清职责与选型",
             "scoring_points": "讲清项目：2分", "explanation": "", "category": "简历",
             "difficulty": "中等", "frequency": "高频"},
        ],
    })
    assert r.status_code == 200, r.text
    p2 = r.json()
    resume_sec = [s for s in p2["sections"] if s["section"] == "简历"][0]
    assert len(resume_sec["embedded_questions"]) == 1
    assert resume_sec["llm_gen_count"] == 0
    # 原卷保留；题库没有新增题目
    assert client.get(f"/api/papers/{paper['id']}").status_code == 200
    assert len(client.get("/api/questions").json()["questions"]) == bank_count
    # resolved 合并展示内嵌题
    resolved_resume = [s for s in p2["resolved"]["sections"] if s["section"] == "简历"][0]
    assert any(q.get("embedded") for q in resolved_resume["questions"])
    # 创建面试包含内嵌简历题
    iv = client.post("/api/interviews", json={
        "paper_id": p2["id"], "candidate_name": "测试", "resume_text": "", "extra_questions": [],
    }).json()
    assert any(it["source"] == "resume" for it in iv["items"])
    assert len(iv["items"]) == 3 + 1
