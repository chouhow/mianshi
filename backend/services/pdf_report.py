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
    pdf.section("面试报告")
    pdf.line_text(f"候选人　{iv['candidate_name']}　　 面试时间　{iv['created_at'].replace('T', ' ')}", 10, INK, 6)
    pdf.line_text(f"试卷　{iv['paper_title']}", 10, INK, 6)
    for index, item in enumerate(iv.get("items", []), 1):
        pdf.ln(2)
        pdf.line_text(f"{index}. {item['stem']}", 11, INK, 6)
        pdf.line_text(f"难度：{item.get('difficulty') or '—'}　类型：{item.get('category') or '—'}", 10, TEAL, 5)
    pdf.section("算法笔试")
    for result in iv.get("written_results", {}).values():
        pdf.line_text(f"{result['title']}　{'通过' if result['passed'] else '未通过'}", 11, INK, 6)
    if not iv.get("written_results"):
        pdf.line_text("未登记", 10, TEXT_MUTED, 6)
    return bytes(pdf.output())


def build_interview_sheet_pdf(paper: dict) -> bytes:
    pdf = InterviewReportPDF()
    pdf.add_page()
    pdf.section(paper["title"])
    pdf.line_text("候选人：________________　面试日期：________________", 11, INK, 8)
    for section in paper["resolved"]["sections"]:
        pdf.section(section["section"])
        for index, question in enumerate(section["questions"], 1):
            pdf.line_text(f"{index}. {question['stem']}", 11, INK, 6)
            pdf.line_text(f"难度：{question.get('difficulty') or '—'}　类型：{question.get('category') or '—'}", 10, TEAL, 5)
            pdf.line_text("回答记录：", 10, TEXT_MUTED, 6)
            pdf.ln(12)
    return bytes(pdf.output())
