"""火山方舟 LLM 调用（OpenAI 兼容 Chat Completions）+ 面试评分提示词。"""
import json
import re
from typing import Optional

import httpx

from config import get_config


class LLMError(Exception):
    pass


# ---------- 基础调用 ----------

async def chat(messages: list, temperature: Optional[float] = None, timeout: float = 180.0) -> str:
    """调用方舟 chat completions，返回首个回复文本。带一次重试。"""
    cfg = get_config()["ark"]
    if not cfg.get("api_key") or not cfg.get("model"):
        raise LLMError("未配置方舟 API Key 或模型 ID，请在设置页填写")
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    body = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.1) if temperature is None else temperature,
    }
    last_err = ""
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(2):
            try:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                # 4xx 参数/鉴权问题不重试，直接抛出
                try:
                    detail = resp.json().get("error", {}).get("message", resp.text[:300])
                except Exception:
                    detail = resp.text[:300]
                last_err = f"HTTP {resp.status_code}: {detail}"
                if resp.status_code < 500:
                    break
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_err = f"网络错误: {e}"
    raise LLMError(f"方舟调用失败：{last_err}")


def extract_json(text: str):
    """从模型输出中鲁棒地提取 JSON（容忍代码围栏与前后说明文字）。"""
    if not text:
        raise LLMError("模型返回为空")
    # 去掉 ```json ... ``` 围栏
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    # 截取首个 [ 或 { 到最后一个 ] 或 }
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        raise LLMError(f"模型输出中未找到 JSON：{text[:200]}")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise LLMError(f"模型输出 JSON 解析失败：{e}；原文片段：{candidate[:200]}")


async def chat_json(messages: list) -> dict | list:
    return extract_json(await chat(messages))


def is_mock() -> bool:
    return bool(get_config().get("llm_mock"))


# ---------- 评分 ----------

JUDGE_SYSTEM = """你是严格但公正的技术面试评委。根据题目、参考答案与评分标准（采分点），对考生的口头回答评分。

评分规则（必须严格遵守）：
1. 按点给分：逐条对照评分标准，考生答到哪个采分点，就给该点的分值；没答到的点不得分。回答长度、详略、语气、表达流畅度一律不影响得分——没达到采分点，说得再多也不得分。
2. 答错不扣分：考生多说的内容、说错的内容不扣分、不抵消已答对的点。只要回答中包含某采分点的正确内容，该点即给分；仅当对该采分点本身的表述存在根本性概念错误时，该点不得分。
3. 转写宽容：语音转写的错别字不影响判断，看技术内容实质。
4. 若题目未提供评分标准，则根据参考答案自行归纳 3-5 个采分点（分值合计 5 分），再按规则 1、2 给分。
5. 总分 = 命中的采分点分值之和，上限 5 分；未作答或完全未命中任何采分点为 0 分。

只输出 JSON，格式：{"score": 总分, "comment": "列出命中的采分点与未命中的采分点，50字以内"}"""


HOLISTIC_SYSTEM = """你是严格但公正的技术面试评委。本题是开放型题目（如项目经历、简历相关、方案设计类），没有唯一标准答案。请结合参考要点与考生的口头回答，综合判断回答质量评分。

综合评价维度：
- 真实具体：有具体细节、数据、明确的个人职责，而非泛泛而谈或背诵概念
- 技术深度：能讲清方案与选型原因、难点与取舍，体现真实实践
- 完整条理：结构清晰，覆盖题目核心

评分标准（0-5 分）：
- 0：未作答或完全偏题
- 1~2：泛泛而谈、缺乏细节，或明显对内容不熟悉
- 3：基本讲清，但深度或完整性不足
- 4：具体、有条理，体现真实经验
- 5：非常深入，有量化成果、深刻的取舍思考或批判性反思

说明：口头转写的错别字不影响判断；回答中无关的赘述不加分也不扣分，只评价与题目相关的质量。

只输出 JSON，格式：{"score": 分数, "comment": "综合评价，指出亮点与不足，50字以内"}"""


