import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- การตั้งค่าเบื้องต้น ---
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346"  # คุณสามารถเปลี่ยนรหัสผ่านตรงนี้ได้

def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=['Timestamp', 'Type', 'Category', 'Detail', 'Amount', 'Balance'])

def save_data(df):
    df.to_csv(FILE_NAME, index=False)

# --- ระบบ Login ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Suppawit Private Bank")
    pwd = st.text_input("กรุณาใส่รหัสผ่านเพื่อเข้าใช้งาน", type="password")
    if st.button("เข้าสู่ระบบ"):
        if pwd == USER_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- หน้าหลักแอป (หลัง Login) ---
st.set_page_config(page_title="My Digital Bank", layout="wide")
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

# ส่วนแสดงผลยอดเงิน (Header)
st.title("🏦 My Digital Bank")
col_bal1, col_bal2 = st.columns(2)
with col_bal1:
    st.metric("ยอดเงินในบัญชีทั้งหมด", f"{current_balance:,.2f} THB")
with col_bal2:
    # คำนวณยอดออมรายเดือน (ตัวอย่าง)
    st.metric("สถานะบัญชี", "ปกติ (Active)")

# --- เมนูธนาคาร ---
st.divider()
menu = st.sidebar.radio("เมนูใช้งาน", ["หน้าหลัก & ฝาก-ถอน", "สมุดบัญชี (Statement)", "ตั้งค่า"])

if menu == "หน้าหลัก & ฝาก-ถอน":
    tab1, tab2 = st.tabs(["📥 ฝากเงิน / รายรับ", "📤 ถอนเงิน / รายจ่าย / DCA"])
    
    with tab1:
        with st.form("dep_form", clear_on_submit=True):
            cat = st.selectbox("หมวดหมู่รายรับ", ["เงินเดือน", "โอนเข้า", "เงินปันผลหุ้น", "อื่นๆ"])
            detail = st.text_input("บันทึกเพิ่มเติม")
            amt = st.number_input("จำนวนเงินฝาก", min_value=0.0)
            if st.form_submit_button("ยืนยันการฝาก"):
                new_balance = current_balance + amt
                new_record = pd.DataFrame([{
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Type': 'Deposit', 'Category': cat, 'Detail': detail, 
                    'Amount': amt, 'Balance': new_balance
                }])
                data = pd.concat([new_record, data], ignore_index=True)
                save_data(data)
                st.success("ฝากเงินสำเร็จ!")
                st.rerun()

    with tab2:
        with st.form("with_form", clear_on_submit=True):
            cat = st.selectbox("หมวดหมู่รายจ่าย", ["ค่าอาหาร", "เดินทาง", "DCA (หุ้น/ETF)", "ช้อปปิ้ง", "อื่นๆ"])
            detail = st.text_input("บันทึกเพิ่มเติม (เช่น ซื้อ JEPQ)")
            amt = st.number_input("จำนวนเงินถอน", min_value=0.0)
            if st.form_submit_button("ยืนยันการถอน"):
                if amt <= current_balance:
                    new_balance = current_balance - amt
                    new_record = pd.DataFrame([{
                        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Type': 'Withdraw', 'Category': cat, 'Detail': detail, 
                        'Amount': -amt, 'Balance': new_balance
                    }])
                    data = pd.concat([new_record, data], ignore_index=True)
                    save_data(data)
                    st.warning("ดำเนินการเรียบร้อย!")
                    st.rerun()
                else:
                    st.error("ยอดเงินไม่เพียงพอ!")

elif menu == "สมุดบัญชี (Statement)":
    st.header("📜 รายงานเดินบัญชี (Statement)")
    st.dataframe(data, use_container_width=True)
    
    # ปุ่มดาวน์โหลดไฟล์ Excel
    csv = data.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 ดาวน์โหลด Statement (CSV)", csv, "statement.csv", "text/csv")

elif menu == "ตั้งค่า":
    if st.button("ออกจากระบบ"):
        st.session_state.logged_in = False
        st.rerun()
