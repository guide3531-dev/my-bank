import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px
import numpy as np

# --- 1. การตั้งค่าพื้นฐานและธีม (ปรับปรุงเพื่อการอ่านง่าย) ---
st.set_page_config(page_title="Suppawit Bank PRO", layout="wide")
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"  # <--- อย่าลืมเปลี่ยนรหัสของคุณ

# CSS ปรับแต่งให้ตัวหนังสือชัดเจนที่สุดบนมือถือ
st.markdown("""
    <style>
    /* พื้นหลังดำเข้ม ตัวหนังสือขาวบริสุทธิ์ */
    .stApp { 
        background-color: #05070A; 
        color: #FFFFFF !important; 
    }
    
    /* ปรับหัวข้อให้ขาวชัด */
    h1, h2, h3, p, span, label { 
        color: #FFFFFF !important; 
        font-weight: 500 !important;
    }

    /* กล่อง Metric (ยอดเงิน) ให้เด่นขึ้น */
    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #3B82F6;
        border-radius: 12px;
        padding: 20px;
    }
    div[data-testid="stMetricValue"] > div {
        color: #3B82F6 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ปรับแต่งช่องกรอกข้อมูลให้อ่านง่าย */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
    }

    /* ปุ่มกดสีน้ำเงินสว่าง */
    .stButton>button {
        width: 100%;
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 10px;
        padding: 12px;
        font-weight: bold;
        border: none;
    }

    /* แถบ Tab ด้านบน */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        color: #9CA3AF !important;
        border-radius: 8px 8px 0 0;
        padding: 10px 15px;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #3B82F6 !important;
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
    st.title("🏦 Suppawit Bank")
    st.markdown("### 🔒 กรุณาใส่รหัสผ่าน")
    pwd_input = st.text_input("รหัสผ่านของคุณ", type="password")
    if st.button("เข้าสู่ระบบ"):
        if pwd_input == USER_PASSWORD:
            st.session_state.auth_active = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 4. หน้าหลักแอป ---
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.title("💎 Suppawit Bank PRO")
st.sidebar.button("🔒 ล็อกแอป", on_click=lambda: st.session_state.update({"auth_active": False}))

# แสดง Dashboard ยอดเงิน
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("ยอดเงินในบัญชี", f"{current_balance:,.2f} THB")
with col_m2:
    dca_total = data[data['Category'] == 'DCA หุ้น']['Amount'].abs().sum() if not data.empty else 0
    st.metric("เงินลงทุน DCA", f"{dca_total:,.2f} THB")

tab1, tab2, tab3 = st.tabs(["💰 ฝาก-ถอน", "📈 กราฟ/ประวัติ", "🧮 คำนวณ DCA"])

# --- Tab 1: การจัดการเงิน ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        st.markdown("#### บันทึกรายการใหม่")
        t_type = st.radio("ประเภท", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
        t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "โอนเข้า", "อื่นๆ"])
        t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
        t_note = st.text_input("บันทึกเพิ่มเติม")
        
        if st.form_submit_button("ยืนยันการบันทึก"):
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
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# --- Tab 2: กราฟและประวัติ ---
with tab2:
    if not data.empty:
        st.subheader("📊 แนวโน้มยอดเงิน")
        fig_line = px.line(data.sort_values('Timestamp'), x='Timestamp', y='Balance', 
                           markers=True, template="plotly_dark", color_discrete_sequence=['#3B82F6'])
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.subheader("📜 ประวัติล่าสุด")
        st.dataframe(data, use_container_width=True)
        
        if st.button("❌ ลบรายการล่าสุด"):
            data = data.drop(data.index[0]); save_data(data); st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

# --- Tab 3: DCA Calculator ---
with tab3:
    st.subheader("🧮 คำนวณความรวยในอนาคต")
    monthly_invest = st.number_input("ออมต่อเดือน", value=5000)
    yearly_return = st.number_input("กำไรต่อปี (%)", value=8.0)
    years = st.number_input("จำนวนปีที่ออม", value=10)
    
    months = years * 12
    rate = (yearly_return / 100) / 12
    future_v = monthly_invest * (((1 + rate)**months - 1) / rate) * (1 + rate)
    
    st.markdown(f"""
    <div style='background-color: #111827; padding: 20px; border-radius: 10px; border: 1px dashed #3B82F6;'>
        <h2 style='color: white; margin: 0;'>เงินรวม: {future_v:,.2f} บาท</h2>
        <p style='color: #9CA3AF;'>จากเงินต้นทั้งหมด: {(monthly_invest*months):,.2f} บาท</p>
    </div>
    """, unsafe_allow_html=True)
    
    growth = [monthly_invest * (((1 + rate)**m - 1) / rate) for m in range(1, months + 1)]
    st.line_chart(growth)
