import streamlit as st
import cv2
import sys
import os
import base64
import pandas as pd 
from datetime import datetime
import altair as alt
import plotly.graph_objects as go
import time

# --- 1. IMPROVED STORAGE FUNCTION ---
def save_to_csv(stats):
    file_path = "user_data_log.csv"
    
    # กำหนดโครงสร้างข้อมูลใหม่ให้รองรับทุกโมเดล
    new_data = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": st.session_state.get("user_name", "Unknown"),
        "Age": st.session_state.get("age", 0),
        "Weight": st.session_state.get("weight", 0.0),
        "Height": st.session_state.get("height", 0.0),
        "Gender": st.session_state.get("gender", "Unknown"),
        
        # ข้อมูลคอลัมน์ใหม่
        "Test_Type": stats.get("test_type", "-"),
        "Time_Taken_Sec": round(stats.get("time", 0), 3) if stats.get("time") else "-",
        
        # ข้อมูล Sit-to-Stand
        "Target_Reps": stats.get("target", "-"),
        "Completed_Reps": stats.get("reps", "-"),
        
        # ข้อมูล Gait Speed
        "Speed_ms": round(stats.get("speed_ms", 0), 2) if stats.get("speed_ms") else "-",
        "Distance_m": stats.get("distance_m", "-"),
        
        # ข้อมูล Balance Test
        "Balance_Result": stats.get("balance_result", "-"),
        "Fail_Reason": stats.get("fail_reason", "-")
    }
    
    df = pd.DataFrame([new_data])
    
    # ตรวจสอบไฟล์และเขียนข้อมูล (Append)
    if os.path.isfile(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, mode='w', header=True, index=False)

# --- DYNAMIC IMPORT & PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model")
ASSET_PATH = os.path.join(BASE_DIR, "asset")
GAME_PATH = os.path.join(BASE_DIR, "game")
sys.path.append(MODEL_PATH)
sys.path.append(BASE_DIR)
sys.path.append(ASSET_PATH)
sys.path.append(GAME_PATH)


# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Select Model", layout="wide")

# --- 2. BACKGROUND IMAGE ---
background_image_path = os.path.join(ASSET_PATH, "Wallpaper.png")

def get_base64(bin_file):
    if not os.path.exists(bin_file):
        return None
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

bin_str = get_base64(background_image_path)

if bin_str:
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Fix for better readability on dark/light backgrounds */
    h1, h2, h3, p {{
        color: #000000 !important;
    }}
    /* Optional: Make the sidebar slightly transparent or solid */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.9);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
else:
    # Diagnostic message if it still fails
    st.sidebar.error(f"⚠️ File not found: {background_image_path}")



# --- 3. STATE MANAGEMENT ---
# This remembers which button you clicked
if 'selected_model' not in st.session_state:
    st.session_state['selected_model'] = None

# Camera index state (default: 0 = built-in webcam)
if 'cam_index' not in st.session_state:
    st.session_state['cam_index'] = 0


# --- 4. THE SIDEBAR (Left Side Menu) ---