def _fmt_qa(idx: int, item: dict) -> str:
    """按题目评分方式组织输入文本：按点给分题强调采分点，综合评价题给参考要点。"""
    holistic = (item.get("scoring_mode") or ("holistic" if item.get("category") == "简历" else "points")) == "holistic"
    scoring = item.get("scoring_points") or ""
    if holistic:
        scoring_part = (f"\n【参考要点（综合评价，不按点机械给分）】\n{scoring}" if scoring.strip()
                        else "\n【参考要点】（未提供，按参考答案理解题目意图）")
        mode_line = "\n【评分方式】综合评价"
    else:
        scoring_part = (f"\n【评分标准（采分点）】\n{scoring}" if scoring.strip()
                        else "\n【评分标准（采分点）】（未提供，请按参考答案自行归纳采分点）")
        mode_line = "\n【评分方式】按点给分"
    explanation = item.get("explanation") or ""
    exp_part = f"\n【题目讲解】\n{explanation}" if explanation.strip() else ""
    return (
        f"### 题目 {idx}\n【题干】{item['stem']}{mode_line}{scoring_part}\n【参考答案】{item['reference_answer']}{exp_part}\n"
        f"【考生回答】{item.get('answer_text') or '（空）'}"
    )


def _is_holistic(item: dict) -> bool:
    return (item.get("scoring_mode") or ("holistic" if item.get("category") == "简历" else "points")) == "holistic"


async def judge_question(item: dict) -> dict:
    """逐题评判，返回 {score, comment}。按点给分题/综合评价题分别使用对应评分体系。"""
    if is_mock():
        return _mock_judge(item)
    system = HOLISTIC_SYSTEM if _is_holistic(item) else JUDGE_SYSTEM
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": _fmt_qa(1, item)},
    ]
    data = await chat_json(messages)
    try:
        score = max(0.0, min(5.0, float(data["score"])))
        return {"score": score, "comment": str(data.get("comment", ""))}
    except (KeyError, TypeError, ValueError) as e:
        raise LLMError(f"评委输出格式不正确：{e}")


async def judge_whole_paper(items: list) -> list:
    """整卷评判，返回与 items 等长的 [{score, comment}]。每题标注评分方式，两套规则并行。"""
    if is_mock():
        return [_mock_judge(it) for it in items]
    qa_text = "\n\n".join(_fmt_qa(i + 1, it) for i, it in enumerate(items))
    system = (
        "你是严格但公正的技术面试评委。试卷包含两类题目，按每题标注的【评分方式】分别评分：\n\n"
        "【按点给分题规则】\n" + JUDGE_SYSTEM.split("只输出 JSON")[0].strip() +
        "\n\n【综合评价题规则】\n" + HOLISTIC_SYSTEM.split("只输出 JSON")[0].strip() +
        f"\n\n共 {len(items)} 道题，逐题输出。"
        "\n只输出 JSON，格式：{\"results\": [{\"index\": 题目序号, \"score\": 分数, \"comment\": \"评价\"}]}"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": qa_text},
    ]
    data = await chat_json(messages)
    results = data.get("results", []) if isinstance(data, dict) else data
    out = [None] * len(items)
    for r in results:
        try:
            idx = int(r["index"]) - 1
            if 0 <= idx < len(items):
                out[idx] = {
                    "score": max(0.0, min(5.0, float(r["score"]))),
                    "comment": str(r.get("comment", "")),
                }
        except (KeyError, TypeError, ValueError):
            continue
    # 漏评的题目补 0 分
    return [r if r else {"score": 0.0, "comment": "（整卷评判时该题漏评，默认 0 分）"} for r in out]


