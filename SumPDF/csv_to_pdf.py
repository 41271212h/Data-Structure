import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import os
from dotenv import load_dotenv
from google import genai

# 載入環境變數並設定 API 金鑰
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 設定檔案名稱
csv_file = "sports_intro_dataset.csv"
pdf_file = "sports_intro_dataset.pdf"

# 讀取 CSV 資料
df = pd.read_csv(csv_file)

# 建立 PDF 文件
doc = SimpleDocTemplate(pdf_file, pagesize=A4)
styles = getSampleStyleSheet()
elements = []

# 將資料轉為表格格式
data = [df.columns.tolist()] + df.values.tolist()

# 處理表格內容格式（轉為 Paragraph，以避免文字太長）
formatted_data = []
for row in data:
    formatted_row = [Paragraph(str(cell), styles["Normal"]) for cell in row]
    formatted_data.append(formatted_row)

# 建立 Table 元件
table = Table(formatted_data, repeatRows=1)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
]))

elements.append(table)

# 產出 PDF
doc.build(elements)
print(f"✅ PDF 檔案已成功產出：{pdf_file}")