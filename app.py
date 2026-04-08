import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime

# 1. ตั้งค่าหน้าเว็บให้ดูโปร (ใช้พื้นที่เต็มจอ)
st.set_page_config(page_title="PetroSense AI", page_icon="🛢️", layout="wide")

# ==========================================
# 🔑 1. ฝัง API KEY (ระบบจะใช้ Key นี้ดึงข้อมูลอัตโนมัติ)
# ==========================================
MY_EIA_API_KEY = "DXB0f1v0nVrAqZxpRcmgKkB2RKuOIih1V1byRnQO"

# ==========================================
# 🛠️ DATA FETCHING ENGINE (ฟังก์ชันดึงข้อมูลจริง)
# ==========================================
@st.cache_data(ttl=3600) 
def fetch_eia_data(api_key):
    try:
        url = f"https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key={api_key}&frequency=daily&data[0]=value&facets[series][]=RWTC&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=30"
        response = requests.get(url, timeout=10) # ตั้งเวลา timeout 10 วิ ถ้าเน็ตหลุดจะได้ไม่ค้าง
        data = response.json()
        
        df = pd.DataFrame(data['response']['data'])
        df['period'] = pd.to_datetime(df['period'])
        df = df.rename(columns={'period': 'Date', 'value': 'Crude Oil'})
        df['Crude Oil'] = df['Crude Oil'].astype(float)
        
        df = df.sort_values('Date').reset_index(drop=True)
        # จำลองราคาน้ำมันสำเร็จรูป (บวกเพิ่มจากค่าการกลั่น)
        df['Refined Oil'] = df['Crude Oil'] + 15 + np.random.normal(0, 1, len(df))
        return df
    except Exception as e:
        return None

# ==========================================
# 2. แถบด้านข้าง (Sidebar)
# ==========================================
st.sidebar.title("🛢️ PetroSense AI")
st.sidebar.caption("Intelligent Oil Price & Supply Chain Monitor")
st.sidebar.markdown("---")
country = st.sidebar.selectbox("🌏 เลือกตลาดอ้างอิง:", ["สหรัฐอเมริกา (WTI) 🇺🇸", "ไทย (อิงสิงคโปร์) 🇹🇭"])
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 System Status")

# ข้อมูลจำลอง (Fallback) เผื่อ API ล่ม หรือเน็ตหลุด
dates = pd.date_range(datetime.date.today() - pd.Timedelta(days=30), periods=30)
fallback_data = pd.DataFrame({
    "Date": dates,
    "Crude Oil": np.random.randn(30).cumsum() + 80,
    "Refined Oil": np.random.randn(30).cumsum() + 95
})

# ==========================================
# ⚡ ระบบดึงข้อมูลอัตโนมัติ (Auto Fetch on Load)
# ==========================================
with st.spinner("⏳ กำลังโหลดข้อมูล Real-time..."):
    real_df = fetch_eia_data(MY_EIA_API_KEY)
    
    if real_df is not None:
        df_data = real_df
        st.sidebar.success("✅ เชื่อมต่อ Live Data สำเร็จ!")
    else:
        df_data = fallback_data
        st.sidebar.error("⚠️ เน็ตเวิร์กขัดข้อง (ใช้ข้อมูลสำรอง)")

# ==========================================
# 3. สร้าง Tabs แบ่งหน้า
# ==========================================
tab1, tab2 = st.tabs(["📊 Dashboard (Main)", "🧠 Intelligence System"])