RESUME_SYSTEM = """你是资深技术面试评委。候选人简历如下，结合其面试中对简历相关问题的回答，
评估其对简历内容的熟悉程度：是否真正参与并理解简历中的项目与技术，还是存在夸大或编造嫌疑。
评分 0-15 分：13-15 非常熟悉、有真实深入的实践；9-12 比较熟悉但细节略有含糊；
5-8 熟悉度一般，多个细节说不清；0-4 明显不熟悉，疑似夸大或编造。
只输出 JSON，格式：{"score": 分数, "comment": "评价依据，100字以内"}"""


async def judge_resume_familiarity(resume_text: str, resume_items: list) -> dict:
    """简历熟悉度整体评价。"""
    if is_mock():
        avg_len = 0
        if resume_items:
            avg_len = sum(len(it.get("answer_text") or "") for it in resume_items) / len(resume_items)
        score = min(15.0, round(avg_len / 30, 1))
        return {"score": score, "comment": "【Mock】按回答长度模拟的简历熟悉度评分。"}
    qa_text = "\n\n".join(_fmt_qa(i + 1, it) for i, it in enumerate(resume_items)) or "（无简历相关问答）"
    messages = [
        {"role": "system", "content": RESUME_SYSTEM},
        {"role": "user", "content": f"【候选人简历】\n{resume_text or '（未提供）'}\n\n【简历相关问答】\n{qa_text}"},
    ]
    data = await chat_json(messages)
    try:
        score = max(0.0, min(15.0, float(data["score"])))
        return {"score": score, "comment": str(data.get("comment", ""))}
    except (KeyError, TypeError, ValueError) as e:
        raise LLMError(f"简历评价输出格式不正确：{e}")


GEN_RESUME_SYSTEM = """你是技术面试官。根据候选人简历，生成面向其简历的个性化面试题，
重点考察简历中声称掌握的技术与项目经历的真实性和深度。

题量要求：根据简历内容的丰富程度自行决定，生成 3~{max_count} 道——
简历单薄、可考察点少则 3~4 道；经历丰富、项目多则可以多问，但不超过 {max_count} 道。宁缺毋滥，不要为凑数出泛泛的题。

每题要求：题干简洁（40 字以内），只聚焦一个具体细节——
某个量化指标怎么来的、某次技术选型的原因、某个具体难点如何解决、某段职责的真实参与深度。
不要在一道题里塞多个子问题；避免"介绍一下你的项目"这类笼统提问。

explanation 字段是写给面试官看的题目说明（面试官未必熟悉候选人项目的技术栈），必须包含三部分：
【为什么问】考察点是什么（验证真实参与度/技术深度/数据可信度等）；
【期望回答】合格回答应出现的要点（具体数字、决策过程、细节取舍）；
【警惕信号】什么样的表现说明候选人可能没做过（含糊带过、说不出细节、数字前后矛盾）。

只输出 JSON，格式：{"questions": [{"stem": "题干", "reference_answer": "参考答案要点", "scoring_points": "评分标准，每行一个采分点及分值，合计5分，如：答出项目背景与职责：2分", "explanation": "为什么问：…；期望回答：…；警惕信号：…", "difficulty": "简单|中等|困难"}]}"""


async def generate_resume_questions(resume_text: str, max_count: int = 10) -> list:
    """根据简历生成个性化面试题：题量 3~max_count 由模型按简历丰富程度自行决定。"""
    if is_mock():
        return [
            {
                "stem": f"【Mock】请详细介绍你简历中的第 {i + 1} 个项目，以及你在其中承担的职责。",
                "reference_answer": "能讲清项目背景、个人职责、技术选型原因与踩坑经历。",
                "explanation": "为什么问：考察对简历项目的真实参与度；期望回答：讲清个人职责、技术选型原因与踩坑经历；警惕信号：只说团队做了什么、说不出自己具体部分。",
                "difficulty": "中等",
                "scoring_mode": "holistic",
            }
            for i in range(count)
        ]
    system = GEN_RESUME_SYSTEM.replace("{max_count}", str(max_count))
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"【候选人简历】\n{resume_text}\n\n请按上述要求生成面试题。"},
    ]
    data = await chat_json(messages)
    questions = data.get("questions", []) if isinstance(data, dict) else data
    out = []
    for q in questions:
        if not q.get("stem") or not q.get("reference_answer"):
            continue
        out.append(
            {
                "stem": str(q["stem"]),
                "reference_answer": str(q["reference_answer"]),
                "scoring_points": str(q.get("scoring_points") or ""),
                "explanation": str(q.get("explanation") or ""),
                "difficulty": q.get("difficulty") if q.get("difficulty") in ("简单", "中等", "困难") else "中等",
                "scoring_mode": "holistic",  # 简历题为开放型，综合评价
            }
        )
    if not out:
        raise LLMError("模型未生成有效的简历题目")
    return out


