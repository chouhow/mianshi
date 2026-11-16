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


INK = (24, 46, 65)
TEAL = (21, 105, 109)
PALE = (232, 243, 242)


class InterviewReportPDF(ReportPDF):
    def header(self):
        self.set_fill_color(*TEAL)
        self.rect(0, 0, self.w, 2, "F")

    def footer(self):
        self.set_y(-14)
        self.h_line()
        self.set_font("cjk", "", 9)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 5, f"第 {self.page_no()} 页", align="R")

    def line_text(self, text, size, color, height):
        self.set_font("cjk", "", size)
        self.set_text_color(*color)
        self.multi_cell(0, height, str(text), wrapmode="CHAR",
                        new_x="LMARGIN", new_y="NEXT")

    def section(self, title):
        if self.will_page_break(26):
            self.add_page()
        self.ln(4)
        self.h_line()
        self.line_text(title, 14, TEAL, 9)


def build_report_pdf(iv: dict) -> bytes:
    pdf = InterviewReportPDF()
    pdf.set_auto_page_break(True, 19)
    pdf.set_title("技术面试报告")
    pdf.add_page()
    scores = iv.get("scores") or {}
    date = (iv.get("created_at") or "-").replace("T", " ")
    pdf.line_text(f"候选人　{iv.get('candidate_name') or '-'}　　 面试时间　{date}", 10, INK, 5)
    pdf.ln(3)
    metrics = [("综合得分", "total", 100), ("基础", "basic", 40),
               ("应用", "applied", 30), ("简历", "resume", 30)]
    width = pdf.epw / len(metrics)
    for i, (label, key, maximum) in enumerate(metrics):
        pdf.set_fill_color(*(INK if i == 0 else PALE))
        pdf.set_text_color(*((255, 255, 255) if i == 0 else INK))
        pdf.set_font("cjk", "", 10)
        pdf.cell(width, 12, f"{label}  {scores.get(key, 0)}/{maximum}", align="C", fill=True)
    pdf.ln(14)
    pdf.line_text("总体评语", 12, TEAL, 7)
    pdf.line_text(iv.get("overall_comment") or "（未生成）", 9.5, INK, 4.8)
    if iv.get("resume_comment"):
        pdf.line_text(f"简历熟悉度（{scores.get('resume_familiar', 0)}/15）：{iv['resume_comment']}",
                      9.5, TEXT_MUTED, 4.8)

    states = {"answered": "", "unknown": "不会",
              "unasked": "未问，不计分", "pending": "未问，不计分"}
    items = iv.get("items") or []
    pdf.section(f"逐题记录　·　{len(items)} 题")
    for i, item in enumerate(items, 1):
        state = item.get("state")
        status = states.get(state, "-")
        lines = []
        if state in ("answered", "unknown"):
            score = item.get("score")
            points = f"{score if score is not None else '-'}/5"
            status = f"{status}  {points}" if status else points
            lines.append((f"评语　{item.get('comment') or '-'}", 9, TEXT_MUTED))
        lines.insert(0, (f"{i:02d}　{item.get('stem', '')}　〔{status}〕", 9.5, INK))
        line_height = 3.75
        row_padding = 0.25
        height = 2 * row_padding
        for content, size, _ in lines:
            pdf.set_font("cjk", "", size)
            height += pdf.multi_cell(0, line_height, content, wrapmode="CHAR", dry_run=True, output="HEIGHT")
        if pdf.will_page_break(height):
            pdf.add_page()
        for content, size, color in lines:
            pdf.line_text(content, size, color, line_height)
        pdf.ln(row_padding)
        pdf.set_draw_color(218, 229, 230)
        pdf.set_line_width(0.15)
        pdf.line(pdf.l_margin, pdf.y, pdf.w - pdf.r_margin, pdf.y)
        pdf.ln(row_padding)
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
