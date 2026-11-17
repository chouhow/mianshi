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


def test_full_interview_flow_with_favorite_append():
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

    extra = _mk_question(client, "临时追加", difficulty="困难")
    favorite_url = f"/api/questions/{extra['id']}/favorite"
    assert client.put(favorite_url, params={"favorite": True}).json()["favorite"]
    favorites = client.get("/api/questions?favorite=true&difficulty=困难").json()["questions"]
    assert [q["id"] for q in favorites] == [extra["id"]]
    append_url = f"/api/interviews/{iv['id']}/items/{extra['id']}"
    assert client.post(append_url).json()["items"][-1]["stem"] == extra["stem"]
    assert len(client.post(append_url).json()["items"]) == len(items) + 1
    assert not client.put(favorite_url, params={"favorite": False}).json()["favorite"]

    # 结束面试：剩余 pending → unasked
    iv = client.post(f"/api/interviews/{iv['id']}/finish").json()
    assert all(it["state"] != "pending" for it in iv["items"])
    unasked_count = sum(1 for it in iv["items"] if it["state"] == "unasked")
    assert unasked_count == 17 - 12

    assert client.post(append_url).status_code == 400
    assert client.post(f"/api/interviews/{iv['id']}/score").status_code == 404

    # 导出
    exp = client.get(f"/api/interviews/{iv['id']}/export").json()
    assert "面试报告" in exp["markdown"] and "张三" in exp["markdown"]

    assert "难度：困难" in exp["markdown"] and "类型：Python" in exp["markdown"]
    assert "总分" not in exp["markdown"]
    assert client.get(f"/api/interviews/{iv['id']}/export_pdf").content.startswith(b"%PDF")

    # 记录列表
    rows = client.get("/api/interviews").json()["interviews"]
    assert any(x["id"] == iv["id"] and x["status"] == "finished" for x in rows)


def test_resume_paper_and_multi_paper_interview():
    """独立简历试卷（仅含简历题）+ 多卷面试合并，报告按 section 汇总。"""
    client = make_client()
    save_config({"llm_mock": True})
    for i in range(4):
        _mk_question(client, "基础题", i=i)
    paper = client.post("/api/papers/generate", json={
        "sections": [{"section": "基础", "count": 3}],
    }).json()
    assert paper["kind"] == "bank"
    bank_count = len(client.get("/api/questions").json()["questions"])

    # 独立简历试卷（mock 模式：无需密钥，同步返回 3 题）
    r = client.post("/api/papers/generate_from_resume", json={
        "resume_text": "三年 Python 后端经验，熟悉 FastAPI 与 MySQL 优化，做过订单系统",
        "max_count": 3,
    })
    assert r.status_code == 200, r.text
    task_id = r.json()["task_id"]
    deadline = time.time() + 10
    p2 = None
    while time.time() < deadline:
        t = client.get(f"/api/papers/tasks/{task_id}").json()
        if t["status"] == "done":
            p2 = client.get("/api/papers/" + t["paper_id"]).json()
            break
        if t["status"] == "error":
            raise AssertionError(t["error"])
        time.sleep(0.1)
    assert p2 is not None
    assert p2["kind"] == "resume"
    # 仅含简历部分：无题库题、3 道内嵌简历题
    assert len(p2["sections"]) == 1 and p2["sections"][0]["section"] == "简历"
    assert p2["sections"][0]["question_ids"] == []
    assert len(p2["sections"][0]["embedded_questions"]) == 3
    # 题库没有新增题目
    assert len(client.get("/api/questions").json()["questions"]) == bank_count
    # resolved 合并展示内嵌题
    resolved_resume = [s for s in p2["resolved"]["sections"] if s["section"] == "简历"][0]
    assert all(q.get("embedded") for q in resolved_resume["questions"])
    # 列表带 kind
    rows = client.get("/api/papers").json()["papers"]
    kinds = {row["id"]: row["kind"] for row in rows}
    assert kinds[paper["id"]] == "bank" and kinds[p2["id"]] == "resume"

    # 多卷面试：随机卷 + 简历卷，题目合并且按 基础→简历 排序
    iv = client.post("/api/interviews", json={
        "paper_ids": [paper["id"], p2["id"]],
        "candidate_name": "测试", "resume_text": "",
    }).json()
    assert len(iv["items"]) == 3 + 3
    assert [it["section"] for it in iv["items"]] == ["基础"] * 3 + ["简历"] * 3
    assert paper["title"] in iv["paper_title"] and p2["title"] in iv["paper_title"]
    assert any(it["source"] == "resume" for it in iv["items"])

    # 单卷兼容写法（paper_id）仍可用
    iv2 = client.post("/api/interviews", json={
        "paper_id": paper["id"], "candidate_name": "兼容", "resume_text": "",
    }).json()
    assert len(iv2["items"]) == 3

    # 未选试卷报 422
    r = client.post("/api/interviews", json={"candidate_name": "无卷", "resume_text": ""})
    assert r.status_code == 422


