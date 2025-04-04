from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv


# 讀取 .env 檔案
load_dotenv("loginAI.env")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError("請確認 loginAI.env 中已正確設定 Usermane和 Password")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context()
    page = context.new_page()

    print("啟動瀏覽器，開始登入 NTNU Moodle System")

    # 進入 Facebook 登入頁面
    page.goto("https://moodle3.ntnu.edu.tw")
    page.wait_for_timeout(5000)
    page.screenshot(path="before_login.png")

    # 使用 .env 讀取帳號密碼
    page.fill("#username", USERNAME)
    page.fill("#password", PASSWORD)
    page.press("#password", "Enter")  # Ensure the correct field is used
    page.wait_for_load_state("networkidle")  # Wait for the page to fully load
    page.screenshot(path="after_login.png")

    # 等待登入完成
    page.wait_for_timeout(5000)
    print("登入成功！")
    
    # 直接前往個人頁面
    page.goto("https://moodle3.ntnu.edu.tw/course/view.php?id=47767")
    page.wait_for_timeout(5000)
    print("進入1132資料結構(Data Structure)")
    page.wait_for_timeout(5000)
    print("1132資料結構(Data Structure)開啟成功！")
    page.screenshot(path="course_opened.png")

    # 保持瀏覽器開啟，方便 Debug
    input("瀏覽器保持開啟，按 Enter 關閉...")

    # 關閉瀏覽器
    browser.close()
    print("瀏覽器已關閉")