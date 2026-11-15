from services.scoring import compute_scores, part_score

K8, K6, K3 = 8, 6, 3  # 基础/应用/简历题阈值


def test_part_score_empty():
    assert part_score([], K8) == 0.0


def test_full_marks():
    # 恰好 8 题全对 = 40；答 12 题全对也 = 40
    assert part_score([5.0] * 8, K8) == 40.0
    assert part_score([5.0] * 12, K8) == 40.0


def test_weighted_top_and_rest():
    # 12 题：6 个 5 分 + 6 个 3 分 → Top8 均分 4.5 占 80%、剩余均分 3 占 20%
    # = (0.8*4.5 + 0.2*3)/5*40 = 33.6（纯平均只有 32）
    assert part_score([5.0] * 6 + [3.0] * 6, K8) == 33.6
    # 12 题：前 4 题 3 分 + 后 8 题满分 → Top8 均分 5、剩余均分 3 → (4+0.6)/5*40 = 36.8
    assert part_score([3.0] * 4 + [5.0] * 8, K8) == 36.8
    # 剩余题全 0（完全没答好）只通过两成拉低：前 4 题 0 分 + 后 8 题满分 → 32（纯平均 26.7）
    assert part_score([0.0] * 4 + [5.0] * 8, K8) == 32.0


def test_below_threshold_plain_sum():
    # 答题数不足 K：直接求和，每题满分 5
    assert part_score([5.0] * 6, K8) == 30.0   # 6 题全对 = 30（不满 8 题拿不到 40）
    assert part_score([5.0] * 3, K8) == 15.0   # 3 题全对 = 15
    assert part_score([1.0, 2.0], K8) == 3.0   # 1 题 1 分 + 1 题 2 分 = 3
    assert part_score([5.0, 4.0, 0.0], K8) == 9.0  # 失手的题照实扣，无放大
    # 6 题全对 + 2 题中等(3分)：答满 8 题进入加权规则，Top8 均分 4.5 → 36
    assert part_score([5.0] * 6 + [3.0] * 2, K8) == 36.0
    # 8 题全 2 分（真不太会）→ 16
    assert part_score([2.0] * 8, K8) == 16.0


def test_all_zero():
    assert part_score([0.0] * 8, K8) == 0.0
    assert part_score([2.0], K6) == 2.0  # 单题低分 × 折扣 1/6 → 2/5*30/6 = 2


def _item(section, state, score=None):
    return {"section": section, "state": state, "score": score}


def test_compute_scores_weighted_rules():
    items = (
        [_item("基础", "answered", 3.0)] * 3      # 前 3 题一般
        + [_item("基础", "answered", 5.0)] * 8     # 后 8 题全对 → Top8 均 5、剩余均 3 → 36.8
        + [_item("基础", "unknown")] * 1            # 不会计 0，落进剩余段
        + [_item("应用", "answered", 5.0)] * 4      # 数量折扣 4/6：30×4/6=20
        + [_item("应用", "unasked", 5.0)] * 3       # 未问不计分
        + [_item("简历", "answered", 4.0)] * 3      # n=K：4/5*15=12
    )
    scores = compute_scores(items, resume_familiar_score=12.0)
    # 基础：Top8=[5]*8 均5，剩余=[3,3,3,0] 均2.25 → (4+0.45)/5*40=35.6
    assert scores["basic"] == 35.6
    assert scores["applied"] == 20.0
    assert scores["resume_q"] == 12.0
    assert scores["resume_familiar"] == 12.0
    assert scores["resume"] == 24.0
    assert scores["total"] == 79.6


def test_compute_scores_no_items():
    scores = compute_scores([], 0.0)
    assert scores["total"] == 0.0


def test_resume_capped_at_30():
    items = [_item("简历", "answered", 5.0)] * 5  # 简历题满 15
    scores = compute_scores(items, resume_familiar_score=15.0)
    assert scores["resume"] == 30.0
    assert scores["total"] == 30.0
