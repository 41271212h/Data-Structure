from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import os
from modules.classifier import classify_students
from modules.pdf_generator import generate_class_pdf, generate_student_pdf
from modules.posttest_suggester import generate_posttest_transcript
from google.generativeai import GenerativeModel
from google.api_core.exceptions import GoogleAPIError

app = Flask(__name__)

# 初始化 Gemini 模型
model = GenerativeModel("gemini-1.5-flash-8b")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_file = request.files["file"]
    if not uploaded_file:
        return "未上傳檔案", 400

    df = pd.read_csv(uploaded_file)
    df_classified = classify_students(df)

    # 取得使用者勾選項目
    do_class_report = 'option_class' in request.form
    do_student_report = 'option_student' in request.form
    do_posttest = 'option_posttest' in request.form

    files = []
    transcript = ""

    if do_class_report:
        generate_class_pdf(df_classified, "static/reports/class_assignment_report.pdf")
        files.append("class_assignment_report.pdf")

    if do_student_report:
        analysis_list = []
        for _, row in df_classified.iterrows():
            entry = {
                "姓名": row["姓名"],
                "聽力": row["聽力成績"],
                "口說": row["口說成績"],
                "閱讀": row["閱讀成績"],
                "寫作": row["寫作成績"],
                "強項": get_strong_skills(row),
                "弱項": get_weak_skills(row),
                "建議": generate_student_suggestion(row)
            }
            analysis_list.append(entry)
        generate_student_pdf(analysis_list, "static/reports/student_feedback_report.pdf")
        files.append("student_feedback_report.pdf")

    if do_posttest:
        transcript = generate_posttest_transcript(df_classified)

    return render_template("result.html", files=files, transcript=transcript)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory("static/reports", filename, as_attachment=True)

# 工具函式
def get_strong_skills(row):
    skills = {"聽力": row["聽力成績"], "口說": row["口說成績"],
              "閱讀": row["閱讀成績"], "寫作": row["寫作成績"]}
    return "、".join(sorted(skills, key=skills.get, reverse=True)[:2])

def get_weak_skills(row):
    skills = {"聽力": row["聽力成績"], "口說": row["口說成績"],
              "閱讀": row["閱讀成績"], "寫作": row["寫作成績"]}
    return "、".join(sorted(skills, key=skills.get)[:2])

# 學生個別建議產生
def generate_student_suggestion(row):
    try:
        prompt = (
            f"你是一位日語教學專家，請針對以下學生的成績，給出具體學習建議：\n\n"
            f"姓名：{row['姓名']}\n"
            f"聽力：{row['聽力成績']}\n口說：{row['口說成績']}\n"
            f"閱讀：{row['閱讀成績']}\n寫作：{row['寫作成績']}\n\n"
            f"請使用清楚段落說明其學習強項、弱點與改善策略，不需說明格式，只需建議內容。"
        )
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else "⚠️ 無建議內容"
    except GoogleAPIError as e:
        print("⚠️ Gemini API 錯誤：", str(e))
        return "⚠️ 由於建議產生額度已滿，請稍後再試。以下為預設建議：請加強練習弱項技能，並多利用教材進行自我檢測。"
    except Exception as e:
        return f"⚠️ 產生建議時發生錯誤：{e}"

if __name__ == "__main__":
    app.run(debug=True)