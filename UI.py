import streamlit as st
import base64
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model")
ASSET_PATH = os.path.join(BASE_DIR, "asset") 

sys.path.append(MODEL_PATH)
sys.path.append(BASE_DIR)
sys.path.append(ASSET_PATH)
# --- 1. SETUP IMAGE PATH ---
background_image_path = os.path.join(ASSET_PATH, "Wallpaper.png")

# --- 2. CONFIGURATION ---
# เปลี่ยนเป็น wide เพื่อให้มีพื้นที่ด้านข้างมากขึ้น
st.set_page_config(page_title="User Info App", layout="wide") 

# --- 3. IMAGE LOADING & CSS ---
# --- 3. IMAGE LOADING & CSS ---
def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

bin_str = get_base64(background_image_path)

if bin_str:
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* === 🚫 โค้ดสำหรับซ่อน Sidebar และปุ่มเมนูมุมซ้ายบน === */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    
    /* ควบคุมขนาดและข้อความของหัวเรื่อง (Title) */
    h1 {{
        color: #000000 !important; 
        text-align: center;
        margin-bottom: 30px; 
        white-space: nowrap; 
        font-size: 2.5rem !important; 
    }}
    
    h1 a {{
        display: none !important;
    }}

    .stTextInput label p, .stNumberInput label p, .stSelectbox label p {{
        color: #000000 !important;
        font-weight: bold;
        font-size: 1.1rem; 
    }}
    
    /* จัดหน้าให้เนื้อหาอยู่ตรงกลางแต่มีความกว้างมากขึ้น */
    .block-container {{
        padding-top: 5rem;
        max-width: 900px !important; 
    }}

    /* === ⬛ Black Button Styling (Continue) === */
    .stButton > button {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000 !important;
        border-radius: 8px; 
    }}

    .stButton > button:hover {{
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border-color: #333333 !important;
    }}

    /* === ⬛ Black Input Boxes & White Text === */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {{
        background-color: #000000 !important;
        border: 1px solid #555555 !important;
    }}

    div[data-baseweb="input"] input {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important; 
    }}

    div[data-baseweb="select"] div, 
    div[data-baseweb="select"] span {{
        color: #FFFFFF !important;
    }}

    div[data-baseweb="input"] svg,
    div[data-baseweb="select"] svg {{
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }}

    /* === ⬛ Minus and Plus Buttons === */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"] {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }}

    button[data-testid="stNumberInputStepDown"]:hover,
    button[data-testid="stNumberInputStepUp"]:hover {{
        background-color: #333333 !important;
    }}

    /* === ⬛ Dropdown Menu (Gender Selectbox Popover) === */
    div[data-baseweb="popover"] > div {{
        background-color: #000000 !important;
    }}

    ul[role="listbox"] {{
        background-color: #000000 !important;
    }}

    li[role="option"] {{
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }}

    li[role="option"]:hover {{
        background-color: #333333 !important;
    }}
    
    li[role="option"][aria-selected="true"] {{
        color: #FFFFFF !important;
        background-color: #222222 !important; 
    }}
    </style>
    """
else:
    st.warning(f"⚠️ Image not found at: {background_image_path}")
    page_bg_img = ""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- 4. THE MAIN UI ---

st.title("Fall Risk Assessment System for Older People")

st.write("") # เว้นบรรทัดนิดนึง

# ปรับ Layout ให้สมดุลขึ้น
col1, col_space, col2 = st.columns([1, 0.1, 1])

with col1:
    st.text_input("User", placeholder="Enter name", key="user_name_input")
    st.number_input("Age", min_value=0, step=1, key="age_input")
    st.number_input("Weight (kg)", min_value=0.0, format="%.2f", key="weight_input")

with col2:
    st.selectbox("Gender", ["Male", "Female", "Other"], key="gender_input")
    st.number_input("Height (cm)", min_value=0.0, format="%.2f", key="height_input")
    
    # เพิ่มช่องว่างหลอกเพื่อให้ฟอร์มสองฝั่งดูความสูงเท่ากัน (เพราะฝั่งซ้ายมี 3 ฝั่งขวามี 2)
    st.write("")
    st.write("")
    st.write("")

st.write("") 
st.write("")

# สร้างปุ่มเพื่อไปหน้าถัดไป
if st.button("Continue", use_container_width=True):
    # ตรวจสอบว่ากรอกชื่อหรือยัง (Optional)
    if st.session_state.user_name_input:
        # บังคับ Copy ค่าจาก Widget keys ไปใส่ Session State หลัก
        st.session_state['user_name'] = st.session_state.user_name_input
        st.session_state['age'] = st.session_state.age_input
        st.session_state['gender'] = st.session_state.gender_input
        st.session_state['weight'] = st.session_state.weight_input
        st.session_state['height'] = st.session_state.height_input
        
        # ย้ายไปหน้า app.py (ตรวจสอบชื่อไฟล์ในโฟลเดอร์ pages ของคุณด้วยนะครับ)
        st.switch_page("pages/app.py")
    else:
        st.error("Please enter your name before continuing.")

# cmd conda activate CapstonePrototype && cd C:\Users\macma\Downloads\CapstonePrototype && streamlit run UI.py
# Terminal conda activate CapstonePrototype_v9 ; cd C:\Users\macma\Downloads\CapstonePrototype ; streamlit run UI.py