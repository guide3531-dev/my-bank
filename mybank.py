import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px
import numpy as np

# --- 1. การตั้งค่าพื้นฐานและธีมเน้นความชัดเจน ---
st.set_page_config(page_title="Suppawit Bank PRO", layout="wide")
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"  # <--- เปลี่ยนรหัสผ่านของคุณตรงนี้

# CSS ปรับแต่งเพื่อให้ตัวหนังสือขาวชัดเจนที่สุด
st.markdown("""
    <style>
    /* พื้นหลังดำสนิท */
    .stApp { 
        background-color: #000000; 
    }
    
    /* บังคับตัวหนังสือทุกส่วนเป็นสีขาวสด */
    html, body, [data-testid="stWidgetLabel"], .stText, p, h1, h2, h3, h4, h5, h6, span, label {
        color: #FFFFFF !important;
        font-size: 1.05rem !important;
    }

    /* กล่องยอดเงิน (Metric) เน้นขอบน้ำเงินและตัวเลขขนาดใหญ่ */
    div[data-testid="stMetric"] {
        background-color: #0A1120;
        border: 2px solid #3B82F6;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] > div {
        color: #FFFFFF !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #3B82F6 !important;
        font-size: 1.2rem !important;
        text-transform: uppercase;
    }

    /* ปรับแต่งช่อง Input ให้มีขอบชัดเจน */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border: 2px solid #3B82F6 !important;
        font-size: 1.1rem !important;
        height: 45px;
    }

    /* ปุ่มกดสีน้ำเงิน Royal Blue */
    .stButton>button {
        width: 100%;
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        border-radius: 12px;
        padding: 15px;
        font-size: 1.2rem !important;
        font-weight: bold;
        border: none;
        box-shadow: 0px 4px 10px rgba(59, 130, 246, 0.4);
    }

    /* แถบ Tab ขยายตัวอักษรให้ใหญ่ */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        color: #FFFFFF !important;
        border-radius: 10px 10px 0 0;
        padding: 12px 25px;
        font-size: 1.1rem !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important;
    }

    /* ตารางข้อมูล (Dataframe) */
    .styled-table {
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการเวลาและข้อมูล ---
def get_thai_time():
    tz_thai = timezone(timedelta(hours=7))
    return datetime.now(tz_thai)

def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)
        return df
    return pd.DataFrame(columns=['Timestamp', 'Type', 'Category', 'Detail', 'Amount', 'Balance'])

def save_data(df):
    df_to_save = df.copy()
    df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime("%d/%m/%Y %H:%M")
    df_to_save.to_csv(FILE_NAME, index=False)

# --- 3. ระบบล็อคแอป ---
if 'auth_active' not in st.session_state:
    st.session_state.auth_active = False

if not st.session_state.auth_active:
    st.markdown("<h1 style='text-align: center; color: white;'>🏦 SUPPAWIT BANK</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #3B82F6;'>Please Enter Security Password</p>", unsafe_allow_html=True)
    
    # สร้างกล่อง Login ตรงกลาง
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        pwd_input = st.text_input("PASSWORD", type="password", label_visibility="collapsed")
        if st.button("LOGIN"):
            if pwd_input == USER_PASSWORD:
                st.session_state.auth_active = True
                st.rerun()
            else:
                st.error("Invalid Password")
    st.stop()

# --- 4. หน้าหลักแอป ---
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.markdown("<h1 style='color: white;'>💎 Suppawit Bank PRO</h1>", unsafe_allow_html=True)

# Dashboard ยอดเงินแบบชัดเจน
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("TOTAL BALANCE", f"{current_balance:,.2f} THB")
with col_m2:
    dca_total = data[data['Category'] == 'DCA หุ้น']['Amount'].abs().sum() if not data.empty else 0
    st.metric("TOTAL DCA", f"{dca_total:,.2f} THB")

tab1, tab2, tab3 = st.tabs(["💰 TRANSACTIONS", "📈 HISTORY & GRAPH", "🧮 DCA CALCULATOR"])

# --- Tab 1: การจัดการเงิน ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        st.markdown("<h3 style='color: #3B82F6;'>➕ บันทึกรายการใหม่</h3>", unsafe_allow_html=True)
        t_type = st.radio("ประเภทรายการ", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
        t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "โอนเข้า", "อื่นๆ"])
        t_amt = st.number_input("จำนวนเงิน (THB)", min_value=0.0)
        t_note = st.text_input("บันทึกเพิ่มเติม (Note)")
        
        if st.form_submit_button("SAVE TRANSACTION"):
            final_amt = t_amt if t_type == "ฝากเงิน" else -t_amt
            new_balance = current_balance + final_amt
            now_thai = get_thai_time()
            new_record = pd.DataFrame([{
                'Timestamp': now_thai.replace(tzinfo=None),
                'Type': t_type, 'Category': t_cat, 'Detail': t_note,
                'Amount': final_amt, 'Balance': new_balance
            }])
            data = pd.concat([new_record, data], ignore_index=True)
            save_data(data)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()

# --- Tab 2: กราฟและประวัติ ---
with tab2:
    if not data.empty:
        st.markdown("<h3 style='color: #3B82F6;'>📊 Growth Graph</h3>", unsafe_allow_html=True)
        # ปรับเส้นกราฟให้หนาและชัด
        fig_line = px.line(data.sort_values('Timestamp'), x='Timestamp', y='Balance', 
                           markers=True, template="plotly_dark")
        fig_line.update_traces(line=dict(width=4, color='#3B82F6'), marker=dict(size=10))
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown("<h3 style='color: #3B82F6;'>📜 History</h3>", unsafe_allow_html=True)
        st.dataframe(data.style.format(subset=['Amount', 'Balance'], formatter="{:,.2f}"), use_container_width=True)
        
        if st.button("❌ DELETE LAST RECORD"):
            data = data.drop(data.index[0]); save_data(data); st.rerun()
    else:
        st.info("No Data Available")

# --- Tab 3: DCA Calculator ---
with tab3:
    st.markdown("<h3 style='color: #3B82F6;'>🧮 DCA Future Predictor</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        monthly_invest = st.number_input("ออมต่อเดือน (บาท)", value=5000)
        years = st.number_input("ระยะเวลา (ปี)", value=10)
    with c2:
        yearly_return = st.number_input("กำไรเฉลี่ยต่อปี (%)", value=8.0)
    
    months = int(years * 12)
    rate = (yearly_return / 100) / 12
    future_v = monthly_invest * (((1 + rate)**months - 1) / rate) * (1 + rate)
    
    st.markdown(f"""
    <div style='background-color: #0A1120; padding: 30px; border-radius: 15px; border: 2px solid #3B82F6; margin-top: 20px;'>
        <h1 style='color: white; text-align: center; margin: 0;'>ESTIMATED: {future_v:,.2f} THB</h1>
        <p style='color: #3B82F6; text-align: center;'>Based on {years} years of saving</p>
    </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth_active = False
    st.rerun()