st.markdown("""
    <style>
        /* Change the main sidebar background to black */
        [data-testid="stSidebar"], [data-testid="stSidebarHeader"] {
            background-color: #000000 !important;
        }

        /* Force text colors to white */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #ffffff !important;
        }

        /* --- Global Button Styling (Sidebar + Main Page) --- */
        [data-testid="stSidebar"] button, 
        div.stButton > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 1px solid #444444 !important;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        /* Ensure text stays white */
        [data-testid="stSidebar"] button p,
        div.stButton > button p,
        div.stButton > button span {
            color: #ffffff !important;
        }

        div.stButton > button:focus, div.stButton > button:active {
            box-shadow: none !important;
            outline: none !important;
        }

        /* =========================================================
           --- NEW FIX: Camera Toggle Buttons (Green/Red) --- 
           ========================================================= */
           
        /* If there's a cam-on span, make the next button Green */
        div:has(span.cam-on) + div button {
            background-color: #28a745 !important;
            border-color: #1e7e34 !important;
        }

        /* If there's a cam-off span, make the next button Red */
        div:has(span.cam-off) + div button {
            background-color: #dc3545 !important;
            border-color: #bd2130 !important;
        }

        /* Hover effect for the camera toggles */
        div:has(span.cam-on) + div button:hover, 
        div:has(span.cam-off) + div button:hover {
            opacity: 0.8 !important;
            border-color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Models")
    
    if st.button("🏋️ Sit-to-Stand", use_container_width=True):
        st.session_state['selected_model'] = "sit_to_stand"
        
    if st.button("🚶 Gait Speed", use_container_width=True):
        st.session_state['selected_model'] = "Gait_Speed"
        
    if st.button("🧍Balance Test", use_container_width=True):
        st.session_state['selected_model'] = "BalanceTest"
        
    st.header("Games")
    
    if st.button("🎮 Pose Matching Game", use_container_width=True):
        st.session_state['selected_model'] = "Game_1"

    st.divider()

    # --- Camera Selection ---
    st.header("📷 Camera")
    col_cam0, col_cam1 = st.columns(2)
    with col_cam0:
        # Highlight the active camera button with a border style via markdown
        label_0 = "✅ Default" if st.session_state['cam_index'] == 0 else "Default"
        if st.button(label_0, use_container_width=True, key="btn_cam0"):
            st.session_state['cam_index'] = 0
            st.rerun()
    with col_cam1:
        label_1 = "✅ External" if st.session_state['cam_index'] == 1 else "External"
        if st.button(label_1, use_container_width=True, key="btn_cam1"):
            st.session_state['cam_index'] = 1
            st.rerun()
    st.caption(f"Active: {'Default webcam (0)' if st.session_state['cam_index'] == 0 else 'External cam (1)'}")

    st.divider()
    
    # === เพิ่มเมนู History แยกออกมา ===
    if st.button("History", use_container_width=True):
        st.session_state['selected_model'] = "history"

    st.divider()
    if st.button("About", use_container_width=True):
        st.session_state['selected_model'] = "about"
        
    st.divider()
    
    if st.button("🔙 Go Back to Home", use_container_width=True):
        st.switch_page("UI.py")

# Resolve camera index once for use throughout the page
cam = st.session_state['cam_index']

# Scenario A: Nothing selected yet
# --- 5. THE MAIN AREA (Right Side) ---

if st.session_state['selected_model'] is None:
    st.title("Please Select Model")
    if "user_name" in st.session_state:
        st.info(f"Welcome, {st.session_state.user_name}! 👈 Click a button on the left to load an AI model.")

# Scenario B: Sit-to-Stand is selected
elif st.session_state['selected_model'] == "sit_to_stand":
    from sit_to_stand_test import SitToStand
    st.title("🏋️ Sit-to-Stand AI Assessment")

    # --- 1. เตรียมตัวแปร State สำหรับควบคุมหน้าจอ ---
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False 
    if 'data_saved' not in st.session_state:
        st.session_state.data_saved = False
    if 'saved_target_reps' not in st.session_state:
        st.session_state.saved_target_reps = 5 #Defualt เริ่มต้น

    # ==========================================
    # ส่วนที่ 1: หน้าจอตอนกำลังทดสอบ (กล้องทำงาน)
    # ==========================================
    if not st.session_state.show_results:
        col1, col2 = st.columns(2)
        with col1:
            target_reps = 5
            st.info("Target Reps: **5**")
            
        with col2:
            st.write("") 
            
            # Initialize state if it doesn't exist
            if 'run_camera' not in st.session_state:
                st.session_state.run_camera = False

            # Inject the invisible marker AND set the label
            if st.session_state.run_camera:
                st.markdown('<span class="cam-on"></span>', unsafe_allow_html=True)
                btn_label = "📷 Camera: ON"
            else:
                st.markdown('<span class="cam-off"></span>', unsafe_allow_html=True)
                btn_label = "🚫 Camera: OFF"

            # Create the button (it will automatically catch the CSS from the span above it)
            if st.button(btn_label, use_container_width=True, key="cam_toggle"):
                st.session_state.run_camera = not st.session_state.run_camera
                st.rerun()

            run_camera = st.session_state.run_camera
        
        if 'processor' not in st.session_state:
            st.session_state.processor = SitToStand(target_reps=target_reps)
        st.session_state.processor.target_reps = target_reps

        col_video, col_stats = st.columns([3, 1])
        
        with col_stats:
            st.subheader("Live Stats")
            status_indicator = st.empty()
            metric_reps = st.empty()
            metric_time = st.empty()

        with col_video:
            frame_placeholder = st.empty()

        if run_camera:
            cap = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)  
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 900) 
            cap.set(cv2.CAP_PROP_FPS, 30)
            while cap.isOpened() and run_camera:
                ret, frame = cap.read()
                if not ret: break
                
                processed_image, stats = st.session_state.processor.process_frame(frame)
                frame_placeholder.image(processed_image, channels="RGB", use_container_width=True)
                
                state_color = "green" if stats["state"] == "standing" else "red" if stats["state"] == "sitting" else "blue"
                status_indicator.markdown(f"**State:** :{state_color}[{stats['state'].upper()}]")
                metric_reps.metric("Repetitions", f"{stats['reps']} / {stats['target']}")
                metric_time.metric("Time Elapsed", f"{stats['time']:.1f}s")

                # === เช็คว่าทำเสร็จหรือยัง ===
                if stats["state"] == "finished":
                    if not st.session_state.data_saved:
                        stats["test_type"] = "Sit-to-Stand" # ระบุประเภทก่อนเซฟ
                        save_to_csv(stats) 
                        st.session_state.data_saved = True
                        st.session_state.final_time = stats["time"] 
                        # --- เก็บข้อมูลเวลาแต่ละครั้งลง Session State ---
                        st.session_state.rep_times = stats.get("rep_times", []) 
                        
                        st.session_state.show_results = True
                        
                        cap.release() 
                        st.rerun() 
                        break
            cap.release()
        else:
            if st.session_state.get("show_results", False):
                frame_placeholder.empty() 
            else:
                frame_placeholder.info("Check 'Start Camera' to begin.")
                
            st.session_state.data_saved = False
            if 'processor' in st.session_state:
                st.session_state.processor.reset()

    # ส่วนที่ 2: หน้าจอ Result (แสดงเวลา, กราฟ และ History)
    # ==========================================
    else:
        st.success("🎉 Finish !")
        st.metric("⏱️ Total time", f"{st.session_state.final_time:.2f} s")
        total_time = st.session_state.final_time
        
        # --- 📊 ประเมินความเสี่ยง (ประเมินเฉพาะกรณีที่ตั้งเป้าหมาย 5 ครั้ง) ---
        # --- 📊 ประเมินความเสี่ยง (ประเมินเฉพาะกรณีที่ตั้งเป้าหมาย 5 ครั้ง) ---
        if st.session_state.processor.target_reps == 5:
            if total_time <= 11.19:
                st.success("4 คะแนน | ความแข็งแรงกล้ามเนื้อขาดีมาก / ความเสี่ยงหกล้มต่ำ")
            elif total_time <= 13.69:
                st.info("3 คะแนน | ความแข็งแรงกล้ามเนื้อขาดี / ความเสี่ยงหกล้มปานกลาง")
            elif total_time <= 16.69:
                st.warning("2 คะแนน | ความแข็งแรงเริ่มลดลง / เริ่มมีความเสี่ยงในการหกล้ม")
                st.info("**💡 Actionable Advice:**\nกล้ามเนื้อขาเริ่มมีสัญญาณอ่อนแรง ควรเริ่มบริหารกล้ามเนื้อต้นขาอย่างค่อยเป็นค่อยไป และระมัดระวังการลุกหรือนั่งที่รวดเร็วเกินไปเพื่อป้องกันหน้ามืด")
            elif total_time <= 60.00:
                st.error("1 คะแนน | มีความเสี่ยงในการหกล้มสูง / ควรระมัดระวัง")
                st.info("**💡 Actionable Advice:**\nมีความเสี่ยงสูง แนะนำให้ปรึกษาแพทย์หรือนักกายภาพบำบัดเพื่อประเมินความแข็งแรงโดยละเอียด และควรปรับสภาพแวดล้อมในบ้านให้ปลอดภัย ")
            else:
                st.error("0 คะแนน | เสี่ยงหกล้มสูงมาก / ใช้เวลามากกว่า 60 วินาที หรือไม่สามารถทำได้")
                st.info("**💡 Actionable Advice:**\nมีความเสี่ยงสูงมากที่จะเกิดการหกล้ม โปรดใช้ความระมัดระวังอย่างมากในชีวิตประจำวัน ควรใช้อุปกรณ์ช่วยเดิน และแนะนำให้อยู่ในการดูแลของแพทย์หรือนักกายภาพบำบัดโดยเร็วที่สุด")
                
        else:
            st.info("💡หากต้องการดูผลประเมินความเสี่ยงและระดับคะแนน กรุณาตั้งค่า Target Reps เป็น 5 ครั้ง")
        # ==========================================
        # 📈 ส่วนสร้างกราฟ (Plot Graph)
        # ==========================================
        st.markdown("---")
        st.subheader("The graph shows the speed of each sit-up.")
        
        if hasattr(st.session_state, 'rep_times') and len(st.session_state.rep_times) > 0:
            times_data = [0.0] + st.session_state.rep_times
            reps_data = list(range(len(times_data)))
            
            df_chart = pd.DataFrame({
                "Time (s)": times_data,
                "Repetition": reps_data
            })
            
            # สร้างกราฟด้วย Altair เพื่อวาดเส้น+จุด และกำหนดสี
            chart = alt.Chart(df_chart).mark_line(
                color='#5677fc', # กำหนดสีเส้น
                point=alt.OverlayMarkDef(color='#5677fc', size=100, filled=True) # กำหนดให้มีจุดขนาดใหญ่
            ).encode(
                x=alt.X('Time (s)', title='Time'),
                y=alt.Y('Repetition', title='Repetition'),
                tooltip=['Repetition', 'Time (s)'] # ให้เอาเมาส์ชี้เพื่อดูค่าได้
            ).properties(
                height=350
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)

        # ==========================================
        # 3. ประวัตินับ 5 ครั้งล่าสุด
        # ==========================================
        st.markdown("---")
        st.subheader("History")
        
        try:
            df = pd.read_csv("user_data_log.csv")
            # โชว์ข้อมูลแค่ 5 รายการล่าสุด (.head(5))
            st.dataframe(df.iloc[::-1].head(5), hide_index=True, use_container_width=True)
        except FileNotFoundError:
            st.info("ยังไม่มีข้อมูลประวัติในระบบ")
            
        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Test again", use_container_width=True):
                
                st.session_state.show_results = False 
                st.session_state.data_saved = False
                
                st.session_state.run_camera = False 
                if 'processor' in st.session_state:
                    del st.session_state['processor']

                st.rerun() 
                
        with col_btn2:
            if st.button("History", use_container_width=True):
                st.session_state['selected_model'] = "history"
                st.rerun()  



# Scenario C: Model 2 is selected
elif st.session_state['selected_model'] == "Gait_Speed":
    from gaitspd_class import WalkSpeedApp
    st.title("🚶 Gait Speed AI Assessment")
    
    # --- จัดการ State สำหรับโชว์หน้า Result ---
    if 'show_gait_results' not in st.session_state:
        st.session_state.show_gait_results = False
    if 'saved_gait_distance' not in st.session_state:
        st.session_state.saved_gait_distance = 4.0  #Defualt เริ่มต้น

    # ------------------------------------------
    # 1. หน้าจอตอนกำลังทดสอบ (กล้องทำงาน)
    # ------------------------------------------
    if not st.session_state.show_gait_results:
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            # เปลี่ยนเป็น Input กรอกตัวเลขแทน Selectbox ตามที่คุณต้องการ
            test_dist = st.number_input("Walking Distance (meters)", min_value=0.1, value=4.0, step=0.1, format="%.2f")
        with col_ctrl2:
            st.write("") 
            
            if 'run_gait' not in st.session_state:
                st.session_state.run_gait = False

            if st.session_state.run_gait:
                st.markdown('<span class="cam-on"></span>', unsafe_allow_html=True)
                gait_label = "📷 Gait Cam: ON"
            else:
                st.markdown('<span class="cam-off"></span>', unsafe_allow_html=True)
                gait_label = "🚫 Gait Cam: OFF"

            if st.button(gait_label, use_container_width=True, key="gait_toggle"):
                st.session_state.run_gait = not st.session_state.run_gait
                st.rerun()

            # Assign to variable for your loop logic
            run_gait = st.session_state.run_gait

        if 'gait_processor' not in st.session_state:
            st.session_state.gait_processor = WalkSpeedApp(known_distance_m=test_dist)
        
        st.session_state.gait_processor.calibration.known_distance_m = test_dist

        col_video, col_metrics = st.columns([3, 1])
        
        with col_metrics:
            st.subheader("Live Data")
            m_speed = st.empty()
            m_time = st.empty()
            m_status = st.empty()

        with col_video:
            frame_placeholder = st.empty()

        if run_gait:
            cap = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)  
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 900) 
            while cap.isOpened() and run_gait:
                ret, frame = cap.read()
                if not ret: break
                
                processed_img, gait_stats = st.session_state.gait_processor.process_frame(frame)
                frame_placeholder.image(processed_img, channels="RGB", use_container_width=True)
                
                m_speed.metric("Speed", f"{gait_stats['speed']:.2f} m/s")
                m_time.metric("Time Elapsed", f"{gait_stats['time']:.2f} s")
                m_status.markdown(f"**Status:** {gait_stats['state'].upper()}")
                
                # เมื่อเดินเสร็จ
                if gait_stats['state'] == "finished":
                    # เก็บค่าลง Session State เพื่อนำไปโชว์หน้า Result
                    st.session_state.gait_final_speed = gait_stats['avg_speed']
                    st.session_state.gait_final_time = gait_stats['time']
                    st.session_state.gait_distance = test_dist
                    
                    # บันทึกข้อมูล Gait Speed ลง CSV ตามโครงสร้างใหม่
                    gait_stats_to_save = {
                        "test_type": "Gait Speed",
                        "time": gait_stats['time'],
                        "speed_ms": gait_stats['avg_speed'],
                        "distance_m": test_dist
                    }
                    save_to_csv(gait_stats_to_save)
                    
                    st.session_state.show_gait_results = True
                    cap.release()
                    st.rerun() 
                    break
                    
            cap.release()
        else:
            frame_placeholder.info("Please check 'Start Gait Camera' to begin. And stand outside the yellow lines.")
            if 'gait_processor' in st.session_state:
                st.session_state.gait_processor.reset_all()

    # ------------------------------------------
    # 2. หน้าจอแสดงผลลัพธ์การเดิน (Gait Speed Results)
    # ------------------------------------------
    else:
        st.success("🎉 Assessment Complete!")
        
        speed = st.session_state.gait_final_speed
        
        # --- ส่วนที่ 1: ตัวเลขสรุป (Core Metrics) ---
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("🚶 Average Speed", f"{speed:.2f} m/s")
        col_res2.metric("⏱️ Total Time", f"{st.session_state.gait_final_time:.2f} s")
        col_res3.metric("📏 Distance Walked", f"{st.session_state.gait_distance:.2f} m")
        
        st.markdown("---")
        
        # --- ส่วนที่ 2 & 3: กราฟหน้าปัด และ การแปรผล (Gauge Chart & Clinical Interpretation) ---
        col_gauge, col_text = st.columns([1, 1])
        
        with col_gauge:
            st.subheader("Speed Meter")
            # สร้าง Gauge Chart ด้วย Plotly
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = speed,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Gait Speed (m/s)"},
                gauge = {
                    'axis': {'range': [0, 2.0], 'tickwidth': 1, 'tickcolor': "black"},
                    'bar': {'color': "black", 'thickness': 0.25}, # สีเข็มชี้
                    'steps': [
                        {'range': [0, 0.8], 'color': "#ff4b4b"},     # แดง (High Risk)
                        {'range': [0.8, 1.0], 'color': "#faca2b"},   # เหลือง (At Risk)
                        {'range': [1.0, 2.0], 'color': "#00cc96"}    # เขียว (Normal)
                    ],
                }
            ))
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_text:
            st.subheader("📋 Assessment Result")
            st.write("")
            if speed < 0.8:
                st.error("🔴 **มีความเสี่ยงในการหกล้มสูง (High Risk)**\n\nความเร็วต่ำกว่า 0.8 m/s เข้าข่ายภาวะมวลกล้ามเนื้อน้อย (Sarcopenia)")
                st.info("**💡 Actionable Advice:**\nแนะนำให้ปรึกษาแพทย์หรือนักกายภาพบำบัดเพื่อประเมินความแข็งแรงของกล้ามเนื้อโดยละเอียด และระมัดระวังการเดินในพื้นที่ต่างระดับ")
            elif speed <= 1.0:
                st.warning("🟡 **อยู่ในเกณฑ์เฝ้าระวัง (At Risk)**\n\nความเร็ว 0.8 - 1.0 m/s กล้ามเนื้อขาเริ่มมีความแข็งแรงลดลง")
                st.info("**💡 Actionable Advice:**\nควรหมั่นออกกำลังกายเพื่อเพิ่มความแข็งแรงของกล้ามเนื้อขา เช่น การเดินเร็ว หรือทำท่า Sit-to-Stand เป็นประจำ")
            else:
                st.success("🟢 **ปกติ / ความเสี่ยงต่ำ (Normal)**\n\nความเร็วมากกว่า 1.0 m/s ความแข็งแรงและการทรงตัวอยู่ในเกณฑ์ดี")
                st.info("**💡 Actionable Advice:**\nยอดเยี่ยมครับ! แนะนำให้รักษาระดับความแข็งแรงนี้ไว้ด้วยการเดินออกกำลังกายหรือทำกิจกรรมที่มีการเคลื่อนไหวอย่างสม่ำเสมอ")

        st.markdown("---")
        
        # --- ส่วนที่ 4: Historical Trend Graph ---
        st.subheader("📈 Historical Trend (ประวัติความเร็วการเดิน)")
        try:
            df_history = pd.read_csv("user_data_log.csv")
            # กรองเอาเฉพาะข้อมูลการเดิน (ดูจาก Test_Type)
            df_gait_history = df_history[df_history["Test_Type"] == "Gait Speed"].copy()
            
            # ถ้าไม่มี Test_Type ใหม่ ให้ลองดึงข้อมูลเก่ามาแสดงไปก่อน
            if df_gait_history.empty:
                df_gait_history = df_history[df_history["Completed_Reps"] == 1].copy()
                if not df_gait_history.empty:
                    df_gait_history["Speed_ms"] = df_gait_history["Target_Reps"] / df_gait_history["Time_Taken_Sec"]

            if not df_gait_history.empty and len(df_gait_history) > 1:
                df_gait_history["Test_Count"] = range(1, len(df_gait_history) + 1)
                
                # แปลงให้ Speed_ms เป็นตัวเลขก่อนพล็อต
                df_gait_history['Speed_ms'] = pd.to_numeric(df_gait_history['Speed_ms'], errors='coerce')
                
                trend_chart = alt.Chart(df_gait_history).mark_line(
                    color='#ff7f0e',
                    point=alt.OverlayMarkDef(color='#ff7f0e', size=100, filled=True)
                ).encode(
                    x=alt.X('Test_Count:O', title='Test Session (ครั้งที่)'),
                    y=alt.Y('Speed_ms:Q', title='Speed (m/s)'),
                    tooltip=['Timestamp', 'Speed_ms']
                ).properties(height=300).interactive()
                
                st.altair_chart(trend_chart, use_container_width=True)
            else:
                st.info("📌 ทำการทดสอบ Gait Speed มากกว่า 1 ครั้ง เพื่อดูกราฟพัฒนาการความเร็วของคุณ")
        except FileNotFoundError:
            pass
            
        # --- ปุ่มควบคุมด้านล่าง ---
        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Test Again", use_container_width=True):
                st.session_state.show_gait_results = False 
                st.session_state.gait_processor.reset_all()
                st.rerun() 
        with col_btn2:
            if st.button("📂 Go to History", use_container_width=True):
                st.session_state['selected_model'] = "history"
                st.rerun()



# Scenario D: Balance Test is selected
elif st.session_state['selected_model'] == "BalanceTest":
    st.title("🧍 Balance Test AI Assessment")

    # --- Import BalanceTest class ---
    from balance_test import BalanceTest   

    # --- State initialization ---
    if 'show_balance_results' not in st.session_state:
        st.session_state.show_balance_results = False
    if 'balance_result' not in st.session_state:
        st.session_state.balance_result = ""
    if 'balance_hand_fail' not in st.session_state:
        st.session_state.balance_hand_fail = False
    if 'balance_hip_fail' not in st.session_state:
        st.session_state.balance_hip_fail = False

    # ==========================================
    # Part 1: Camera / Testing screen
    # ==========================================
    if not st.session_state.show_balance_results:

        col_ctrl1, col_ctrl2 = st.columns(2)

        with col_ctrl1:
            st.info(
                f"**Phase 1 — Calibration ({BalanceTest.CAL_T}s):** Stand still in your normal posture.\n\n"
                f"**Phase 2 — Testing ({BalanceTest.TEST_T}s):** Maintain the same posture. Any excess hand spread or hip tilt will be flagged."
            )

        with col_ctrl2:
            st.write("")

            if 'run_balance' not in st.session_state:
                st.session_state.run_balance = False

            if st.session_state.run_balance:
                st.markdown('<span class="cam-on"></span>', unsafe_allow_html=True)
                balance_label = "📷 Camera: ON"
            else:
                st.markdown('<span class="cam-off"></span>', unsafe_allow_html=True)
                balance_label = "🚫 Camera: OFF"

            if st.button(balance_label, use_container_width=True, key="balance_toggle"):
                st.session_state.run_balance = not st.session_state.run_balance
                # Reset processor on each new camera start
                if st.session_state.run_balance and 'balance_processor' in st.session_state:
                    del st.session_state['balance_processor']
                st.rerun()

            run_balance = st.session_state.run_balance

        # Instantiate processor once per session
        if 'balance_processor' not in st.session_state:
            st.session_state.balance_processor = BalanceTest()

        col_video, col_stats = st.columns([3, 1])

        with col_stats:
            st.subheader("Live Stats")
            metric_phase   = st.empty()
            metric_hand    = st.empty()
            metric_hip     = st.empty()
            metric_hand_st = st.empty()
            metric_hip_st  = st.empty()

        with col_video:
            frame_placeholder = st.empty()

        if run_balance:
            bt = st.session_state.balance_processor
            cap = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

            while cap.isOpened() and run_balance:
                ok, frame = cap.read()
                if not ok:
                    break

                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                import mediapipe as mp
                res = bt.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                now = time.time()
                hand = hip = None

                if res.pose_landmarks:
                    lm = res.pose_landmarks.landmark
                    bt.draw.draw_landmarks(
                        frame, res.pose_landmarks, bt.mp_pose.POSE_CONNECTIONS
                    )
                    hand, hip = bt.get_signals(lm, w, h)

                # Run the appropriate phase
                if bt.phase == "calibration":
                    bt.calibration_phase(frame, now, hand, hip)
                elif bt.phase == "testing":
                    bt.testing_phase(frame, now, hand, hip)
                else:
                    bt.done_phase(frame)

                # Display frame (BGR → RGB for Streamlit)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(frame_rgb, use_container_width=True)

                # --- Live sidebar metrics ---
                phase_colors = {"calibration": "🟡", "testing": "🟢", "done": "🔵"}
                metric_phase.markdown(
                    f"**Phase:** {phase_colors.get(bt.phase, '')} `{bt.phase.upper()}`"
                )

                if hand is not None and bt.hand_th is not None:
                    metric_hand.metric("Hand Distance", f"{hand:.1f}", f"/ {bt.hand_th:.1f}")
                if hip is not None and bt.hip_th is not None:
                    metric_hip.metric("Hip Angle", f"{hip:.1f}°", f"/ {bt.hip_th:.1f}°")

                if bt.phase in ("testing", "done"):
                    metric_hand_st.markdown(
                        f"**Hand:** {'🔴 FAIL' if bt.hand_fail else '🟢 OK'}"
                    )
                    metric_hip_st.markdown(
                        f"**Hip:** {'🔴 FAIL' if bt.hip_fail else '🟢 OK'}"
                    )

                # --- Test finished → save & switch to results ---
                if bt.phase == "done":
                    
                    # หาเหตุผลที่ตก (ถ้ามี)
                    reason = "-"
                    if bt.hand_fail and bt.hip_fail: reason = "Hand & Hip"
                    elif bt.hand_fail: reason = "Hand Spread"
                    elif bt.hip_fail: reason = "Hip Angle"
                    
                    balance_stats = {
                        "test_type": "Balance Test",
                        "time": BalanceTest.CAL_T + BalanceTest.TEST_T,
                        "balance_result": bt.result,
                        "fail_reason": reason
                    }
                    save_to_csv(balance_stats)

                    st.session_state.balance_result    = bt.result
                    st.session_state.balance_hand_fail = bt.hand_fail
                    st.session_state.balance_hip_fail  = bt.hip_fail
                    st.session_state.show_balance_results = True
                    st.session_state.run_balance = False

                    cap.release()
                    st.rerun()
                    break

            cap.release()

        else:
            frame_placeholder.info(
                "👈 Toggle the camera button to begin.\n\n"
                "Stand in front of the camera so your full body is visible."
            )
            # Reset processor when camera is turned off mid-session
            if 'balance_processor' in st.session_state:
                del st.session_state['balance_processor']

    # ==========================================
    # Part 2: Results screen
    # ==========================================
    else:
        result      = st.session_state.balance_result
        hand_fail   = st.session_state.balance_hand_fail
        hip_fail    = st.session_state.balance_hip_fail

        if result == "PASS":
            st.success("🎉 PASS — Balance within normal range!")
        else:
            st.error("❌ FAIL — Balance exceeded calibration baseline.")

        # Metric cards
        col_r1, col_r2 = st.columns(2)
        col_r1.metric("Hand Spread", "FAIL ❌" if hand_fail else "OK ✅")
        col_r2.metric("Hip Angle",   "FAIL ❌" if hip_fail  else "OK ✅")

        st.markdown("---")

        # Clinical interpretation
        st.subheader("📋 Assessment Result")
        if result == "PASS":
            st.success(
                "🟢 **ผลการทดสอบ: ปกติ**\n\n"
                "การทรงตัวและการควบคุมลำตัวอยู่ในเกณฑ์ปกติ "
                "ความเสี่ยงการหกล้มอยู่ในระดับต่ำ"
            )
            st.info(
                "**💡 Actionable Advice:**\n"
                "แนะนำให้รักษาระดับความแข็งแรงนี้ไว้ด้วยการออกกำลังกายสม่ำเสมอ "
                "เช่น โยคะ หรือการฝึกความสมดุล"
            )
        else:
            if hand_fail and hip_fail:
                st.error(
                    "🔴 **มีความเสี่ยงในการหกล้มสูง**\n\n"
                    "พบความผิดปกติทั้งการกางมือและมุมสะโพก "
                    "ซึ่งอาจบ่งชี้ถึงปัญหาการทรงตัวโดยรวม"
                )
            elif hand_fail:
                st.warning(
                    "🟡 **พบการชดเชยด้วยแขน (Hand Compensation)**\n\n"
                    "แขนกางออกเพื่อช่วยทรงตัว อาจบ่งชี้ถึง "
                    "ความแข็งแรงของแกนกลางลำตัวที่ลดลง"
                )
            else:
                st.warning(
                    "🟡 **พบการเอียงสะโพก (Hip Sway)**\n\n"
                    "มุมสะโพกเกินค่าปกติ อาจบ่งชี้ถึงปัญหา "
                    "การทรงตัวหรือความแข็งแรงของกล้ามเนื้อขา"
                )
            st.info(
                "**💡 Actionable Advice:**\n"
                "แนะนำให้ปรึกษานักกายภาพบำบัด และฝึกท่าเสริมความสมดุล "
                "เช่น Single-leg Stand หรือ Heel-to-Toe Walk"
            )

        # History table
        st.markdown("---")
        st.subheader("History")
        try:
            df = pd.read_csv("user_data_log.csv")
            # กรองให้แสดงเฉพาะประวัติของ Balance Test
            df_balance = df[df["Test_Type"] == "Balance Test"]
            
            # ถ้ามีข้อมูล Balance ให้แสดง ถ้าไม่มีให้แสดงตารางรวม
            if not df_balance.empty:
                st.dataframe(df_balance.iloc[::-1].head(5), hide_index=True, use_container_width=True)
            else:
                st.dataframe(df.iloc[::-1].head(5), hide_index=True, use_container_width=True)
        except FileNotFoundError:
            st.info("ยังไม่มีข้อมูลประวัติในระบบ")

        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Test Again", use_container_width=True):
                st.session_state.show_balance_results = False
                st.session_state.run_balance = False
                if 'balance_processor' in st.session_state:
                    del st.session_state['balance_processor']
                st.rerun()
        with col_btn2:
            if st.button("📂 Go to History", use_container_width=True):
                st.session_state['selected_model'] = "history"
                st.rerun()
    

# Scenario E: Game 1 is selected
elif st.session_state.get('selected_model') == "Game_1":
    from Game_1 import PoseMatcher
    st.title("🎮 Pose Matching Game")

    POSE_SECONDS = 5          # seconds per pose
    POSES_PATH   = os.path.join(BASE_DIR, "POSES")
    image_files  = sorted([f for f in os.listdir(POSES_PATH) if f.endswith(('.jpg', '.png'))])
    total_poses  = len(image_files)

    for k, v in {
        "pose_index":    0,
        "pose_scores":   [],   # list of per-pose best scores
        "pose_start":    None,
        "best_score":    0,    # best score seen in current pose window
        "game_over":     False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    def reset_game():
        st.session_state.update(
            pose_index=0, pose_scores=[], pose_start=None,
            best_score=0, game_over=False
        )

    # ── Results screen ────────────────────────────────────────────────────────
    if st.session_state.game_over:
        scores  = st.session_state.pose_scores
        total   = sum(scores)
        perfect = total_poses * 100

        st.markdown(f"## 🎉 Game over!  {total} / {perfect}")
        st.progress(total / perfect)

        for i, s in enumerate(scores):
            grade = "S 🏅" if s>=95 else "A 🥇" if s>=85 else "B 🥈" if s>=70 else "C 🥉" if s>=50 else "D ❌"
            col_a, col_b, col_c = st.columns([1, 4, 1])
            col_a.markdown(f"**Pose {i+1}**")
            col_b.progress(s / 100)
            col_c.markdown(f"**{s}** — {grade}")

        st.balloons()
        if st.button("🔄 Play Again"):
            reset_game()
            st.rerun()
        st.stop()

    # ── Game UI ───────────────────────────────────────────────────────────────
    game_engine  = PoseMatcher(error_threshold=20)
    current_idx  = st.session_state.pose_index
    target_image = game_engine.set_target_picture(
        os.path.join(POSES_PATH, image_files[current_idx])
    )

    st.progress(current_idx / total_poses,
                text=f"Pose {current_idx + 1} of {total_poses}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Match this!")
        pose_ph = st.empty()
        pose_ph.image(cv2.resize(target_image, (640, 640)), channels="BGR")
    with col2:
        st.subheader("📸 You")
        cam_ph = st.empty()

    timer_ph  = st.empty()
    score_ph  = st.empty()

    col_stop, col_restart = st.columns(2)
    with col_stop:
        if st.button("⏹️ Stop", use_container_width=True):
            reset_game(); st.rerun()
    with col_restart:
        if st.button("🔄 Restart", use_container_width=True):
            reset_game(); st.rerun()

    # ── Camera loop ───────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(cam, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if st.session_state.pose_start is None:
        st.session_state.pose_start = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame, total_score, is_perfect = game_engine.process_frame(cv2.flip(frame, 1))
        cam_ph.image(processed_frame, channels="BGR", use_container_width=True)

        now     = time.time()
        elapsed = now - st.session_state.pose_start
        remaining = max(0.0, POSE_SECONDS - elapsed)

        # Track the best score seen during this pose window
        if total_score > st.session_state.best_score:
            st.session_state.best_score = total_score

        # Timer bar + countdown
        timer_ph.progress(
            1.0 - remaining / POSE_SECONDS,
            text=f"⏱ {remaining:.1f}s remaining"
        )

        grade = "S 🏅" if total_score>=95 else "A 🥇" if total_score>=85 else "B 🥈" if total_score>=70 else "C 🥉" if total_score>=50 else "D ❌"
        score_ph.markdown(f"**Live: {total_score}/100 — {grade}** &nbsp;|&nbsp; Best this pose: **{st.session_state.best_score}**")

        # ── Time's up → bank best score and advance ──────────────────────────
        if remaining <= 0:
            st.session_state.pose_scores.append(st.session_state.best_score)
            st.session_state.pose_index += 1
            st.session_state.pose_start  = None
            st.session_state.best_score  = 0

            if st.session_state.pose_index >= total_poses:
                st.session_state.game_over = True
                cap.release()
                st.rerun()
                break

            # Load next pose without stopping the camera
            next_img = game_engine.set_target_picture(
                os.path.join(POSES_PATH, image_files[st.session_state.pose_index])
            )
            pose_ph.image(cv2.resize(next_img, (640, 640)), channels="BGR")
            st.session_state.pose_start = time.time()

    cap.release()

# History side bar menu
elif st.session_state['selected_model'] == "history":
    st.title("History Database") 
    try:
        # ดึงข้อมูลจากไฟล์มาแสดง
        df = pd.read_csv("user_data_log.csv")
        
        # --- กรองข้อมูลด้วย Test_Type ถ้าต้องการ ---
        # ถ้าอยากให้เลือกดูเป็นรายโมเดลได้ สามารถเปิดคอมเมนต์ด้านล่างได้ครับ
        # test_types = ["All"] + list(df["Test_Type"].dropna().unique())
        # selected_type = st.selectbox("Filter by Test Type", test_types)
        # if selected_type != "All":
        #    df = df[df["Test_Type"] == selected_type]
        
        # --- 🗑️ ระบบลบข้อมูล ---
        # 1. แทรกคอลัมน์ Checkbox ไว้หน้าสุดของตาราง
        if "ลบ 🗑️" not in df.columns:
            df.insert(0, "ลบ 🗑️", False)
        # 2. ใช้ data_editor เพื่อให้ตารางโต้ตอบได้
        edited_df = st.data_editor(
            df.iloc[::-1], # เรียงจากใหม่ไปเก่าเหมือนเดิม
            use_container_width=True,
            hide_index=True, # ซ่อนเลข Index ด้านหน้าเพื่อให้ดูคลีน
            column_config={
                "ลบ 🗑️": st.column_config.CheckboxColumn(
                    "ลบ 🗑️",
                    help="เลือกเพื่อลบข้อมูลแถวนี้",
                    default=False,
                )
            }
        )
        
        # 3. ปุ่มกดเพื่อยืนยันการลบ (จัดให้อยู่ฝั่งซ้าย)
        if st.button("Confirm data deletion", type="primary"):
            # กรองเอาเฉพาะข้อมูลที่ "ไม่ได้ติ๊กลบ" (ลบ 🗑️ == False)
            df_to_keep = edited_df[edited_df["ลบ 🗑️"] == False].copy()
            
            # เอาคอลัมน์เช็คบ็อกซ์ออกก่อนเซฟกลับไปเป็น CSV
            df_to_keep = df_to_keep.drop(columns=["ลบ 🗑️"])
            
            # เซฟทับไฟล์เดิม (เรียงกลับให้ถูกต้องก่อนเซฟ)
            df_to_keep.iloc[::-1].to_csv("user_data_log.csv", index=False)
            
            st.success("✔️ ลบข้อมูลเรียบร้อยแล้ว!")
            st.rerun() # รีเฟรชหน้าจอเพื่ออัปเดตตารางใหม่ทันที

        st.markdown("---")
        
        # ปุ่มดาวน์โหลด (เอาคอลัมน์ ลบ 🗑️ ออกก่อนให้โหลด)
        clean_df = df.drop(columns=["ลบ 🗑️"], errors='ignore')
        csv_data = clean_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as a file CSV",
            data=csv_data,
            file_name='fall_risk_assessment_history.csv',
            mime='text/csv',
        )
        
    except FileNotFoundError:
        st.info("⚠️ ยังไม่มีข้อมูลประวัติในระบบ กรุณาทำการทดสอบอย่างน้อย 1 ครั้ง")

elif st.session_state['selected_model'] == "about":

    st.markdown("""
    <style>
    .card {
        background-color: rgba(0, 0, 0, 0.75);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .card h3 {
        color: #ffffff !important;
        margin-top: 0;
        border-bottom: 1px solid #333;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1rem;
    }
    .card p, .card li, .card span {
        color: #cccccc !important;
        font-size: 14px;
        line-height: 1.7;
    }
    .card ul { padding-left: 1.2rem; margin: 0; }
    .card li { margin-bottom: 0.4rem; }
    .card code {
        background: #1a1a1a;
        color: #aaa !important;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 12px;
    }
    .tag {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid #444;
        color: #aaa !important;
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 4px;
        margin: 3px 3px 3px 0;
    }
    .member {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px solid #222;
    }
    .member:last-child { border-bottom: none; }
    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #1a1a1a;
        border: 1px solid #444;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        color: #aaa;
        flex-shrink: 0;
        font-weight: 600;
    }
    .member-name {
        color: #ffffff !important;
        font-size: 14px;
    }
    .supervisor-box {
        background: #111;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 1rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .supervisor-title {
        color: #888 !important;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 2px;
    }
    .supervisor-name {
        color: #ffffff !important;
        font-size: 14px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <h3>About</h3>
      <p>This application was developed as part of the 2102399 Capstone Project in the Department of Electrical Engineering at Chulalongkorn University.</p>
      <p>The primary aim of this project is to build an AI-powered system to accurately assess fall risks in elder people.</p>
      <p>Disclaimer: This application is a university engineering prototype designed for educational and preliminary screening purposes. 
                It is not intended to replace professional medical advice, diagnosis, or treatment. </p>
      <p> Privacy Note: All video processing is performed locally on your device using computer vision. 
                No video footage is recorded, uploaded to the cloud, or shared externally. </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <h3>Development Team</h3>
      <div class="member"><div class="avatar">NP</div><span class="member-name">Natchaphon Pewon | UX/UI developer </span></div>
      <div class="member"><div class="avatar">PS</div><span class="member-name">Phasatron Sriphirod | UX/UI developer </span></div>
      <div class="member"><div class="avatar">PS</div><span class="member-name">Phisit Suphothina |  AI model specialist </span></div>
      <div class="member"><div class="avatar">JJ</div><span class="member-name">Jettanat Jindalux | AI model specialist </span></div>
      <div class="member"><div class="avatar">RP</div><span class="member-name">Ramida Pongkapanakrai | Project coordinator</span></div>
      
      <div class="supervisor-box">
        <div>
          <p class="supervisor-title">Project Supervisor</p>
          <p class="supervisor-name">Asst. Prof. Suree Pumrin</p>
          <p class="supervisor-name">Assoc. Prof. Charnchai Pluempitiwiriyawej</p>
          <p class="supervisor-name">Dr. Natthakorn Kasamsumran</p>
          <p class="supervisor-name">Dr. Chaowarit Ngernthaisong</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <h3>Reference</h3>
      <ul>
        <li><b style="color:#fff">Emojis:</b> All emojis in the app are provided by the Unicode Consortium</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div class="card">
  <h3>Built with</h3>
  <ul style="line-height: 1.8;">
    <li><b>Python</b> – Core programming language powering the app logic</li>
    <li><b>Streamlit</b> – Interactive web app framework for fast UI development</li>
    <li><b>OpenCV</b> – Real-time computer vision and image processing</li>
    <li><b>MediaPipe</b> – Pose detection and movement tracking</li>
    <li><b>NumPy</b> – Efficient numerical computations</li>
    <li><b>Pandas</b> – Data manipulation and analysis</li>
    <li><b>Altair</b> – Declarative statistical visualizations</li>
    <li><b>Plotly</b> – Interactive charts and dashboards</li>
  </ul>
</div>
""", unsafe_allow_html=True)