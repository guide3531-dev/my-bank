import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- ตั้งค่าพื้นฐาน ---
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"  # <--- เปลี่ยนรหัสผ่านของคุณตรงนี้

# --- ฟังก์ชันจัดการข้อมูล (เพื่อให้ข้อมูลไม่หาย) ---
def load_data():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        # แปลง Timestamp เป็นรูปแบบเวลาเพื่อให้กราฟเรียงลำดับถูกต้อง
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)
        return df
    return pd.DataFrame(columns=['Timestamp', 'Type', 'Category', 'Detail', 'Amount', 'Balance'])

def save_data(df):
    df_to_save = df.copy()
    # แปลงเวลากลับเป็นตัวหนังสือเพื่อบันทึกลง CSV
    df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime("%d/%m/%Y %H:%M")
    df_to_save.to_csv(FILE_NAME, index=False)

# --- ระบบล็อคแอป (Session State) ---
if 'auth_active' not in st.session_state:
    st.session_state.auth_active = False

if not st.session_state.auth_active:
    st.title("🏦 Suppawit Private Bank")
    st.write("🔒 กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน")
    pwd_input = st.text_input("รหัสผ่าน", type="password")
    if st.button("ตกลง"):
        if pwd_input == USER_PASSWORD:
            st.session_state.auth_active = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- เริ่มต้นหน้าแอปหลัก ---
st.set_page_config(page_title="My Digital Bank", layout="wide")
data = load_data()

# คำนวณยอดเงินล่าสุด
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.title("🏦 Suppawit Private Bank")
st.sidebar.button("🔒 ล็อกแอป", on_click=lambda: st.session_state.update({"auth_active": False}))

# แสดงยอดเงินปัจจุบันแบบเด่นๆ
st.metric(label="ยอดเงินคงเหลือปัจจุบัน", value=f"{current_balance:,.2f} THB")

tab1, tab2 = st.tabs(["💰 ทำรายการ ฝาก-ถอน", "📈 กราฟและประวัติ"])

with tab1:
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_type = st.radio("ประเภทรายการ", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
            t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "เงินโอน", "อื่นๆ"])
        with col2:
            t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0)
            t_note = st.text_input("บันทึกเพิ่มเติม")
        
        if st.form_submit_button("ยืนยันบันทึกรายการ"):
            final_amt = t_amt if t_type == "ฝากเงิน" else -t_amt
            new_balance = current_balance + final_amt
            
            # สร้างข้อมูลใหม่
            new_record = pd.DataFrame([{
                'Timestamp': datetime.now(),
                'Type': t_type, 
                'Category': t_cat, 
                'Detail': t_note,
                'Amount': final_amt, 
                'Balance': new_balance
            }])
            
            # เอาข้อมูลใหม่วางบนสุด (Concat)
            data = pd.concat([new_record, data], ignore_index=True)
            save_data(data)
            st.success(f"บันทึก {t_type} เรียบร้อยแล้ว!")
            st.rerun()

with tab2:
    # --- ส่วนแสดงกราฟ ---
    st.subheader("📈 แนวโน้มยอดเงิน (กราฟ)")
    if not data.empty:
        # เรียงข้อมูลตามเวลาจากเก่าไปใหม่เพื่อวาดกราฟ
        chart_df = data.sort_values('Timestamp')
        fig = px.line(chart_df, x='Timestamp', y='Balance', markers=True, 
                      labels={'Balance': 'ยอดเงินคงเหลือ', 'Timestamp': 'วันที่/เวลา'},
                      title="เส้นทางการเติบโตของเงิน")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลสำหรับวาดกราฟ")

    st.divider()

    # --- ส่วนตารางประวัติ ---
    st.subheader("📜 สมุดบัญชีย้อนหลัง")
    st.dataframe(data, use_container_width=True)

    # --- ส่วนปุ่มลบข้อมูล ---
    st.write("---")
    if st.button("❌ ลบรายการล่าสุด (แก้ไขกรณีพิมพ์ผิด)"):
        if not data.empty:
            data = data.drop(data.index[0])
            save_data(data)
            st.warning("ลบรายการล่าสุดออกแล้ว ยอดเงินถูกรีเซ็ตกลับไปก่อนหน้า")
            st.rerun()
        else:
            st.error("ไม่มีข้อมูลเหลือให้ลบ")
