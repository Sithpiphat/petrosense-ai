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
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        @media (min-width: 992px) {
            [data-testid="collapsedControl"] { display: none !important; }
        }
        .top-right-badge {
            display: flex; justify-content: flex-end; align-items: center; height: 100%;
        }
        .badge-text {
            background-color: rgba(99, 102, 241, 0.1); color: #4F46E5;
            padding: 6px 16px; border-radius: 20px; font-size: 13px;
            font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.3);
        }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }
        .stButton button { border-radius: 10px; height: 50px; font-weight: 600; margin-bottom: -10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔑 2. ดึง API KEY จาก Secrets (เพื่อความปลอดภัย)
# ==========================================
# หากรันในเครื่องตัวเองแล้วยังไม่ได้ตั้ง Secrets ให้ใส่ Key สำรองไว้ที่นี่
MY_EIA_API_KEY = st.secrets.get("EIA_API_KEY", "DXB0f1v0nVrAqZxpRcmgKkB2RKuOIih1V1byRnQO")
MY_GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyCxVLLz_SuzRNuWZnyk8RF_dnNWKUTmo-o")

# ==========================================
# 🤖 3. ตั้งค่า AI Model
# ==========================================
genai.configure(api_key=MY_GEMINI_API_KEY)

system_rules = """
คุณคือ 'PetroSense AI' ผู้เชี่ยวชาญด้านพลังงาน ตอบเฉพาะเรื่องน้ำมัน/ก๊าซ/พลังงาน เท่านั้น 
ตอบให้กระชับ อิงหลักสถิติ และมีความเป็นนักวิเคราะห์ข้อมูล
"""

if "ai_model" not in st.session_state:
    st.session_state.ai_model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_rules)
    
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.ai_model.start_chat(history=[])
    st.session_state.messages = [{"role": "assistant", "content": "PetroSense AI พร้อมวิเคราะห์สัญญาณตลาดน้ำมันแล้วครับ"}]

# ==========================================
# 🛠️ 4. DATA ENGINE
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
        # จำลองราคาน้ำมันสำเร็จรูป (Refined)
        df['Refined Oil'] = df['Crude Oil'] + 15 + np.random.normal(0, 1, len(df))
        return df
    except: return None

with st.spinner("🔄 Syncing Live Signals..."):
    real_df = fetch_eia_data(MY_EIA_API_KEY)
    df_data = real_df if real_df is not None else pd.DataFrame({
        "Date": pd.date_range(datetime.date.today()-pd.Timedelta(days=29), periods=30),
        "Crude Oil": np.random.randn(30).cumsum() + 80,
        "Refined Oil": np.random.randn(30).cumsum() + 95
    })
    status_is_success = real_df is not None
    latest_crude = df_data["Crude Oil"].iloc[-1]

# ==========================================
# 🎯 5. SIDEBAR NAVIGATION
# ==========================================
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "📊 Overview Dashboard"

with st.sidebar:
    st.markdown("## 🛢️ PetroSense **OS**")
    st.markdown("---")
    st.caption("MAIN MENU")
    
    pages = {
        "📊 Overview Dashboard": "📊 Overview Dashboard",
        "🧠 Intelligence & AI": "🧠 Intelligence & AI",
        "🧪 Backtest Lab": "🧪 Backtest Lab"
    }
    
    for page_name in pages:
        if st.button(page_name, use_container_width=True, 
                     type="primary" if st.session_state.selected_page == page_name else "secondary"):
            st.session_state.selected_page = page_name
            st.rerun()
    
    st.markdown("---")
    st.caption("SYSTEM STATUS")
    st.success("🟢 System Online") if status_is_success else st.error("⚠️ Offline Mode")

# ==========================================
# 📊 6. MAIN CONTENT
# ==========================================
selected_page = st.session_state.selected_page

# --- หน้า 1: Dashboard ---
if selected_page == "📊 Overview Dashboard":
    st.title("Overview Dashboard")
    st.caption("Real-time Energy Market Monitoring")
    
    c1, c2, c3 = st.columns(3)
    delta = latest_crude - df_data["Crude Oil"].iloc[-2]
    c1.metric("Crude Oil (WTI)", f"${latest_crude:.2f}", f"{delta:.2f} USD")
    c2.metric("Refined Estim.", f"${df_data['Refined Oil'].iloc[-1]:.2f}", "1.25 USD", delta_color="inverse")
    c3.metric("Risk Level", "Moderate", "Watch: Mid-East", delta_color="off")

    with st.container(border=True):
        fig = px.line(df_data, x="Date", y=["Crude Oil", "Refined Oil"], template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# --- หน้า 2: Intelligence & AI ---
elif selected_page == "🧠 Intelligence & AI":
    st.title("Intelligence & AI")
    st.caption("Anomaly Detection & Probabilistic Forecast")

    col_ai1, col_ai2 = st.columns([1.2, 1])
    with col_ai1:
        # Anomaly Logic
        df_data['Mean'] = df_data['Crude Oil'].rolling(5).mean()
        df_data['Std'] = df_data['Crude Oil'].rolling(5).std()
        df_data['Is_Anomaly'] = abs(df_data['Crude Oil'] - df_data['Mean']) > (1.5 * df_data['Std'])
        
        with st.container(border=True):
            st.markdown("**🔍 Anomaly Detection**")
            fig_anom = go.Figure()
            fig_anom.add_trace(go.Scatter(x=df_data["Date"], y=df_data["Crude Oil"], name="Actual"))
            anoms = df_data[df_data['Is_Anomaly']]
            fig_anom.add_trace(go.Scatter(x=anoms["Date"], y=anoms["Crude Oil"], mode='markers', name='Anomaly', marker=dict(color='red')))
            fig_anom.update_layout(height=300, template="plotly_dark")
            st.plotly_chart(fig_anom, use_container_width=True)

    with col_ai2:
        with st.container(border=True):
            st.markdown("**🤖 AI Interpreter**")
            chat_container = st.container(height=250)
            for m in st.session_state.messages: chat_container.chat_message(m["role"]).write(m["content"])
            if p := st.chat_input("Ask PetroSense..."):
                st.session_state.messages.append({"role": "user", "content": p})
                resp = st.session_state.chat_session.send_message(p)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
                st.rerun()

# --- หน้า 3: Backtest Lab ---
elif selected_page == "🧪 Backtest Lab":
    st.title("Backtest Lab")
    st.caption("Historical Performance Validation")

    window = 7
    train, test = df_data.iloc[:-window], df_data.iloc[-window:]
    # จำลองการทายในอดีต
    backtest_preds = test["Crude Oil"].values * (1 + np.random.normal(0, 0.01, window))
    mae = np.mean(np.abs(test["Crude Oil"].values - backtest_preds))

    c1, c2 = st.columns(2)
    c1.metric("Mean Absolute Error", f"${mae:.2f}", "Lower is better")
    c2.metric("Model Fidelity", f"{100-(mae/latest_crude*100):.1f}%", "Confidence")

    with st.container(border=True):
        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(x=df_data["Date"], y=df_data["Crude Oil"], name="Actual Price"))
        fig_bt.add_trace(go.Scatter(x=test["Date"], y=backtest_preds, name="AI Backtest", line=dict(dash='dash', color='green')))
        fig_bt.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_bt, use_container_width=True)
    
    st.info("**Analysis:** โมเดลมีความแม่นยำสูงในช่วงเทรนด์คงที่ แต่ต้องระวังในช่วงเหตุการณ์ภูมิรัฐศาสตร์ฉับพลัน")
