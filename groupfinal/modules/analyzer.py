import pandas as pd
from google.generativeai import GenerativeModel
from google.api_core.exceptions import GoogleAPIError

model = GenerativeModel("gemini-1.5-flash-8b")

def analyze_strengths_and_weaknesses(df):
    results = []

    for _, row in df.iterrows():
        name = row.get("姓名", "未命名")
        scores = {
            "聽力": row.get("聽力成績", 0),
            "口說": row.get("口說成績", 0),
            "閱讀": row.get("閱讀成績", 0),
            "寫作": row.get("寫作成績", 0)
        }

        # 找出強弱項目
        sorted_skills = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [s[0] for s in sorted_skills[:2]]
        weaknesses = [s[0] for s in sorted_skills[-2:]]

        # 建構 prompt 給 Gemini
        prompt = f"""
你是一位日語教師，請針對以下學生的語言能力分數，分析其學習優勢與劣勢，並提供針對性的學習建議。建議內容請涵蓋：
- 強項技能可如何進階學習
- 弱項技能可如何補強
- 適合的教材或練習方式
- 回應為簡潔段落

學生資料：
姓名：{name}
聽力：{scores['聽力']}
口說：{scores['口說']}
閱讀：{scores['閱讀']}
寫作：{scores['寫作']}

強項：{', '.join(strengths)}
弱項：{', '.join(weaknesses)}
"""

        try:
            response = model.generate_content(prompt)
            suggestion = response.text.strip() if response and response.text else ""
        except GoogleAPIError as e:
            suggestion = f"⚠️ API 錯誤：{e}"
        except Exception as e:
            suggestion = f"⚠️ 建議產生失敗：{e}"

        results.append({
            "姓名": name,
            "聽力": scores['聽力'],
            "口說": scores['口說'],
            "閱讀": scores['閱讀'],
            "寫作": scores['寫作'],
            "強項": ", ".join(strengths),
            "弱項": ", ".join(weaknesses),
            "建議": suggestion
        })

    return results