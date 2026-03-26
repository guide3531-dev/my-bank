import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone # เพิ่ม timedelta และ timezone
import plotly.express as px

# --- ตั้งค่าพื้นฐาน ---
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"  # <--- อย่าลืมเปลี่ยนเป็นรหัสของคุณ

# --- ฟังก์ชันตั้งค่าเวลาประเทศไทย (GMT+7) ---
def get_thai_time():
    # สร้าง timezone ของไทย (UTC+7)
    tz_thai = timezone(timedelta(hours=7))
    return datetime.now(tz_thai)

# --- ฟังก์ชันจัดการข้อมูล ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # เปลี่ยนวิธีโหลดเวลาเพื่อให้รองรับ format ที่หลากหลาย
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)
        return df
    return pd.DataFrame(columns=['Timestamp', 'Type', 'Category', 'Detail', 'Amount', 'Balance'])

def save_data(df):
    df_to_save = df.copy()
    # เซฟเวลาลง CSV ในรูปแบบที่อ่านง่าย (วัน/เดือน/ปี ชั่วโมง:นาที)
    df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime("%d/%m/%Y %H:%M")
    df_to_save.to_csv(FILE_NAME, index=False)

# --- ระบบล็อคแอป (Session State) ---
if 'auth_active' not in st.session_state:
    st.session_state.auth_active = False

if not st.session_state.auth_active:
    st.title("🏦 Suppawit Private Bank")
    pwd_input = st.text_input("รหัสผ่าน", type="password")
    if st.button("ตกลง"):
        if pwd_input == USER_PASSWORD:
            st.session_state.auth_active = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- หน้าหลักแอป ---
st.set_page_config(page_title="My Bank Thailand Time", layout="wide")
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.title("🏦 Suppawit Private Bank")
st.metric(label="ยอดเงินคงเหลือปัจจุบัน", value=f"{current_balance:,.2f} THB")

tab1, tab2 = st.tabs(["💰 ทำรายการ", "📈 กราฟและประวัติ"])

with tab1:
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_type = st.radio("ประเภทรายการ", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
            t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "เงินโอน", "อื่นๆ"])
        with col2:
            t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
            t_note = st.text_input("บันทึก")
        
        if st.form_submit_button("บันทึกรายการ"):
            final_amt = t_amt if t_type == "ฝากเงิน" else -t_amt
            new_balance = current_balance + final_amt
            
            # ใช้ฟังก์ชัน get_thai_time() ที่เราสร้างไว้ข้างบน
            now_thai = get_thai_time()
            
            new_record = pd.DataFrame([{
                'Timestamp': now_thai.replace(tzinfo=None), # ลบข้อมูลเขตเวลาออกเพื่อให้บันทึกง่าย
                'Type': t_type, 'Category': t_cat, 'Detail': t_note,
                'Amount': final_amt, 'Balance': new_balance
            }])
            
            data = pd.concat([new_record, data], ignore_index=True)
            save_data(data)
            st.success(f"บันทึกสำเร็จเมื่อเวลา {now_thai.strftime('%H:%M')} น.")
            st.rerun()

with tab2:
    st.subheader("📈 กราฟแสดงแนวโน้มเงิน (เวลาไทย)")
    if not data.empty:
        chart_df = data.sort_values('Timestamp')
        fig = px.line(chart_df, x='Timestamp', y='Balance', markers=True,
                      labels={'Balance': 'เงินคงเหลือ', 'Timestamp': 'วันที่/เวลา'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    st.subheader("📜 ประวัติรายการ")
    st.dataframe(data, use_container_width=True)
    
    if st.button("❌ ลบรายการล่าสุด"):
        if not data.empty:
            data = data.drop(data.index[0])
            save_data(data)
            st.rerun()

if st.sidebar.button("🔒 ล็อกแอป"):
    st.session_state.auth_active = False
    st.rerun()
