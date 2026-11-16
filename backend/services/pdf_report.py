"""面试报告 PDF 生成（fpdf2 + 系统中文字体）。"""
import glob
import os

from fpdf import FPDF

# 常见中文字体候选（按平台）
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

ACCENT = (37, 99, 235)     # 主题蓝
TEXT_MUTED = (100, 116, 139)


def _find_cjk_font() -> str:
    for cand in _FONT_CANDIDATES:
        if os.path.exists(cand):
            return cand
    for pattern in ("/usr/share/fonts/**/*.tt[cf]", "/System/Library/Fonts/**/*.tt[cf]"):
        for p in glob.glob(pattern, recursive=True):
            name = os.path.basename(p).lower()
            if any(k in name for k in ("cjk", "hei", "song", "ping", "ming", "wqy", "noto")):
                return p
    raise RuntimeError("未找到可用的中文字体，无法生成 PDF")


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        font_path = _find_cjk_font()
        # TTC 集合字体取第一个字型；fpdf2 通过后缀判断类型
        self.add_font("cjk", "", font_path)
        self.add_font("cjk", "b", font_path)  # 无粗体字型，用同款字体加粗渲染由字号区分
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(16, 14, 16)
        self._font_path = font_path

    # ---- 小工具 ----
    def h_line(self, color=(226, 232, 240)):
        self.set_draw_color(*color)
        self.set_line_width(0.4)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2)

    def kv(self, key, value):
        self.set_font("cjk", "", 10.5)
        self.set_text_color(*TEXT_MUTED)
        self.write(6, f"{key}：")
        self.set_text_color(15, 23, 42)
        self.write(6, str(value))
        self.ln(6)


def build_report_pdf(iv: dict) -> bytes:
    """渲染 PDF：①基本信息 ②各部分成绩与总分 ③总体评语 ④问题列表 ⑤各题评价汇总（按题号）。"""
    pdf = ReportPDF()
    scores = iv.get("scores") or {}
    pdf.add_page()

    # ---- 一、基本信息 ----
    pdf.set_font("cjk", "", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, "技术面试报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.kv("候选人", iv.get("candidate_name", "-"))
    pdf.kv("面试时间", (iv.get("created_at") or "-").replace("T", " "))
    pdf.kv("试卷", iv.get("paper_title", "-"))
    pdf.kv("评分模式", "逐题评判" if iv.get("judge_mode") == "per_question" else "整卷评判")
    pdf.h_line()

    # ---- 二、各部分得分与总分 ----
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "一、成绩", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    rows = [
        ("基础部分", f"{scores.get('basic', 0)}", "40"),
        ("应用部分", f"{scores.get('applied', 0)}", "30"),
        ("简历部分（题目 15 + 熟悉度 15）", f"{scores.get('resume', 0)}", "30"),
        ("总分", f"{scores.get('total', 0)}", "100"),
    ]
    with pdf.table(
        text_align=("LEFT", "CENTER", "CENTER"),
        col_widths=(110, 30, 24),
        line_height=7,
        padding=1.5,
    ) as table:
        head = table.row()
        for title in ("部分", "得分", "满分"):
            head.cell(title)
        for name, got, full in rows:
            row = table.row()
            row.cell(name)
            row.cell(got)
            row.cell(full)
    pdf.ln(4)

    # ---- 三、总体评语 ----
    if pdf.get_y() > 245:
        pdf.add_page()
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "二、总体评语", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("cjk", "", 10.5)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 6, new_x="LMARGIN", new_y="NEXT",
                   text=iv.get("overall_comment") or "（未生成）")
    if iv.get("resume_comment"):
        pdf.ln(2)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.multi_cell(0, 6, new_x="LMARGIN", new_y="NEXT",
                       text=f"简历熟悉度（{scores.get('resume_familiar', 0)}/15）：{iv['resume_comment']}")
    pdf.ln(2)

    # ---- 四、问题列表 ----
    if pdf.get_y() > 240:
        pdf.add_page()
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "三、问题列表", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    state_text = {"answered": "已回答", "unknown": "不会", "unasked": "未问", "pending": "未问"}
    items = iv.get("items", [])
    for i, it in enumerate(items, 1):
        if pdf.get_y() > 262:
            pdf.add_page()
        pdf.set_font("cjk", "", 10.5)
        pdf.set_text_color(15, 23, 42)
        state = state_text.get(it.get("state"), "-")
        unasked = it.get("state") in ("unasked", "pending")
        pdf.multi_cell(0, 6, new_x="LMARGIN", new_y="NEXT",
                       text=f"{i}. [{state}{'，不计分' if unasked else ''}] {it.get('stem', '')}")
    pdf.ln(2)

    # ---- 五、各题回答评价汇总 ----
    if pdf.get_y() > 245:
        pdf.add_page()
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "四、各题回答评价汇总", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    judged = [(i, it) for i, it in enumerate(items, 1) if it.get("state") in ("answered", "unknown")]
    for i, it in judged:
        if pdf.get_y() > 262:
            pdf.add_page()
        score = it.get("score")
        score_txt = f"{score}" if score is not None else "-"
        pdf.set_font("cjk", "", 10.5)
        pdf.set_text_color(*ACCENT)
        pdf.write(6, f"题{i}（{score_txt}/5）：")
        pdf.set_text_color(51, 65, 85)
        pdf.write(6, it.get("comment") or "-")
        pdf.ln(6)
    if not judged:
        pdf.set_font("cjk", "", 10.5)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(0, 6, "（无已回答题目）", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


_SHEET_SECTION_ORDER = {"基础": 0, "应用": 1, "简历": 2}


def _write_line(pdf, height=8):
    """画一条浅灰书写线（供手写）。"""
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.35)
    y = pdf.get_y() + height - 2
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(height)