EXTRACT_NAME_SYSTEM = """从简历文本中提取候选人姓名。姓名通常出现在开头（"姓名：XXX"或简历标题下方），也可能是文档属性。
只输出 JSON，格式：{"name": "姓名"}；确实找不到时输出 {"name": ""}。"""


async def extract_candidate_name(resume_text: str) -> str:
    """从简历文本中提取候选人姓名，失败返回空串（不阻塞流程）。"""
    if is_mock():
        return ""
    messages = [
        {"role": "system", "content": EXTRACT_NAME_SYSTEM},
        {"role": "user", "content": resume_text[:3000]},
    ]
    try:
        data = await chat_json(messages)
        name = str(data.get("name", "")).strip()
        # 过滤明显不是姓名的结果
        return name if 1 < len(name) <= 20 and "\\n" not in name else ""
    except LLMError:
        return ""


OVERALL_SYSTEM = """你是技术面试评委。根据每题的得分与评语、各部分成绩，对面试者写一段简短的整体评价：
概括整体水平，点出主要优势与明显短板，最后一句话给录用建议。120字以内，行文连贯，不要分点罗列。
只输出 JSON，格式：{"comment": "整体评价"}"""


async def generate_overall_comment(items: list, scores: dict) -> str:
    """根据逐题评分与各部分成绩生成整体评价。"""
    if is_mock():
        avg = (scores.get("total") or 0) / 100
        level = "整体表现较好" if avg >= 0.7 else ("整体表现一般" if avg >= 0.4 else "整体表现较弱")
        return f"【Mock】{level}，建议结合各部分得分综合判断是否录用。"
    lines = []
    for i, it in enumerate(items, 1):
        if it.get("state") == "answered":
            lines.append(f"题{i}（{it.get('score')}分）：{it.get('comment') or '-'}")
        elif it.get("state") == "unknown":
            lines.append(f"题{i}：面试者表示不会（0分）")
    part_summary = (
        f"基础 {scores.get('basic')}/40，应用 {scores.get('applied')}/30，"
        f"简历题 {scores.get('resume_q')}/15，简历熟悉度 {scores.get('resume_familiar')}/15，"
        f"总分 {scores.get('total')}/100。"
    )
    messages = [
        {"role": "system", "content": OVERALL_SYSTEM},
        {"role": "user", "content": f"【各部分成绩】{part_summary}\n\n【逐题评语】\n" + "\n".join(lines)},
    ]
    try:
        data = await chat_json(messages)
        return str(data.get("comment", "")).strip()
    except LLMError:
        return ""


# ---------- Mock ----------

def _mock_judge(item: dict) -> dict:
    """确定性模拟评分：按回答长度打分，便于无密钥联调。"""
    ans = (item.get("answer_text") or "").strip()
    if not ans:
        return {"score": 0.0, "comment": "【Mock】未作答，0 分。"}
    score = max(0.0, min(5.0, round(1.0 + len(ans) / 120, 1)))
    return {"score": score, "comment": f"【Mock】按回答长度（{len(ans)}字）模拟评分：{score} 分。"}
