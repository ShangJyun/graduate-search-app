from google import genai
import json
import os
import sys

# ✅ 改成這樣：從環境變數讀取
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 增加一個檢查機制，如果讀不到 Key 就報錯停止
if not GEMINI_API_KEY:
    print("❌ 錯誤：找不到 GEMINI_API_KEY 環境變數")
    sys.exit(1)

def ai_micro_extract():
    print("✂️ 啟動微型提取模式 (節省流量版)...")
    
    # 1. 讀取原始檔
    if not os.path.exists("raw_university_data.md"):
        print("❌ 找不到 raw_university_data.md")
        return

    with open("raw_university_data.md", "r", encoding="utf-8") as f:
        full_content = f.read()

    # 2. 【關鍵步驟】智慧切割資料
    # 我們只尋找 "國立臺灣大學" 出現的位置，然後只往後抓 1500 個字
    # 這樣可以把 Token 消耗量降低 90%！
    keyword = "國立臺灣大學"
    start_index = full_content.find(keyword)
    
    if start_index == -1:
        # 如果找不到台大，就只抓最前面 1000 字
        target_content = full_content[:1000]
        print("⚠️ 找不到特定關鍵字，改抓取前 1000 字...")
    else:
        target_content = full_content[start_index : start_index + 1500]
        print(f"✅ 已鎖定「{keyword}」相關段落，大幅減少資料量...")

    client = genai.Client(api_key=str(GEMINI_API_KEY).strip())
    
    # 3. 發送請求
    model_id = "gemini-2.0-flash"
    
    prompt = f"""
    請從以下簡短的招生簡章片段中，提取「學校」、「系所」、「重要日期」、「考試科目」。
    輸出格式：JSON 列表。
    
    資料片段：
    ---
    {target_content}
    ---
    """
    
    try:
        print(f"📡 正在傳送微量數據給 {model_id}...")
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        # 4. 處理回傳
        text = response.text.strip()
        if "```json" in text:
            text = text.split("json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        
        # 寫入檔案
        with open("structured_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 成功鑽過限制！抓到了 {len(data)} 筆真實資料！")
        print("👉 現在去重新整理你的 App 網頁，你應該會看到真實的台大資料了！")

    except Exception as e:
        print(f"❌ 依然被阻擋：{e}")
        print("💡 如果連這樣都失敗，請執行下面的『方案 B』手動注入真實資料。")

if __name__ == "__main__":
    ai_micro_extract()