import os
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 嘗試尋找系統中的中文字型
def register_chinese_font():
    font_path = os.path.join(os.path.dirname(__file__), "groupfinal/Noto_Sans_TC/NotoSansTC-VariableFont_wght.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
        print("✅ 使用中文字型：NotoSansTC-VariableFont")
    else:
        raise FileNotFoundError(f"❌ 無法找到字型檔案：{font_path}")

register_chinese_font()

# 樣式設定
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ChineseTitle", fontName="ChineseFont", fontSize=16, leading=20))
styles.add(ParagraphStyle(name="ChineseHeading", fontName="ChineseFont", fontSize=14, leading=18))
styles.add(ParagraphStyle(name="Chinese", fontName="ChineseFont", fontSize=12, leading=15))

def generate_class_pdf(df: pd.DataFrame, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
    elements = []

    title = Paragraph("<b>Class Assignment Report</b>", styles["ChineseTitle"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    data = [df.columns.tolist()] + df.values.tolist()
    formatted_data = [[Paragraph(str(cell), styles["Chinese"]) for cell in row] for row in data]

    table = Table(formatted_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e1e7f0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "ChineseFont"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elements.append(table)
    doc.build(elements)
    print(f"✅ 班級報告 PDF 已產出：{output_path}")

def generate_student_pdf(analysis_results: list, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    for entry in analysis_results:
        name = entry.get("姓名", "未命名")
        scores = {
            "聽力": entry.get("聽力", ""),
            "口說": entry.get("口說", ""),
            "閱讀": entry.get("閱讀", ""),
            "寫作": entry.get("寫作", "")
        }
        strengths = entry.get("強項", "")
        weaknesses = entry.get("弱項", "")
        suggestion = entry.get("建議", "")

        elements.append(Paragraph(f"<b>學生姓名：{name}</b>", styles["ChineseHeading"]))
        elements.append(Spacer(1, 6))

        score_data = [["技能", "分數"]] + [[k, str(v)] for k, v in scores.items()]
        score_table = Table(score_data, colWidths=[60, 60])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "ChineseFont"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 6))

        elements.append(Paragraph(f"<b>強項：</b> {strengths}", styles["Chinese"]))
        elements.append(Paragraph(f"<b>弱項：</b> {weaknesses}", styles["Chinese"]))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>學習建議：</b>", styles["Chinese"]))
        suggestion_paragraph = Paragraph(suggestion.replace("\n", "<br/>"), styles["Chinese"])
        elements.append(suggestion_paragraph)

        elements.append(Spacer(1, 18))
        elements.append(PageBreak())

    doc.build(elements)
    print(f"✅ 學生建議 PDF 已產出：{output_path}")
    
def generate_student_csv(analysis_results: list, output_path: str):
    df = pd.DataFrame(analysis_results)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 學生建議 CSV 已產出：{output_path}")