def test_manual_paper_starts_empty_and_accepts_bank_questions():
    client = make_client()
    paper = client.post("/api/papers", json={"title": "自选 Python"}).json()
    assert paper["kind"] == "manual"
    assert all(not sec["question_ids"] for sec in paper["sections"])
    question = _mk_question(client, "数据库事务", difficulty="困难")
    url = f"/api/papers/{paper['id']}/questions/{question['id']}"
    assert client.put(url).status_code == 200
    assert client.put(url).status_code == 200
    saved = client.get("/api/papers/" + paper["id"]).json()
    applied = next(s for s in saved["resolved"]["sections"] if s["section"] == "应用")
    assert applied["question_ids"] == [question["id"]]
    interview = client.post("/api/interviews", json={"paper_id": paper["id"], "candidate_name": "张三"}).json()
    assert [item["question_id"] for item in interview["items"]] == [question["id"]]


def test_resume_matching_and_report_categories():
    from routers.papers import _create_resume_paper
    from services.resume_questions import sample_questions

    client = make_client()
    save_config({"llm_mock": True})
    text = "项目使用 FastAPI、Docker 和 PostgreSQL，源码托管在 GitHub。"
    bank = [_mk_question(client, category, category=category)
            for category in ("FastAPI", "Docker", "PostgreSQL", "Git")]
    large_pool = [dict(bank[0], id=str(i), stem=f"接口题 {i}") for i in range(8)]
    assert len({q["stem"] for q in sample_questions(text, large_pool)}) == 6
    sampled = sample_questions(text, bank)
    assert {q["technology"] for q in sampled} == {"FastAPI", "Docker", "PostgreSQL"}
    assert not sample_questions("熟悉 GitHub 和 storage", bank)
    base = _mk_question(client, "常规问题", category="测试基础")
    paper = client.post("/api/papers/generate", json={
        "sections": [{"section": "基础", "count": 1, "categories": [base["category"]]}]
    }).json()
    request = {"paper_ids": [paper["id"]], "candidate_name": "测试", "resume_text": text}
    interview = client.post("/api/interviews", json=request).json()
    resume_items = [i for i in interview["items"] if i["section"] == "简历"]
    assert len(resume_items) == 6
    assert all(i["category"] == "简历" for i in resume_items)
    report = client.get(f"/api/interviews/{interview['id']}/export").json()["markdown"]
    assert report.count("类型：简历") == 6 and "类型：测试基础" in report
    saved = _create_resume_paper("简历卷", [{"stem": "项目职责？", "reference_answer": "描述本人工作"}], text)
    request["paper_ids"].append(saved["id"])
    combined = client.post("/api/interviews", json=request).json()
    assert len(combined["items"]) == 5
    assert all(i["category"] == "简历" for i in combined["items"] if i["section"] == "简历")
