import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
import os
from dotenv import load_dotenv
from google import genai
from reportlab.lib.styles import ParagraphStyle

def create_pdf_from_csv(csv_file, pdf_file):
    df = pd.read_csv(csv_file)

    doc = SimpleDocTemplate(pdf_file, pagesize=landscape(A4))  # 使用橫式 A4
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(f"<b>Class Report: {os.path.splitext(os.path.basename(csv_file))[0].title()}</b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    data = [df.columns.tolist()] + df.values.tolist()

    formatted_data = []
    for row in data:
        formatted_row = [Paragraph(str(cell), styles["Normal"]) for cell in row]
        formatted_data.append(formatted_row)

    table = Table(formatted_data, repeatRows=1)
    table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e1e7f0")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
]))  

    elements.append(table)
    doc.build(elements)
    print(f"✅ PDF 產出成功：{pdf_file}")

# 批次處理三個等級
for level in ["beginner", "intermediate", "advanced"]:
    csv = f"class_{level}.csv"
    pdf = f"class_{level}.pdf"
    if os.path.exists(csv):
        create_pdf_from_csv(csv, pdf)
        