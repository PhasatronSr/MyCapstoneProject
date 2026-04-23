import cv2
import mediapipe as mp
import time

# สร้าง Class จำลองเพื่อรองรับตัวแปรจาก app.py โดยที่ไม่ต้องไปแก้โค้ดหน้า UI
class DummyCalibration:
    def __init__(self, known_distance_m):
        self.known_distance_m = known_distance_m

class WalkSpeedApp:
    def __init__(self, known_distance_m=2.0):
        # ตั้งค่า MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        
        # ตัวแปรสำหรับการคำนวณระยะทางและเวลา
        self.calibration = DummyCalibration(known_distance_m)
        
        self.reset_all()

    def reset_all(self):
        """รีเซ็ตค่าทั้งหมดเพื่อเริ่มการทดสอบใหม่"""
        self.state = "waiting" # waiting, walking, finished
        self.direction = None  # "L2R" (ซ้ายไปขวา) หรือ "R2L" (ขวาไปซ้าย)
        self.start_time = 0
        self.end_time = 0
        self.current_speed = 0.0
        self.avg_speed = 0.0
        self.feedback = "Stand outside the lines to start."

    def process_frame(self, frame):
        """ประมวลผลเฟรมวิดีโอ วาดเส้น และคำนวณความเร็ว"""
        # แปลงสีสำหรับ MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        
        # แปลงสีกลับสำหรับวาด UI
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        h, w, _ = image_bgr.shape

        # กำหนดตำแหน่งเส้น Start / Finish บนหน้าจอ (ที่ระยะ 15% และ 85% ของความกว้างจอ)
        left_line_x = int(w * 0.15)
        right_line_x = int(w * 0.85)
        
        # วาดเส้นจำลองลงบนหน้าจอ
        cv2.line(image_bgr, (left_line_x, 0), (left_line_x, h), (0, 255, 255), 4) # เส้นซ้าย (สีเหลือง)
        cv2.line(image_bgr, (right_line_x, 0), (right_line_x, h), (0, 255, 255), 4) # เส้นขวา (สีเหลือง)

        if results.pose_landmarks:
            # ดึงจุดสะโพกซ้ายและขวา เพื่อหาจุดกึ่งกลางลำตัว (มีความเสถียรสุดเวลาเดิน)
            l_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            r_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            
            # คำนวณพิกัด X ของจุดกึ่งกลางสะโพกเทียบกับขนาดจอ
            mid_hip_x = int(((l_hip.x + r_hip.x) / 2) * w)
            mid_hip_y = int(((l_hip.y + r_hip.y) / 2) * h)
            
            # วาดจุดกึ่งกลางลำตัวให้เห็นชัดๆ
            cv2.circle(image_bgr, (mid_hip_x, mid_hip_y), 10, (0, 0, 255), -1)

            # --- STATE MACHINE (ลอจิกการจับเวลา) ---
            if self.state == "waiting":
                # เช็คว่าผู้ทดสอบยืนรออยู่ฝั่งไหน
                if mid_hip_x < left_line_x:
                    self.direction = "L2R"
                    self.feedback = "Ready... Walk to the RIGHT ->"
                elif mid_hip_x > right_line_x:
                    self.direction = "R2L"
                    self.feedback = "<- Ready... Walk to the LEFT"
                else:
                    self.feedback = "Step OUTSIDE the yellow lines to begin."

                # เงื่อนไขการเริ่มจับเวลา (เดินตัดเส้น)
                if self.direction == "L2R" and mid_hip_x >= left_line_x:
                    self.state = "walking"
                    self.start_time = time.time()
                    self.feedback = "WALKING... KEEP GOING!"
                elif self.direction == "R2L" and mid_hip_x <= right_line_x:
                    self.state = "walking"
                    self.start_time = time.time()
                    self.feedback = "WALKING... KEEP GOING!"

            elif self.state == "walking":
                # กำลังเดิน ให้คำนวณเวลาและความเร็วแบบ Real-time
                current_time_elapsed = time.time() - self.start_time
                if current_time_elapsed > 0:
                    self.current_speed = self.calibration.known_distance_m / current_time_elapsed

                # เงื่อนไขการหยุดจับเวลา (เดินทะลุเส้นตรงข้าม)
                if self.direction == "L2R" and mid_hip_x >= right_line_x:
                    self.state = "finished"
                    self.end_time = current_time_elapsed
                    self.avg_speed = self.calibration.known_distance_m / self.end_time
                    self.feedback = "TEST COMPLETE!"
                elif self.direction == "R2L" and mid_hip_x <= left_line_x:
                    self.state = "finished"
                    self.end_time = current_time_elapsed
                    self.avg_speed = self.calibration.known_distance_m / self.end_time
                    self.feedback = "TEST COMPLETE!"

            # วาดเส้นก้างปลาโครงร่าง
            self.mp_drawing.draw_landmarks(image_bgr, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        # วาดแถบ UI ด้านบนสำหรับบอกสถานะและคำแนะนำ
        cv2.rectangle(image_bgr, (0, 0), (w, 60), (0, 0, 0), -1)
        
        # เปลี่ยนสีข้อความตาม State
        text_color = (255, 255, 255)
        if self.state == "walking": text_color = (0, 255, 0)
        elif self.state == "finished": text_color = (0, 255, 255)
        
        cv2.putText(image_bgr, self.feedback, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

        # แปลงเป็น RGB รอบสุดท้ายเพื่อส่งกลับไปให้ Streamlit
        final_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        # เตรียมข้อมูลส่งกลับให้ app.py ดึงไปแสดงผล
        time_display = (time.time() - self.start_time) if self.state == "walking" else self.end_time
        
        stats = {
            "speed": self.current_speed if self.state == "walking" else self.avg_speed,
            "time": time_display,
            "state": self.state,
            "avg_speed": self.avg_speed
        }
        
        return final_image, stats