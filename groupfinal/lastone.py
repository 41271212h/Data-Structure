import asyncio
import sys
from google import genai
import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle

# === 設定 ===
csv_file_path = "japanese_pretest.csv"
jlpt_file_path = "japanese_learning_info.csv"
chunk_size = 1000
batch_size = 12
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
if __name__ == "__main__":
    # === Part 1: 學生分級 ===
    merged_df = classify_and_export()

    # === Part 2 & 3: 處理每個級別 ===
    for level in ["beginner", "intermediate", "advanced"]:
        input_csv = f"class_{level}.csv"
        output_csv = f"output_{level}.csv"

        if not os.path.exists(input_csv):
            print(f"⚠️ 找不到檔案：{input_csv}")
            continue

        df = pd.read_csv(input_csv)
        dialogue_col = select_dialogue_column(df)
        print(f"🔍 [{level.capitalize()}] 使用欄位作為逐字稿來源：{dialogue_col}")

        if os.path.exists(output_csv):
            os.remove(output_csv)

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
            print(f"✅ [{level.capitalize()}] 已處理 {end_idx}/{total} 筆資料")

            time.sleep(1)

        print(f"🎉 [{level.capitalize()}] 全部處理完成，結果儲存於：{output_csv}")


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
    csv = f"output_{level}.csv"
    pdf = f"output_{level}.pdf"
    if os.path.exists(csv):
        create_pdf_from_csv(csv, pdf)

#last

# 根據你的專案結構調整下列 import
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

load_dotenv()

async def process_chunk(chunk, start_idx, total_records, model_client, termination_condition):
    """
    處理單一批次資料：
      - 將該批次資料轉成 dict 格式
      - 組出提示，要求各代理人根據該批次資料進行分析，
        並提供語言學習中心建議。
      - 請 MultimodalWebSurfer 代理人利用外部網站搜尋功能，
        搜尋關於日語學習之評量基準（例如口說、單字量、文法使用、聽力技巧、閱讀測驗等），
        並將搜尋結果納入建議中。
      - 收集所有回覆訊息並返回。
    """
    # 將資料轉成 dict 格式
    chunk_data = chunk.to_dict(orient='records')
    prompt = (
        f"目前正在處理第 {start_idx} 至 {start_idx + len(chunk) - 1} 筆資料（共 {total_records} 筆）。\n"
        f"以下為該批次資料:\n{chunk_data}\n\n"
        "請根據以上資料進行分析，並提供完整的建議。"
        "其中請特別注意：\n"
        "  1. 分系市面上及網路上三份日文教學進度，並區分初學者、中等學習者、高級學習者等。；\n"
        "  2. 請 MultimodalWebSurfer 搜尋外部網站，搜尋關於日語學習之評量基準（例如口說、單字量、文法使用、聽力技巧、閱讀測驗等），\n"
        "     並將搜尋結果整合進回覆中；\n"
        "  3. 最後請提供三份不同等級且滿分為100分的日語測驗和相關參考資訊。\n"
        "請各代理人協同合作，提供一份完整且具參考價值的建議並根據調查內容，設計出一份具鑑別日語學習者的測驗考卷。"
    )
    
    # 為每個批次建立新的 agent 與 team 實例
    local_data_agent = AssistantAgent("data_agent", model_client)
    local_web_surfer = MultimodalWebSurfer("web_surfer", model_client)
    local_assistant = AssistantAgent("assistant", model_client)
    local_user_proxy = UserProxyAgent("user_proxy")
    local_team = RoundRobinGroupChat(
        [local_data_agent, local_web_surfer, local_assistant, local_user_proxy],
        termination_condition=termination_condition
    )
    
    messages = []
    async for event in local_team.run_stream(task=prompt):
        if isinstance(event, TextMessage):
            # 印出目前哪個 agent 正在運作，方便追蹤
            print(f"[{event.source}] => {event.content}\n")
            messages.append({
                "batch_start": start_idx,
                "batch_end": start_idx + len(chunk) - 1,
                "source": event.source,
                "content": event.content,
                "type": event.type,
                "prompt_tokens": event.models_usage.prompt_tokens if event.models_usage else None,
                "completion_tokens": event.models_usage.completion_tokens if event.models_usage else None
            })
    return messages

async def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("請檢查 .env 檔案中的 GEMINI_API_KEY。")
        return

    # 初始化模型用戶端 (此處示範使用 gemini-2.0-flash)
    model_client = OpenAIChatCompletionClient(
        model="gemini-2.0-flash",
        api_key=gemini_api_key,
    )
    
    termination_condition = TextMentionTermination("exit")
    
    # 使用 pandas 以 chunksize 方式讀取 CSV 檔案
    csv_file_path1 = "output_advanced.csv"
    csv_file_path2 = "output_beginner.csv"
    csv_file_path3 = "output_intermediate.csv"
    chunk_size = 1000
    chunks = []
    for csv_file_path in [csv_file_path1, csv_file_path2, csv_file_path3]:
        for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
            chunks.append(chunk)
    combined_df = pd.concat(chunks, ignore_index=True)
    total_records = sum(chunk.shape[0] for chunk in chunks)
    
    # 利用 map 與 asyncio.gather 同時處理所有批次（避免使用傳統 for 迴圈）
    tasks = list(map(
        lambda idx_chunk: process_chunk(
            idx_chunk[1],
            idx_chunk[0] * chunk_size,
            total_records,
            model_client,
            termination_condition
        ),
        enumerate(chunks)
    ))
    
    results = await asyncio.gather(*tasks)
    # 將所有批次的訊息平坦化成一個清單
    all_messages = [msg for batch in results for msg in batch]
    
    # 將對話紀錄整理成 DataFrame 並存成 CSV
    df_log = pd.DataFrame(all_messages)
    output_file = "final_conversation.csv"
    df_log.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"已將所有對話紀錄輸出為 {output_file}")

if __name__ == '__main__':
    asyncio.run(main())