import os
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# 設定 matplotlib 後端與字體
matplotlib.use('Agg')
matplotlib.rc('font', family='Microsoft JhengHei')  # 使用微軟正黑體顯示中文

def generate_quiz_score_plot(student_id, student_scores):
    """
    根據學生的每日小考成績，生成一張成績趨勢圖並儲存為 .png 檔案。
    
    參數:
    student_id (str): 學生 ID 或姓名
    student_scores (DataFrame): 包含 '日期' 和 '分數' 欄位的 DataFrame
    
    回傳:
    output_path (str): 儲存後的圖片檔案路徑
    """

    # 設定輸出資料夾
    output_dir = "static/quiz_scores"
    os.makedirs(output_dir, exist_ok=True)

    # 處理資料
    student_scores["Date"] = pd.to_datetime(student_scores["Date"], errors="coerce")
    student_scores["Quiz Score"] = pd.to_numeric(student_scores["Quiz Score"], errors="coerce")

    # 計算平均分數
    avg_score = student_scores["Quiz Score"].mean()

    # 畫圖
    plt.figure(figsize=(12, 6))
    sns.lineplot(x="Date", y="Quiz Score", data=student_scores, marker="o", label="scores daily", color="blue", errorbar=None)
    plt.axhline(y=avg_score, color='orange', linestyle='--', label=f"avg_scores ({avg_score:.2f})")
    plt.xlabel("Date")
    plt.ylabel("Quiz Scores")
    plt.title(f"{student_id} 's trend of quiz")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.ylim(0, 100)  # 小考分數範圍設定為 0-100

    # 儲存圖片
    output_path = os.path.join(output_dir, f"quiz_score_{student_id}.png")
    plt.savefig(output_path)
    plt.close()

    return output_path
