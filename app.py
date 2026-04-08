import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime
import google.generativeai as genai 

# ==========================================
# 1. ตั้งค่าหน้าเว็บ & Custom CSS (SaaS Style)
# ==========================================
st.set_page_config(
    page_title="PetroSense OS", 
    page_icon="🛢️", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
        /* ซ่อน Header และ Footer พื้นฐานของ Streamlit */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 🔒 ล็อกเมนู (ซ่อนปุ่มพับ) เฉพาะบนหน้าจอคอมพิวเตอร์กว้างๆ */
        @media (min-width: 992px) {
            [data-testid="collapsedControl"] {
                display: none !important;
            }
        }
        
        /* ปรับสไตล์ Badge มุมขวาบน */
        .top-right-badge {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            height: 100%;
        }
        .badge-text {
            background-color: rgba(99, 102, 241, 0.1);
            color: #4F46E5;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(99, 102, 241, 0.3);
            letter-spacing: 0.5px;
        }
        
        /* ปรับแต่งตัวอักษร Metric ให้ดู Modern ขึ้น */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
        }
        
        /* ตกแต่งให้ปุ่มเมนูดูเป็นบล็อกโปร่งๆ */
        .stButton button {
            border-radius: 10px;
            height: 50px;
            font-weight: 600;
            margin-bottom: -10px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔑 2. ฝัง API KEY ต่างๆ
# ==========================================
MY_EIA_API_KEY = "DXB0f1v0nVrAqZxpRcmgKkB2RKuOIih1V1byRnQO"
MY_GEMINI_API_KEY = "AIzaSyCxVLLz_SuzRNuWZnyk8RF_dnNWKUTmo-o"

# ==========================================
# 🤖 3. ตั้งค่า AI Model (Gemini)
# ==========================================
genai.configure(api_key=MY_GEMINI_API_KEY)

# กฎเหล็กบังคับให้ AI คุยแค่เรื่องน้ำมันและพลังงาน
system_rules = """
คุณคือ 'PetroSense AI' ผู้เชี่ยวชาญระดับสูงด้านตลาดน้ำมัน (Oil Market), Supply Chain พลังงาน, และเศรษฐศาสตร์มหภาค
กฎข้อบังคับของคุณ:
1. ตอบคำถามที่เกี่ยวข้องกับ น้ำมัน, ก๊าซธรรมชาติ, พลังงาน, หรือเศรษฐกิจที่เชื่อมโยงกับพลังงาน เท่านั้น
2. หากผู้ใช้ถามเรื่องอื่นที่ไม่เกี่ยวข้อง (เช่น ทำอาหาร, เล่นเกม, ดารา, หรือเขียนโปรแกรมที่ไม่เกี่ยวกับแอปนี้) ให้ปฏิเสธอย่างสุภาพ แจ้งว่าคุณถูกสร้างมาเพื่อวิเคราะห์ตลาดพลังงานเท่านั้น
3. ตอบให้กระชับ อิงหลักความเป็นจริง ดูเป็นมืออาชีพ และมีความเป็นนักวิเคราะห์ข้อมูล
"""

# ใช้ Session State เพื่อเก็บ Model และประวัติแชท
if "ai_model" not in st.session_state:
    st.session_state.ai_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_rules
    )
    
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.ai_model.start_chat(history=[])
    st.session_state.messages = [{"role": "assistant", "content": "PetroSense AI พร้อมให้บริการครับ ต้องการเจาะลึกข้อมูลตลาดน้ำมันมิติไหนเป็นพิเศษไหมครับ?"}]


# ==========================================
# 🛠️ 4. DATA FETCHING ENGINE (EIA)
# ==========================================
@st.cache_data(ttl=3600) 
def fetch_eia_data(api_key):
    try:
        url = f"https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key={api_key}&frequency=daily&data[0]=value&facets[series][]=RWTC&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=30"
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data['response']['data'])
        df['period'] = pd.to_datetime(df['period'])
        df = df.rename(columns={'period': 'Date', 'value': 'Crude Oil'})
        df['Crude Oil'] = df['Crude Oil'].astype(float)
        df = df.sort_values('Date').reset_index(drop=True)
        df['Refined Oil'] = df['Crude Oil'] + 15 + np.random.normal(0, 1, len(df))
        return df
    except Exception:
        return None

# ข้อมูลสำรอง (Fallback) กรณี API ล่ม
dates = pd.date_range(datetime.date.today() - pd.Timedelta(days=30), periods=30)
fallback_data = pd.DataFrame({
    "Date": dates,
    "Crude Oil": np.random.randn(30).cumsum() + 80,
    "Refined Oil": np.random.randn(30).cumsum() + 95
})

# Sync Data
with st.spinner("🔄 Syncing Live Data..."):
    real_df = fetch_eia_data(MY_EIA_API_KEY)
    df_data = real_df if real_df is not None else fallback_data
    status_is_success = real_df is not None

# ==========================================
# 🎯 5. LAYOUT: เมนูนำทางแบบกล่อง (Sidebar)
# ==========================================
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "📊 Overview Dashboard"

