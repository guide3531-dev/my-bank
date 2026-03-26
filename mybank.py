import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- ตั้งค่าเบื้องต้น ---
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "250346" # ใส่รหัสเดิมของคุณตรงนี้

# ฟังก์ชันจัดการความจำการ Login
if 'auth_success' not in st.session_state:
    st.session_state.auth_success = False

def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=['Timestamp', 'Type', 'Category', 'Detail', 'Amount', 'Balance'])

def save_data(df):
    # คำนวณยอดคงเหลือใหม่ทุกครั้งที่มีการลบ เพื่อให้ยอดเงินถูกต้องเสมอ
    if not df.empty:
        df = df.sort_values(by='Timestamp', ascending=True)
        temp_balance = 0
        new_balances = []
        for amt in df['Amount']:
            temp_balance += amt
            new_balances.append(temp_balance)
        df['Balance'] = new_balances
        df = df.sort_values(by='Timestamp', ascending=False)
    df.to_csv(FILE_NAME, index=False)
    return df

# --- ระบบ Login (เหมือนเดิม) ---
if not st.session_state.auth_success:
    st.title("🏦 Suppawit Private Bank")
    pwd = st.text_input("รหัสผ่าน", type="password")
    if st.button("ตกลon"):
        if pwd == USER_PASSWORD:
            st.session_state.auth_success = True
            st.rerun()
        else:
            st.error("รหัสไม่ถูกต้อง")
    st.stop()

# --- หน้าหลักแอป ---
st.set_page_config(page_title="My Digital Bank", layout="wide")
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.title("🏦 Suppawit Private Bank")
st.metric("ยอดเงินปัจจุบัน", f"{current_balance:,.2f} THB")

tab1, tab2 = st.tabs(["💰 ทำรายการ", "📜 ประวัติและลบข้อมูล"])

with tab1:
    with st.form("bank_form", clear_on_submit=True):
        type = st.radio("ประเภท", ["ฝากเงิน", "ถอนเงิน/รายจ่าย"])
        cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "โอนเข้า", "อื่นๆ"])
        amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
        note = st.text_input("บันทึก")
        if st.form_submit_button("บันทึก"):
            final_amt = amt if type == "ฝากเงิน" else -amt
            new_balance = current_balance + final_amt
            new_record = pd.DataFrame([{
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Type': type, 'Category': cat, 'Detail': note,
                'Amount': final_amt, 'Balance': new_balance
            }])
            data = pd.concat([new_record, data], ignore_index=True)
            save_data(data)
            st.success("สำเร็จ!")
            st.rerun()

with tab2:
    if not data.empty:
        st.subheader("📊 กราฟเงินคงเหลือ")
        chart_df = data.sort_values('Timestamp')
        fig = px.line(chart_df, x='Timestamp', y='Balance', markers=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📜 รายการทั้งหมด")
        st.dataframe(data, use_container_width=True)

        st.divider()
        st.subheader("🗑️ เลือกรายการที่ต้องการลบ")
        
        # สร้างรายการให้เลือก (เอา Timestamp + ประเภท + จำนวนเงิน มาโชว์)
        data['select_label'] = data['Timestamp'] + " | " + data['Type'] + " | " + data['Amount'].astype(str) + " บาท"
        options = data['select_label'].tolist()
        selected_to_delete = st.multiselect("เลือกรายการที่พิมพ์ผิด (เลือกได้หลายรายการ)", options)

        if st.button("❌ ยืนยันลบรายการที่เลือก"):
            if selected_to_delete:
                # กรองเอาเฉพาะรายการที่ "ไม่ได้ถูกเลือก" เก็บไว้
                data = data[~data['select_label'].isin(selected_to_delete)]
                data = data.drop(columns=['select_label'])
                data = save_data(data) # บันทึกและคำนวณยอดเงินใหม่
                st.warning(f"ลบไปแล้ว {len(selected_to_delete)} รายการ")
                st.rerun()
            else:
                st.info("กรุณาเลือกรายการก่อนกดลบ")
    else:
        st.info("ยังไม่มีข้อมูล")

if st.sidebar.button("🔒 ล็อกแอป"):
    st.session_state.auth_success = False
    st.rerun()