def build_scoring_sheet_pdf(paper: dict) -> bytes:
    """线下评分表 PDF：仅列出题目与空白评分/评语栏（得分、过程评价、整体评价均留空），
    供无电脑与麦克风的场景由面试官手写评分。"""
    pdf = ReportPDF()
    resolved = paper.get("resolved") or {"sections": []}
    sections = sorted(resolved.get("sections", []),
                      key=lambda s: _SHEET_SECTION_ORDER.get(s.get("section"), 9))
    total = sum(len(s.get("questions", [])) for s in sections)
    pdf.add_page()

    # ---- 标题与基本信息（留空手填） ----
    pdf.set_font("cjk", "", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 12, "技术面试评分表", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("cjk", "", 10)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 6, "（线下纸质评分 · 供无电脑 / 麦克风场景使用）", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("cjk", "", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, "候选人：______________　　面试日期：____________　　面试官：______________",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("cjk", "", 10)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 6, f"试卷：{paper.get('title', '-')}　·　题库题 {total} 道", new_x="LMARGIN", new_y="NEXT")
    pdf.h_line()

    # ---- 一、成绩汇总（留空手填） ----
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "一、成绩汇总", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    rows = [
        ("基础部分（满分 5×8，Top-8 加权）", "40"),
        ("应用部分（满分 5×6，Top-6 加权）", "30"),
        ("简历 · 题目", "15"),
        ("简历 · 熟悉度", "15"),
        ("总分", "100"),
    ]
    with pdf.table(
        text_align=("LEFT", "CENTER", "CENTER"),
        col_widths=(110, 30, 24),
        line_height=7,
        padding=1.5,
    ) as table:
        head = table.row()
        for title in ("部分", "得分（手填）", "满分"):
            head.cell(title)
        for name, full in rows:
            row = table.row()
            row.cell(name)
            row.cell("")
            row.cell(full)
    pdf.ln(2)
    pdf.set_font("cjk", "", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.multi_cell(0, 5, new_x="LMARGIN", new_y="NEXT",
                   text="评分规则：每题满分 5 分，「不会」计 0 分，未问的题不计入。"
                        "各部分计分题数 ≥ K 时取最好的 K 题折算平均分占 80%、其余题占 20% 加权（基础 K=8、应用 K=6、简历题 K=3）；"
                        "计分题数 < K 时按每题实际得分直接求和。")
    pdf.ln(2)

    # ---- 二、题目评分（题干 + 空白得分/评语） ----
    if pdf.get_y() > 235:
        pdf.add_page()
    pdf.set_font("cjk", "", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "二、题目评分", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    no = 0
    for sec in sections:
        for q in sec.get("questions", []):
            no += 1
            if pdf.get_y() > 250:
                pdf.add_page()
            meta = "｜".join(filter(None, [sec.get("section"), q.get("category"), q.get("difficulty")]))
            if q.get("embedded"):
                meta += "｜按简历生成"
            pdf.set_font("cjk", "b", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(0, 6, new_x="LMARGIN", new_y="NEXT",
                           text=f"{no}.【{meta}】{q.get('stem', '')}")
            pdf.set_font("cjk", "", 10.5)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.write(6, "得分：______ / 5　　评语：")
            pdf.ln(6)
            _write_line(pdf)
            _write_line(pdf, 7)
            pdf.ln(1)
        # 简历部分：面试时按简历现场生成的题，预留空位手记
        for _ in range(sec.get("llm_gen_count") or 0):
            no += 1
            if pdf.get_y() > 250:
                pdf.add_page()
            pdf.set_font("cjk", "b", 10.5)
            pdf.set_text_color(15, 23, 42)
            pdf.write(6, f"{no}.【{sec.get('section')}｜按简历现场生成】题干：")
            pdf.ln(6)
            _write_line(pdf, 7)
            pdf.set_font("cjk", "", 10.5)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.write(6, "得分：______ / 5　　评语：")
            pdf.ln(6)
            _write_line(pdf)
            _write_line(pdf, 7)
            pdf.ln(1)

    # ---- 三 / 四、简历熟悉度与整体评价（留空手写） ----
    for title, n_lines in (("三、简历熟悉度评价（______ / 15）", 3), ("四、整体评价", 4)):
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_font("cjk", "", 13)
        pdf.set_text_color(*ACCENT)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        for _ in range(n_lines):
            _write_line(pdf)
        pdf.ln(2)

    return bytes(pdf.output())
