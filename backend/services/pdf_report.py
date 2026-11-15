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
