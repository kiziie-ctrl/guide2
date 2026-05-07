import streamlit as st
import json
from google import genai
from google.genai import types

# 1. 頁面基本設定
st.set_page_config(page_title="附中 AI 導覽員", page_icon="🏫")
st.title("🏫 陽明交大附中 - 小胖 (Gemini 3)")

# 2. 讀取 tour.json 內容
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
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY。")
        st.stop()

    # 建立新版 SDK Client
    client = genai.Client(api_key=api_key)
    st.session_state.gemini_client = client

    # 設定系統指令 (System Instruction)
    system_instruction = (
        f"你是陽明交大附中導覽員「小胖」。你的個性親切且專業。\n"
        f"請優先參考以下提供的【手冊內容】來回答問題，如果手冊內找不到答案，請自動使用 Google 搜尋來獲取最新資訊。\n\n"
        f"【手冊內容】：\n{context_text}"
    )

    # 🚨 重要修正：GenerateContentConfig 內不可包含 model 參數，否則會報 Pydantic 錯誤
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(google_search=types.GoogleSearch())], # 開啟 Google 搜尋功能
        temperature=0.7,
    )
    st.session_state.config = config

    # 🚨 重要修正：將 model 名稱放在 chats.create 中
    # 使用你在 Playground 看到的最新預覽版模型
    try:
        st.session_state.chat_session = client.chats.create(
            model="gemini-3-flash", 
            config=config
        )
    except Exception as e:
        st.warning(f"無法啟動 Gemini 3，嘗試退回 Gemini 2.0。錯誤：{e}")
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash", 
            config=config
        )
    
    # 初始歡迎訊息
    st.session_state.messages = [
        {"role": "assistant", "content": "哈囉！我是小胖。我已經升級到 Gemini 3 最新大腦，並準備好為您導覽附中了！"}
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

    with st.spinner("小胖思考中並聯網查閱..."):
        try:
            # 發送訊息給 Gemini 3
            response = st.session_state.chat_session.send_message(prompt)
            
            # 取得模型回應文字
            response_text = response.text
            
            # 顯示助理回應
            st.chat_message("assistant").write(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"❌ 對話發生異常：{e}")
            st.info("提示：這可能是因為 API 配額限制或模型名稱變更。")
