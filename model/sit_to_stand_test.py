import cv2
import mediapipe as mp
import numpy as np
import time

class SitToStand:
    def __init__(self, target_reps=5, calibration_time_frames=60):
        self.target_reps = target_reps
        self.cal_frames_limit = calibration_time_frames
        
        # MediaPipe Init
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1, 
            min_detection_confidence=0.5
        )
        self.reset()

    def reset(self):
        self.reps = 0
        self.state = "pre_calibration" # New Initial State
        self.pre_cal_start_time = None 
        
        self.calibration_frames = 0
        self.calibration_ratios = []
        self.standing_ref = 0
        
        self.sit_thresh = 0
        self.stand_thresh = 0
        self.start_time = 0
        self.end_time = 0
        self.feedback = "Prepare to stand still"
        
        # --- ตัวแปรสำหรับจับเวลาแต่ละรอบ ---
        self.rep_times = []     
        self.rep_start_time = 0 

    def _calculate_ratio(self, landmarks):
        try:
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            avg_hip_y = (left_hip.y + right_hip.y) / 2
            avg_knee_y = (left_knee.y + right_knee.y) / 2
            ys = [lm.y for lm in landmarks]
            body_height = max(ys) - min(ys)
            return (avg_knee_y - avg_hip_y) / body_height if body_height != 0 else 0
        except: return 0


    def process_frame(self, frame):
        h_orig, w_orig = frame.shape[:2]
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)

        
        display_frame = frame.copy()
        current_ratio = 0

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            current_ratio = self._calculate_ratio(landmarks)
            
            # --- 1. PRE-CALIBRATION (3 SECONDS WAITING) ---
            if self.state == "pre_calibration":
                if self.pre_cal_start_time is None:
                    self.pre_cal_start_time = time.time()
                
                elapsed = time.time() - self.pre_cal_start_time
                countdown = max(0, int(np.ceil(3 - elapsed)))
                self.feedback = "STAND FOR CALIBRATION"

                # Central UI for Countdown
                cv2.putText(display_frame, "STAND FOR CALIBRATION", (w_orig//2 - 250, h_orig//2 - 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
                cv2.putText(display_frame, str(countdown), (w_orig//2 - 20, h_orig//2 + 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 255), 5)

                if elapsed >= 3:
                    self.state = "calibrating"

            # --- 2. CALIBRATION (60 FRAMES DATA COLLECTION) ---
            elif self.state == "calibrating":
                self.calibration_frames += 1
                self.calibration_ratios.append(current_ratio)
                self.feedback = "CALIBRATING... STAND STILL"
                
                # Visual Bar for 60-frame progress
                progress = int((self.calibration_frames / self.cal_frames_limit) * 400)
                cv2.rectangle(display_frame, (w_orig//2 - 200, h_orig//2 + 20), (w_orig//2 - 200 + progress, h_orig//2 + 40), (0, 255, 255), -1)
                cv2.putText(display_frame, "COLLECTING DATA", (w_orig//2 - 120, h_orig//2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

                if self.calibration_frames >= self.cal_frames_limit:
                    self.standing_ref = np.mean(self.calibration_ratios)
                    self.sit_thresh = self.standing_ref * 0.7
                    self.stand_thresh = self.standing_ref * 0.9
                    self.state = "standing"
                    self.start_time = time.time()
                    self.rep_start_time = self.start_time # เริ่มจับเวลารอบที่ 1
                    self.feedback = "GO!"

            # --- 3. EXERCISING LOGIC ---
            elif self.state in ["standing", "sitting"] and self.reps < self.target_reps:
                if self.state == "standing" and current_ratio < self.sit_thresh:
                    self.state = "sitting"
                    self.feedback = "DOWN"
                if self.state == "sitting" and current_ratio > self.stand_thresh:
                    self.state = "standing"
                    self.reps += 1
                    
                    # คำนวณเวลาที่ใช้ในรอบนี้ (Lap Time) โดยเอาเวลาปัจจุบันลบกับเวลาเริ่มของรอบนั้น
                    current_time = time.time()
                    time_taken = current_time - self.rep_start_time
                    self.rep_times.append(time_taken)
                    self.rep_start_time = current_time # รีเซ็ตเวลาเพื่อเริ่มจับรอบถัดไป
                    
                    self.feedback = "UP - Good Rep!"
                self._draw_threshold_bar(display_frame, current_ratio, h_orig, w_orig)

            elif self.reps >= self.target_reps:
                if self.end_time == 0: self.end_time = time.time() - self.start_time
                self.state = "finished"
                self.feedback = "COMPLETE"

            self.mp_drawing.draw_landmarks(display_frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        # UI Header
        cv2.rectangle(display_frame, (0,0), (350, 80), (245, 117, 16), -1)
        cv2.putText(display_frame, f'REPS: {self.reps}/{self.target_reps}', (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(display_frame, f' {self.feedback}', (10,65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        stats = {
            "reps": self.reps,
            "target": self.target_reps,
            "state": self.state,
            "feedback": self.feedback,
            "time": (time.time() - self.start_time) if self.start_time > 0 and self.state != "finished" else self.end_time,
            "rep_times": self.rep_times # ส่งข้อมูลเวลาไปให้ app.py วาดกราฟ
        }
        
        return cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB), stats

    def _draw_threshold_bar(self, image, current_ratio, h, w):
        cv2.rectangle(image, (w-40, 100), (w-10, h-100), (200,200,200), 1)
        norm_h = int(np.interp(current_ratio, [0, self.standing_ref], [h-100, 100]))
        cv2.rectangle(image, (w-40, norm_h), (w-10, h-100), (0,255,0), -1)
        sit_y = int(np.interp(self.sit_thresh, [0, self.standing_ref], [h-100, 100]))
        cv2.line(image, (w-50, sit_y), (w, sit_y), (0,0,255), 2)