with st.sidebar:
    st.markdown("## 🛢️ PetroSense **OS**")
    st.markdown("---")
    st.caption("MAIN MENU")
    
    # เมนูแบบปุ่มกด
    if st.button("📊 Overview Dashboard", use_container_width=True, 
                 type="primary" if st.session_state.selected_page == "📊 Overview Dashboard" else "secondary"):
        st.session_state.selected_page = "📊 Overview Dashboard"
        st.rerun()

    if st.button("🧠 Intelligence & AI", use_container_width=True, 
                 type="primary" if st.session_state.selected_page == "🧠 Intelligence & AI" else "secondary"):
        st.session_state.selected_page = "🧠 Intelligence & AI"
        st.rerun()
    
    st.markdown("---")
    st.caption("SYSTEM STATUS")
    if status_is_success:
        st.success("🟢 System Online")
    else:
        st.error("⚠️ Offline Mode")
        
    # Mock User Profile
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**🧑‍💻 Admin User**")
        st.caption("Enterprise Plan")

# ==========================================
# 📊 6. LAYOUT: เนื้อหาหลัก
# ==========================================
selected_page = st.session_state.selected_page

# ----------------------------------------------------
# หน้าที่ 1: Overview Dashboard
# ----------------------------------------------------
if selected_page == "📊 Overview Dashboard":
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.title("Overview Dashboard")
        st.caption("Real-time Energy Market Monitoring")
    with col_badge:
        st.markdown('<div class="top-right-badge"><span class="badge-text">🇺🇸 Market: US (WTI)</span></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    latest_crude = df_data["Crude Oil"].iloc[-1]
    prev_crude = df_data["Crude Oil"].iloc[-2]
    delta_crude = latest_crude - prev_crude
    
    with col1:
        with st.container(border=True):
            st.metric("Crude Oil (WTI)", f"${latest_crude:.2f}", f"{delta_crude:.2f} USD")
    with col2:
        with st.container(border=True):
            st.metric("Refined Estim.", f"${df_data['Refined Oil'].iloc[-1]:.2f}", "1.25 USD", delta_color="inverse")
    with col3:
        with st.container(border=True):
            st.metric("Risk Level", "Moderate", "Watch: Mid-East", delta_color="off")

    with st.container(border=True):
        st.subheader("Market Trend Analysis (30 Days)")
        fig = px.line(df_data, x="Date", y=["Crude Oil", "Refined Oil"], 
                      labels={"value": "Price (USD)", "variable": "Commodity"},
                      template="plotly_dark")
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# หน้าที่ 2: Intelligence & AI
# ----------------------------------------------------
elif selected_page == "🧠 Intelligence & AI":
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        st.title("Intelligence & AI")
        st.caption("Anomaly Detection & Probabilistic Models")
    with col_badge:
        st.markdown('<div class="top-right-badge"><span class="badge-text">🇺🇸 Market: US (WTI)</span></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**🔗 Data Fusion Status**")
        c1, c2, c3 = st.columns(3)
        c1.metric("EIA Node", "Online", "Pipeline A")
        c2.metric("OWID Context", "Synced", "Risk Model")
        c3.metric("DOEB Sensor", "Online", "Reserve")

    col_ai1, col_ai2 = st.columns([1.2, 1])
    
    # 📌 ฝั่งซ้าย: Charts & Anomaly Model
    with col_ai1:
        df_data['Rolling_Mean'] = df_data['Crude Oil'].rolling(window=5).mean()
        df_data['Rolling_Std'] = df_data['Crude Oil'].rolling(window=5).std()
        df_data['Is_Anomaly'] = abs(df_data['Crude Oil'] - df_data['Rolling_Mean']) > (1.5 * df_data['Rolling_Std'])
        
        with st.container(border=True):
            st.markdown("**🔍 Historical Anomaly Detection**")
            fig_actual = go.Figure()
            fig_actual.add_trace(go.Scatter(x=df_data["Date"].tail(20), y=df_data["Crude Oil"].tail(20), mode='lines', name='WTI', line=dict(color='#3B82F6', width=2)))
            anomalies = df_data.tail(20)[df_data.tail(20)['Is_Anomaly']]
            if not anomalies.empty:
                fig_actual.add_trace(go.Scatter(x=anomalies["Date"], y=anomalies["Crude Oil"], mode='markers', name='Anomaly', marker=dict(color='#EF4444', size=8, symbol='x')))
            fig_actual.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_actual, use_container_width=True)

    # 📌 ฝั่งขวา: Gemini Chatbot
    with col_ai2:
        with st.container(border=True):
            st.markdown("**🤖 AI Signal Interpreter**")
            st.info("• EIA Signal: พบความผิดปกติสัปดาห์ล่าสุด\n• Risk: เปราะบางต่อ Supply Shock")
            st.markdown("---")
            
            # กล่องแชท
            chat_container = st.container(height=250)
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # รับ Input จากผู้ใช้
            if prompt := st.chat_input("Ask AI about Oil Market..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container:
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    with st.chat_message("assistant"):
                        try:
                            with st.spinner("กำลังวิเคราะห์..."):
                                # ส่งข้อความไปหา Gemini
                                response = st.session_state.chat_session.send_message(prompt)
                                st.markdown(response.text)
                                st.session_state.messages.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {e}")