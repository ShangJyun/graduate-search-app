import streamlit as st
import json
from datetime import datetime
import pandas as pd
import numpy as np
import os

# --- 1. 設定頁面與 Session State (解決按鈕沒反應的問題) ---
st.set_page_config(page_title="2026 電資研招辦", page_icon="🎓", layout="centered")

# 初始化搜尋關鍵字狀態
if 'search_input' not in st.session_state:
    st.session_state.search_input = ''

# 定義按鈕的回呼函式 (Click Callback)
def update_search(keyword):
    st.session_state.search_input = keyword

# --- 2. 注入 CSS 美化樣式 ---
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 10px 20px;
        border: 2px solid #4CAF50;
    }
    .card {
        background-color: #262730;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .urgent { border-left: 5px solid #FF4B4B !important; }
    .card-title { font-size: 1.3rem; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;}
    .info-text { color: #E0E0E0; margin-bottom: 5px; font-size: 0.95rem; }
    .countdown-text { 
        margin-top: 10px; font-weight: bold; color: #FFD700; font-size: 1rem; 
        background-color: rgba(255, 215, 0, 0.1); padding: 5px 10px; border-radius: 5px; display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 輔助函式 ---
def calculate_days_left(date_str):
    try:
        if "筆試" in date_str and ":" in date_str:
            exam_part = date_str.split("筆試")[1].replace("：", "").replace(":", "").strip()
            exam_part = exam_part.split(" ")[0].split("/")[0]
            if "." in exam_part:
                parts = exam_part.split('.')
                if len(parts) == 3:
                    roc_year, month, day = parts
                    ad_year = int(roc_year) + 1911
                    exam_date = datetime(ad_year, int(month), int(day))
                    today = datetime.now()
                    delta = exam_date - today
                    return delta.days
        return None
    except:
        return None

def get_mock_trends():
    years = ['111年', '112年', '113年', '114年(預估)']
    rates = np.random.uniform(3, 10, size=4).round(2)
    return pd.DataFrame({'年份': years, '錄取率(%)': rates})

# --- 4. 智慧搜尋邏輯 (解決搜不到台大/交大的問題) ---
def smart_search(query, data_item):
    # 1. 簡稱對應表
    query = query.lower()
    query = query.replace("台大", "臺灣大學").replace("交大", "交通大學").replace("清大", "清華大學")
    
    # 2. 將搜尋字串轉為關鍵字列表 (支援空格搜尋，例如 "台大 電子")
    # 如果使用者沒打空格 (例如 "台大電子")，這裡還是會變成單一關鍵字 "臺灣大學電子"，
    # 所以建議使用者習慣打空格，或者我們可以更暴力的檢查。
    keywords = query.split() 
    
    # 3. 檢查「所有」關鍵字是否都在資料字串中 (AND 邏輯)
    data_str = str(data_item).lower()
    return all(k in data_str for k in keywords)

# --- 5. 主程式介面 ---
st.title("🎓 研究所入學資訊搜尋")
st.caption("🚀 專為電子/通訊考生打造的戰情室")

# 搜尋框 (綁定 session_state)
query = st.text_input("", placeholder="🔍 試試看：台大 電子 (請用空白鍵分隔關鍵字)", key="search_input")

# 熱門標籤區 (改用 Callback 解決按鈕沒反應)
st.write("🔥 **快速標籤：**")
c1, c2, c3, c4 = st.columns(4)
# 這裡我們傳入帶有空格的關鍵字，確保能精準搜尋
c1.button("台大 電子", on_click=update_search, args=("台大 電子",))
c2.button("交大 電子", on_click=update_search, args=("交大 電子",))
c3.button("推甄", on_click=update_search, args=("推甄",))
c4.button("筆試日期", on_click=update_search, args=("筆試",))

# 讀取資料
json_path = "structured_data.json"
data = []
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        st.error("⚠️ 資料庫格式錯誤。")
else:
    st.warning("⚠️ 找不到資料庫，請先執行模擬資料生成腳本。")

# 執行搜尋與顯示
if query:
    # 使用新的 smart_search 函式
    results = [d for d in data if smart_search(query, d)]
    
    if results:
        st.success(f"找到 {len(results)} 筆相關資訊：")
        
        for r in results:
            days_left = calculate_days_left(r.get('重要日期', ''))
            card_class = "card urgent" if (days_left is not None and days_left < 60) else "card"
            
            countdown_html = ""
            if days_left is not None:
                countdown_html = f'<div class="countdown-text">⏳ 距離筆試還有 {days_left} 天！</div>'

            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-title">🏫 {r.get('學校名稱', '學校')} - {r.get('系所名稱', '系所')}</div>
                <div class="info-text">📅 <b>重要日期：</b> {r.get('重要日期', '未提供')}</div>
                <div class="info-text">📝 <b>招生管道：</b> {r.get('管道', '未提供')}</div>
                <div class="info-text">📚 <b>考試科目：</b> {', '.join(r.get('考試科目', [])) if isinstance(r.get('考試科目'), list) else r.get('考試科目', '無')}</div>
                {countdown_html}
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"📊 查看 {r.get('系所名稱')} 錄取趨勢"):
                st.bar_chart(get_mock_trends(), x='年份', y='錄取率(%)', color='#4CAF50')
                
    else:
        st.warning(f"😅 找不到包含「{query}」的結果。建議使用空白鍵分隔，例如：「台大 電子」")