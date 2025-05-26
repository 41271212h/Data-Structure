import os
import pandas as pd
from google.generativeai import GenerativeModel, configure
from google.api_core.exceptions import GoogleAPIError

# ✅ 初始化 Gemini API
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-1.5-flash-8b")

SKILLS = ["聽力", "口說", "閱讀", "寫作"]

TEMPLATES = {
    "聽力": "建議設計基礎生活聽力理解題，例如日常對話聽寫、聽後選擇題。",
    "口說": "可安排口說互動活動，如看圖說話、情境角色扮演等。",
    "閱讀": "適合加入段落排序、文章主旨選擇等閱讀理解題型。",
    "寫作": "建議設計短文造句、圖文寫作等實作型題目，培養表達結構。"
}

def generate_posttest_transcript(df: pd.DataFrame) -> str:
    if "Class_Level" not in df.columns:
        raise ValueError("缺少 Class_Level 欄位，請先完成分班。")

    class_info = {}
    for level in sorted(df["Class_Level"].unique()):
        group = df[df["Class_Level"] == level]
        avg_scores = {
            skill: group[f"{skill}成績"].mean() for skill in SKILLS
        }
        sorted_skills = sorted(avg_scores.items(), key=lambda x: x[1])
        weak_skills = [s[0] for s in sorted_skills[:2]]
        class_info[level] = weak_skills

    try:
        prompt_lines = [
            "你是一位日語課程設計專家，請根據每個班級的平均弱項技能，撰寫後測題目設計建議段落。",
            "每個段落請明確指出班級名稱、弱項技能、學生傾向與出題建議，語氣自然、有教育專業感，不要使用 Exit。",
            ""
        ]
        for level, weak_skills in class_info.items():
            prompt_lines.append(f"【{level} 班】：弱項：{weak_skills[0]}、{weak_skills[1]}")
        prompt = "\n".join(prompt_lines)

        response = model.generate_content(prompt)
        suggestion = response.text.strip() if response and hasattr(response, "text") else ""
        return suggestion

    except GoogleAPIError as e:
        print("⚠️ Gemini API 錯誤，改用模板建議。\n", str(e))
        output = ["⚠️ 因為 Gemini API 額度已滿，以下為初步建議，實際建議可重新嘗試獲取：\n"]
        for level, weak_skills in class_info.items():
            suggestions = [TEMPLATES.get(skill, "") for skill in weak_skills]
            paragraph = f"【{level} 班】\n本班學生在「{weak_skills[0]}」與「{weak_skills[1]}」表現相對薄弱。\n" + "\n".join(suggestions)
            output.append(paragraph)
        return "\n\n".join(output)

    except Exception as e:
        return f"⚠️ 產生建議失敗：{e}"
    