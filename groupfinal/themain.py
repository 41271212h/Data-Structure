import os
from dotenv import load_dotenv
import asyncio
from autogen_core.models import UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 載入 .env 檔案中的環境變數
load_dotenv()

async def main():
    # 從環境變數中讀取金鑰
    api_key = os.environ.get("GEMINI_API_KEY")
    model_client = OpenAIChatCompletionClient(
        model="gemini-1.5-flash-8b",
        api_key=api_key,
    )
    response = await model_client.create([UserMessage])
    print("Agent response:", response)

if __name__ == '__main__':
    asyncio.run(main())