import pandas as pd

def classify(score):
    """根據總分進行分級"""
    if score < 45:
        return "Beginner"
    elif 45 <= score < 55:
        return "Intermediate"
    else:
        return "Advanced"

def classify_students(df: pd.DataFrame) -> pd.DataFrame:
    """
    傳入學生測驗成績資料（含總分），根據分數分類學生等級。
    - 欄位預期包含：'姓名'、'聽力成績'、'口說成績'、'閱讀成績'、'寫作成績'、'總分'
    - 回傳加入 Class_Level 欄位的新 DataFrame
    """
    if "總分" not in df.columns:
        # 若沒有總分，則以四項平均計算總分
        df["總分"] = df[["聽力成績", "口說成績", "閱讀成績", "寫作成績"]].mean(axis=1)

    df["Class_Level"] = df["總分"].apply(classify)
    return df