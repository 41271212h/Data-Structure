import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from google import  genai 

# === 設定 ===
csv_file_path = "japanese_pretest.csv"
jlpt_file_path = "japanese_learning_info.csv"
chunk_size = 1000
batch_size = 12
output_csv = "2output.csv"
delimiter = "-----"

ITEMS = [
]

# === 載入 API Key ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# === JSON Parse Function ===
def parse_response(response_text):
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        print(f"⚠️ 解析 JSON 失敗：{e}")
        print("原始回傳內容：", response_text)
        return {item: "" for item in ITEMS}

# === Dialogue Column Detection ===
def select_dialogue_column(chunk: pd.DataFrame) -> str:
    preferred = ["text", "utterance", "content", "dialogue", "Dialogue"]
    for col in preferred:
        if col in chunk.columns:
            return col
    print("⚠️ 找不到預設欄位，將使用第一個欄位：", list(chunk.columns))
    return chunk.columns[0]

# === Classify by Score ===
def classify_level(score):
    if score < 45:
        return "Beginner"
    elif 45 <= score < 55:
        return "Intermediate"
    else:
        return "Advanced"

# === 將學生分級並輸出分類結果 ===
def classify_and_export():
    pretest_df = pd.read_csv(csv_file_path)
    jlpt_df = pd.read_csv(jlpt_file_path)
    merged_df = pd.merge(pretest_df, jlpt_df, on="StudentID")
    merged_df["Class_Level"] = merged_df["Total_Score"].apply(classify_level)

    class_groups = {
        "Beginner": merged_df[merged_df["Class_Level"] == "Beginner"],
        "Intermediate": merged_df[merged_df["Class_Level"] == "Intermediate"],
        "Advanced": merged_df[merged_df["Class_Level"] == "Advanced"]
    }

    for level, df in class_groups.items():
        filename = f"class_{level.lower()}.csv"
        df.to_csv(filename, index=False)

    return merged_df

# === 批次分析逐字稿 ===
def process_batch_dialogue(client, dialogues: list):
    prompt = (
        "你是一位日文教學專家，請根據以下編碼規則評估是否與日語教學的目標相同：\n"
        + "\n".join(ITEMS) +
        "\n\n請依據評估結果，對每個項目：若觸及則標記為 Yes，否則標記為 No。"
        "請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "```json\n"
        "{ \"Vocab\": \"Yes\", \"Listening\": \"No\", ... }\n"
        f"{delimiter}\n"
        "{...}\n```"
    )

    batch_text = f"\n{delimiter}\n".join(dialogues)
    content = prompt + "\n\n" + batch_text

    try:
        response = client.generate_content(
            model="models/gemini-1.5-flash-latest",
            contents=[{"role": "user", "parts": [content]}]
        )
    except Exception as e:
        print(f"❌ API 呼叫失敗：{e}")
        return [{item: "" for item in ITEMS} for _ in dialogues]

    response_text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
    print("✅ 批次 API 回傳內容：", response_text)

    parts = response_text.split(delimiter)
    results = []
    for part in parts:
        part = part.strip()
        if part:
            results.append(parse_response(part))

    while len(results) < len(dialogues):
        results.append({item: "" for item in ITEMS})
    return results[:len(dialogues)]

# === 主程式 ===
def main():
    if len(sys.argv) < 2:
        print("📌 使用方式：python3 second.py")
        sys.exit(1)

    input_csv = sys.argv[1]
    if os.path.exists(output_csv):
        os.remove(output_csv)

    df = pd.read_csv(input_csv)
    dialogue_col = select_dialogue_column(df)
    print(f"🔍 使用欄位作為逐字稿來源：{dialogue_col}")

    total = len(df)
    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        dialogues = [str(d).strip() for d in batch[dialogue_col]]
        batch_results = process_batch_dialogue(genai, dialogues)

        batch_df = batch.copy()
        for item in ITEMS:
            batch_df[item] = [res.get(item, "") for res in batch_results]

        mode = 'w' if start_idx == 0 else 'a'
        header = (start_idx == 0)
        batch_df.to_csv(output_csv, mode=mode, index=False, header=header, encoding="utf-8-sig")
        print(f"✅ 已處理 {end_idx}/{total} 筆資料")

        time.sleep(1)

    print(f"🎉 全部處理完成。已儲存於：{output_csv}")

if __name__ == "__main__":
    classify_and_export()
    main()
    