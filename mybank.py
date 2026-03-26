import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone
import plotly.express as px
import yfinance as yf

# --- 1. การตั้งค่าพื้นฐานและธีม ---
st.set_page_config(page_title="Suppawit Portfolio Pro", layout="wide")
FILE_NAME = 'bank_database.csv'
USER_PASSWORD = "your_password" # <--- อย่าลืมเปลี่ยนเป็นรหัสของคุณ

# CSS สำหรับปรับแต่งธีม (น้ำเงิน-ดำ-เงิน)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 8px; border: none; }
    .stMetric { background-color: #161B22; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161B22; border-radius: 5px 5px 0 0; padding: 10px 20px; }
    .profit { color: #00FFA3; font-weight: bold; }
    .loss { color: #FF4B4B; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ฟังก์ชันจัดการข้อมูลและเวลา ---
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

# ฟังก์ชันดึงราคาหุ้น Real-time
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.fast_info
        last_price = info['last_price']
        prev_close = info['previous_close']
        change = ((last_price - prev_close) / prev_close) * 100
        return last_price, change
    except:
        return None, None

# --- 3. ระบบล็อคแอป ---
if 'auth_active' not in st.session_state:
    st.session_state.auth_active = False

if not st.session_state.auth_active:
    st.title("🏦 Suppawit Portfolio Pro")
    pwd_input = st.text_input("กรุณาใส่รหัสผ่าน", type="password")
    if st.button("Log In"):
        if pwd_input == USER_PASSWORD:
            st.session_state.auth_active = True
            st.rerun()
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")
    st.stop()

# --- 4. หน้าหลักแอป ---
data = load_data()
current_balance = data.iloc[0]['Balance'] if not data.empty else 0.0

st.title("💎 Suppawit Investment Dashboard")
st.sidebar.button("🔒 ล็อกแอป", on_click=lambda: st.session_state.update({"auth_active": False}))

# แสดง Dashboard ยอดเงิน
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("เงินสดคงเหลือ", f"{current_balance:,.2f} THB")
with col_m2:
    dca_total = data[data['Category'] == 'DCA หุ้น']['Amount'].abs().sum() if not data.empty else 0
    st.metric("เงินลงทุนสะสม (DCA)", f"{dca_total:,.2f} THB")

tab1, tab2, tab3 = st.tabs(["💵 บันทึกรายการ", "📊 พอร์ตลงทุน (Real-time)", "🧮 เครื่องคิดเลข DCA"])

# --- Tab 1: การจัดการเงิน ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        t_type = st.radio("ประเภท", ["ฝากเงิน", "ถอน/จ่าย/ลงทุน"])
        t_cat = st.selectbox("หมวดหมู่", ["เงินเดือน", "DCA หุ้น", "ค่ากิน", "โอนเข้า", "อื่นๆ"])
        t_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0)
        t_note = st.text_input("ชื่อหุ้น/กองทุนที่ซื้อ หรือ บันทึก")
        
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

    st.divider()
    st.subheader("📜 ประวัติรายการทั้งหมด")
    st.dataframe(data, use_container_width=True)
    if st.button("❌ ลบรายการล่าสุด"):
        if not data.empty:
            data = data.drop(data.index[0]); save_data(data); st.rerun()

# --- Tab 2: พอร์ตลงทุน Real-time ---
with tab2:
    st.subheader("📈 พอร์ตลงทุนของคุณ (Real-time)")
    
    # ดึงข้อมูลรายการ DCA เพื่อสร้างตารางพอร์ต
    dca_data = data[data['Category'] == 'DCA หุ้น']
    if not dca_data.empty:
        # แยกชื่อหุ้นจาก Detail และคำนวณจำนวนหุ้น/ราคาเฉลี่ย
        # (สมมติว่า Detail เก็บชื่อหุ้นในรูปแบบ "ซื้อ PTT.BK 100 หุ้น @ 35.0")
        portfolio = pd.DataFrame()
        for stock_name, stock_df in dca_data.groupby('Detail'):
            total_cost = stock_df['Amount'].abs().sum()
            # ลองหาข้อมูลจำนวนหุ้นจากบันทึก (สมมติว่าระบุไว้)
            # ถ้าไม่ระบุ จะคำนวณจำนวนหุ้นเป็น 0 และราคาเฉลี่ยเป็น 0
            shares = 0
            if 'หุ้น @' in stock_name:
                try: shares = float(stock_name.split(' ')[-3])
                except: pass
            
            avg_cost = total_cost / shares if shares > 0 else 0
            
            # ดึงราคา Real-time
            # (ต้องแน่ใจว่าบันทึก Detail มีชื่อหุ้นที่ yfinance รู้จัก เช่น "PTT.BK")
            current_price = None
            if shares > 0:
                current_price, _ = get_stock_price(stock_name.split(' ')[1])
            
            market_value = current_price * shares if current_price else 0
            profit_loss = market_value - total_cost
            p_l_percent = (profit_loss / total_cost) * 100 if total_cost > 0 else 0
            
            new_stock_df = pd.DataFrame([{
                'หุ้น/กองทุน': stock_name,
                'จำนวนหุ้น': shares,
                'ราคาเฉลี่ย': avg_cost,
                'ราคาปัจจุบัน': current_price,
                'มูลค่าตลาด': market_value,
                'กำไร/ขาดทุน': profit_loss,
                'กำไร/ขาดทุน (%)': p_l_percent
            }])
            portfolio = pd.concat([portfolio, new_stock_df], ignore_index=True)
            
        st.dataframe(portfolio, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลลงทุนสะสม (DCA)")
    
    st.divider()
    st.subheader("📊 กราฟพอร์ตลงทุน (มูลค่าตลาด)")
    if not portfolio.empty:
        fig_pie = px.pie(portfolio, values='มูลค่าตลาด', names='หุ้น/กองทุน', template="plotly_dark", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลพอร์ตลงทุนสำหรับวาดกราฟ")

# --- Tab 3: DCA Calculator ---
with tab3:
    st.subheader("🧮 เครื่องคิดเลขวางแผนเศรษฐี (Compound Interest)")
    # (โค้ดส่วนเครื่องคิดเลขเหมือนเดิม) ...
