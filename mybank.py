import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px
import numpy as np

# --- 1. การตั้งค่าพื้นฐานและธีม ---
st.set_page_config(page_title="Suppawit Private Bank PRO", layout="wide")
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"# <--- เปลี่ยนรหัสผ่านของคุณตรงนี้

# CSS สำหรับปรับแต่งธีม (น้ำเงิน-ดำ-เงิน)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    .stMetric { background-color: #161B22; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161B22; border-radius: 5px 5px 0 0; padding: 10px 20px; }
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
    st.title("🏦 Suppawit Private Bank")
    st.subheader("🔒 Luxury Secure Access")
    pwd_input = st.text_input("กรุณาใส่รหัสผ่าน", type="password")
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

st.title("💎 Suppawit Private Bank")
st.sidebar.button("🔒 ล็อกแอป", on_click=lambda: st.session_state.update({"auth_active": False}))

# แสดง Dashboard ยอดเงิน
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("ยอดเงินในบัญชีทั้งหมด", f"{current_balance:,.2f} THB")
with col_m2:
    dca_total = data[data['Category'] == 'DCA หุ้น']['Amount'].abs().sum() if not data.empty else 0
    st.metric("ยอดลงทุน DCA สะสม", f"{dca_total:,.2f} THB")

tab1, tab2, tab3 = st.tabs(["💰 ฝาก-ถอน/DCA", "📈 วิเคราะห์พอร์ต & กราฟ", "🧮 เครื่องคิดเลขคาดการณ์ DCA"])

# --- Tab 1: การจัดการเงิน ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        t_type = st.radio("ประเภทรายการ", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
        t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "โอนเข้า", "อื่นๆ"])
        t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
        t_note = st.text_input("บันทึกเพิ่มเติม")
        
        if st.form_submit_button("บันทึกรายการ"):
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
    st.subheader("📈 แนวโน้มยอดเงินรวม")
    if not data.empty:
        fig_line = px.line(data.sort_values('Timestamp'), x='Timestamp', y='Balance', 
                           markers=True, template="plotly_dark", color_discrete_sequence=['#3B82F6'])
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.subheader("📊 สัดส่วนการใช้เงิน (แยกตามหมวดหมู่)")
        fig_pie = px.pie(data[data['Amount'] < 0], values=data[data['Amount'] < 0]['Amount'].abs(), 
                         names='Category', template="plotly_dark", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    st.subheader("📜 ประวัติรายการทั้งหมด")
    st.dataframe(data, use_container_width=True)
    if st.button("❌ ลบรายการล่าสุด"):
        if not data.empty:
            data = data.drop(data.index[0]); save_data(data); st.rerun()

# --- Tab 3: DCA Calculator ---
with tab3:
    st.subheader("🧮 เครื่องคิดเลขวางแผนเศรษฐี (Compound Interest)")
    c1, c2, c3 = st.columns(3)
    with c1:
        monthly_invest = st.number_input("เงินลงทุนต่อเดือน (บาท)", value=5000)
    with c2:
        yearly_return = st.number_input("ผลตอบแทนคาดหวังต่อปี (%)", value=8.0)
    with c3:
        years = st.number_input("ระยะเวลาลงทุน (ปี)", value=10)
    
    # คำนวณดอกเบี้ยทบต้น
    months = years * 12
    rate_per_month = (yearly_return / 100) / 12
    future_value = monthly_invest * (((1 + rate_per_month)**months - 1) / rate_per_month) * (1 + rate_per_month)
    total_invested = monthly_invest * months
    profit = future_value - total_invested

    st.markdown(f"""
    ### 💎 ผลลัพธ์การคาดการณ์ในอีก {years} ปีข้างหน้า
    * **เงินต้นสะสม:** {total_invested:,.2f} บาท
    * **ดอกเบี้ย/กำไร:** {profit:,.2f} บาท
    * **เงินรวมทั้งหมด:** <span style='font-size: 24px; color: #3B82F6;'>{future_value:,.2f} บาท</span>
    """, unsafe_allow_html=True)
    
    # กราฟจำลองการเติบโต
    growth_data = [monthly_invest * (((1 + rate_per_month)**m - 1) / rate_per_month) for m in range(1, months + 1)]
    st.line_chart(growth_data)
