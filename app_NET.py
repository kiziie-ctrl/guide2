import streamlit as st
import json
import google.generativeai as genai
# 這裡多導入一個工具定義
from google.generativeai.types import content_types 

st.set_page_config(page_title="附中 AI 導覽員", page_icon="🏫")
st.title("🏫 陽明交大附中 - 小胖 (Gemini 2.5)")

# 讀取 JSON
try:
    with open('tour.json', 'r', encoding='utf-8') as f:
        context_text = json.dumps(json.load(f), ensure_ascii=False)
except:
    st.error("找不到 tour.json")
    st.stop()

# 初始化
if "gemini_model" not in st.session_state:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    system_instruction = f"你是陽明交大附中導覽員小胖。優先查手冊，手冊沒寫再上網查。\n手冊內容：{context_text}"

    # ✅ 這是 2026 年最保險的宣告寫法
    # 如果 SDK 夠新，它會認識 google_search；如果不認識，這裡會直接噴錯，我們就知道是版本沒裝成功
    try:
        search_tool = genai.types.Tool(google_search=genai.types.GoogleSearch())
    except:
        # 萬一 SDK 真的太舊，退而求其次的備案
        search_tool = {"google_search": {}}

    st.session_state.gemini_model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_instruction,
        tools=[search_tool]
    )
    
    st.session_state.chat_session = st.session_state.gemini_model.start_chat(history=[])
    st.session_state.messages = [{"role": "assistant", "content": "哈囉！我是小胖。大腦修正完畢，準備好服務您了！"}]

# 顯示與輸入 (維持原樣)
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("請輸入問題..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("思考中..."):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            st.chat_message("assistant").write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"連線異常：{e}")