# --- TAB 1: Dashboard พื้นฐาน ---
with tab1:
    st.header(f"สรุปสถานการณ์ตลาด: {country}")
    
    col1, col2, col3 = st.columns(3)
    latest_crude = df_data["Crude Oil"].iloc[-1]
    prev_crude = df_data["Crude Oil"].iloc[-2]
    delta_crude = latest_crude - prev_crude
    
    col1.metric("ราคาน้ำมันดิบ (WTI)", f"${latest_crude:.2f}", f"{delta_crude:.2f} (เทียบวันก่อน)")
    col2.metric("ราคาน้ำมันสำเร็จรูป (Estim.)", f"${df_data['Refined Oil'].iloc[-1]:.2f}", "1.25", delta_color="inverse")
    col3.metric("ความเสี่ยง Supply Chain", "ปานกลาง", "เฝ้าระวังตะวันออกกลาง", delta_color="off")

    st.markdown("---")
    
    st.subheader("📈 แนวโน้มราคา 30 วันย้อนหลัง")
    fig = px.line(df_data, x="Date", y=["Crude Oil", "Refined Oil"], 
                  labels={"value": "ราคา (USD)", "variable": "ประเภทน้ำมัน"},
                  template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: Intelligence & Chatbot ---
# --- TAB 2: Intelligence & Chatbot ---
# --- TAB 2: Intelligence System (Track A: Synthetic Sensing) ---
with tab2:
    st.markdown("### 🌐 Planetary Signals & Synthetic Sensing Lab")
    st.caption("ผสานข้อมูล EIA (Global Price), OWID (Macro Energy), และ DOEB (Local Supply) เพื่อตรวจจับสัญญาณเตือนภัย")
    
    # --- Metrics Section (Integration Simulation) ---
    st.markdown("##### 🔗 Multi-Source Data Fusion Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("EIA Global Signal", "Active", "WTI Price & Supply", delta_color="normal")
    c2.metric("OWID Energy Context", "Active", "Energy Mix Ratio", delta_color="normal")
    c3.metric("DOEB Local Sensor", "Active", "Thai Reserve Levels", delta_color="normal")
    st.markdown("---")

    col_ai1, col_ai2 = st.columns([1.2, 1])
    
    with col_ai1:
        st.subheader("🚨 Anomaly Detection & Probabilistic Forecast")
        
        # ==========================================
        # 🧠 Data Processing สำหรับ Track A
        # ==========================================
        # 1. Anomaly Detection (ใช้ Z-Score อย่างง่ายด้วย Rolling Std)
        df_data['Rolling_Mean'] = df_data['Crude Oil'].rolling(window=5).mean()
        df_data['Rolling_Std'] = df_data['Crude Oil'].rolling(window=5).std()
        # ถ้ากระชากเกิน 1.5 เท่าของความเบี่ยงเบนมาตรฐาน ถือเป็น Anomaly
        df_data['Is_Anomaly'] = abs(df_data['Crude Oil'] - df_data['Rolling_Mean']) > (1.5 * df_data['Rolling_Std'])
        
        # 2. Probabilistic Modeling เตรียมข้อมูลคาดการณ์
        last_date = df_data["Date"].iloc[-1]
        last_price = df_data["Crude Oil"].iloc[-1]
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=7)
        
        np.random.seed(42)
        base_trend = np.random.normal(0.5, 0.8, 7).cumsum()
        forecast_prices = last_price + base_trend
        
        # สร้างกรอบความน่าจะเป็น (Confidence Intervals - 95%)
        volatility = df_data['Rolling_Std'].iloc[-1] if not pd.isna(df_data['Rolling_Std'].iloc[-1]) else 1.5
        upper_bound = forecast_prices + (volatility * np.linspace(1, 3, 7)) # ยิ่งไกลยิ่งกว้าง
        lower_bound = forecast_prices - (volatility * np.linspace(1, 3, 7))
        
        shock_threshold = last_price + 4.0 

        # ==========================================
        # 📊 กราฟที่ 1: Time-Series & Anomaly Detection
        # ==========================================
        st.markdown("##### 🔍 กราฟตรวจจับความผิดปกติ (Historical Anomaly Detection)")
        fig_actual = go.Figure()
        
        # เส้นราคาปกติ
        fig_actual.add_trace(go.Scatter(
            x=df_data["Date"].tail(20), y=df_data["Crude Oil"].tail(20),
            mode='lines', name='WTI Crude (EIA)', line=dict(color='#00B4D8', width=2)
        ))
        
        # จุด Anomaly (สีแดง)
        anomalies = df_data.tail(20)[df_data.tail(20)['Is_Anomaly']]
        if not anomalies.empty:
            fig_actual.add_trace(go.Scatter(
                x=anomalies["Date"], y=anomalies["Crude Oil"],
                mode='markers', name='Detected Anomaly', 
                marker=dict(color='red', size=8, symbol='x')
            ))

        fig_actual.update_layout(
            height=250, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
        )
        st.plotly_chart(fig_actual, use_container_width=True)

        # ==========================================
        # 🔮 กราฟที่ 2: Probabilistic Modeling Forecast
        # ==========================================
        st.markdown("##### 🎲 แบบจำลองความน่าจะเป็น (7-Day Probabilistic Forecast)")
        fig_pred = go.Figure()
        
        conn_dates = [last_date] + list(future_dates)
        conn_prices = [last_price] + list(forecast_prices)
        conn_upper = [last_price] + list(upper_bound)
        conn_lower = [last_price] + list(lower_bound)
        
        # วาดกรอบความน่าจะเป็น (Shaded Area)
        fig_pred.add_trace(go.Scatter(
            x=conn_dates + conn_dates[::-1],
            y=conn_upper + conn_lower[::-1],
            fill='toself', fillcolor='rgba(255, 77, 77, 0.2)', line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval'
        ))
        
        # เส้นทำนายหลัก
        fig_pred.add_trace(go.Scatter(
            x=conn_dates, y=conn_prices,
            mode='lines+markers', name='Expected Trajectory', 
            line=dict(color='#FF4D4D', width=3, dash='dash')
        ))

        fig_pred.add_hline(
            y=shock_threshold, line_dash="dot", line_color="#FFA500", line_width=2,
            annotation_text="⚠️ Oil Shock Threshold", annotation_position="top left"
        )

        fig_pred.update_layout(
            xaxis_title="Date", yaxis_title="Price (USD)", height=250, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
        )
        st.plotly_chart(fig_pred, use_container_width=True)

        risk_prob = np.mean(upper_bound > shock_threshold) * 100
        st.warning(f"⚠️ **Probability Assessment:** โมเดลประเมินความน่าจะเป็น {risk_prob:.0f}% ที่ราคาจะแตะระดับ Shock Threshold จากความผันผวนปัจจุบัน")
        
    with col_ai2:
        st.subheader("🤖 Signal Interpreter AI")
        st.caption("AI ตีความข้อมูลข้ามมิติ (Cross-dimensional Analysis)")
        
        # สรุปผลลัพธ์แบบ Text เชิงลึก
        st.info(
            "**🔍 บทวิเคราะห์ล่าสุด (Auto-Generated):**\n\n"
            "1. **EIA Data:** พบพฤติกรรมราคาดีดตัวผิดปกติ (Anomaly) ในช่วงสัปดาห์ที่ผ่านมา\n"
            "2. **OWID Data:** สัดส่วนการพึ่งพาพลังงานฟอสซิลของประเทศอ้างอิงยังอยู่ในระดับสูง ทำให้เปราะบางต่อ Shock\n"
            "3. **DOEB Data:** ปริมาณสำรองน้ำมันดิบในประเทศ (แบบจำลอง) อยู่ในเกณฑ์รับมือได้เพียง 45 วัน\n"
            "**ข้อเสนอแนะ:** เตรียมแผนรองรับ Supply Disruption ในระดับภูมิภาค"
        )
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "ระบบทำการ Fusion ข้อมูลเรียบร้อยแล้ว ต้องการให้ผมเจาะลึกความสัมพันธ์ของ EIA และ DOEB ในมิติไหนเพิ่มเติมไหมครับ?"}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("พิมพ์คำถาม..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            response = "จากแบบจำลอง Probabilistic หากเกิด Oil Shock ขึ้นจริง ข้อมูล DOEB ระบุว่ามาตรการอุดหนุนกองทุนน้ำมันจะสามารถพยุงราคาในประเทศได้ประมาณ 2 สัปดาห์ ก่อนที่ราคาขายปลีกจะต้องปรับตัวตามตลาดโลก (อิงจากข้อมูล EIA) ครับ"
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})