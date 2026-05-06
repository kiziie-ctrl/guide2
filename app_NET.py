import streamlit as st
import json
from google import genai
from google.genai import types

# 1. 頁面基本設定
st.set_page_config(page_title="附中 AI 導覽員", page_icon="🏫")
st.title("🏫 陽明交大附中 - 小胖 (Gemini 2.0)")

# 2. 讀取 tour.json
try:
    with open('tour.json', 'r', encoding='utf-8') as f:
        # 讀取 JSON 並轉為字串作為模型背景知識
        context_data = json.load(f)
        context_text = json.dumps(context_data, ensure_ascii=False)
except FileNotFoundError:
    st.error("❌ 找不到 tour.json 檔案，請確認檔案是否存在於根目錄。")
    st.stop()
except Exception as e:
    st.error(f"❌ 讀取 JSON 發生錯誤：{e}")
    st.stop()

# 3. 初始化 Gemini Client 與對話 Session
if "gemini_client" not in st.session_state:
    # 從 Streamlit Secrets 取得 API Key
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    st.session_state.gemini_client = client

    # 設定系統指令（System Instruction）
    system_instruction = (
        f"你是陽明交大附中導覽員「小胖」。\n"
        f"請優先參考以下提供的【手冊內容】來回答問題，如果手冊內找不到答案，請使用 Google 搜尋補足。\n\n"
        f"【手冊內容】：\n{context_text}"
    )

    # 設定模型配置：包含 Google Search 工具
    config = types.GenerateContentConfig(
        model="gemini-2.0-flash", # 建議使用目前的穩定版本
        system_instruction=system_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())], # 啟用上網搜尋
        temperature=0.7
    )
    st.session_state.config = config

    # 建立對話 Session
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.0-flash",
        config=config
    )
    
    # 初始歡迎訊息
    st.session_state.messages = [
        {"role": "assistant", "content": "哈囉！我是小胖。我已經更新了我的導覽手冊，並連上網路了，有什麼問題儘管問我！"}
    ]

# 4. 顯示對話歷史紀錄
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 5. 使用者輸入處理
if prompt := st.chat_input("想問關於附中的什麼事？"):
    # 顯示使用者訊息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("小胖思考中並查閱資料..."):
        try:
            # 發送訊息給 Gemini
            response = st.session_state.chat_session.send_message(prompt)
            
            # 取得模型回應文字
            response_text = response.text
            
            # 顯示助理回應
            st.chat_message("assistant").write(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"❌ 發生連線或處理異常：{e}")
            st.info("提示：請檢查 API Key 是否有效，或嘗試稍後再試。")
