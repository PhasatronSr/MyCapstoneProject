import cv2
import mediapipe as mp
import numpy as np

class PoseMatcher:
    def __init__(self, error_threshold=25):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self.pose_video = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose_image = self.mp_pose.Pose(
            static_image_mode=True,
            min_detection_confidence=0.5
        )

        self.target_angles = [0, 0, 0, 0]
        self.error_threshold = error_threshold
        self.limb_names = ["R Arm", "L Arm", "R Leg", "L Leg"]

    @staticmethod
    def calculate_angle(a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    @staticmethod
    def angle_error_to_score(error_deg):
        """
        Converts a single limb angle error (degrees) to a 0–100 score.
        
        Scoring curve:
          0°  error → 100 (perfect)
         10°  error →  90
         25°  error →  70
         45°  error →  50
         90°  error →   0
        """
        max_error = 90.0
        error_deg = min(error_deg, max_error)
        # Quadratic decay: score drops faster as error grows
        score = 100 * ((max_error - error_deg) / max_error) ** 1.5
        return round(score)

    @staticmethod
    def score_to_grade(score):
        """Maps a 0–100 score to a letter grade."""
        if score >= 95: return "S", (0, 215, 255)   # Gold
        if score >= 85: return "A", (0, 200, 80)    # Green
        if score >= 70: return "B", (0, 160, 255)   # Blue
        if score >= 50: return "C", (0, 165, 255)   # Orange
        return "D", (0, 0, 220)                     # Red

    def get_body_angles(self, landmarks):
        def get_coords(landmark_name):
            return [landmarks[landmark_name.value].x, landmarks[landmark_name.value].y]

        r_shoulder = get_coords(self.mp_pose.PoseLandmark.RIGHT_SHOULDER)
        r_elbow    = get_coords(self.mp_pose.PoseLandmark.RIGHT_ELBOW)
        r_wrist    = get_coords(self.mp_pose.PoseLandmark.RIGHT_WRIST)
        l_shoulder = get_coords(self.mp_pose.PoseLandmark.LEFT_SHOULDER)
        l_elbow    = get_coords(self.mp_pose.PoseLandmark.LEFT_ELBOW)
        l_wrist    = get_coords(self.mp_pose.PoseLandmark.LEFT_WRIST)
        r_hip      = get_coords(self.mp_pose.PoseLandmark.RIGHT_HIP)
        r_knee     = get_coords(self.mp_pose.PoseLandmark.RIGHT_KNEE)
        r_ankle    = get_coords(self.mp_pose.PoseLandmark.RIGHT_ANKLE)
        l_hip      = get_coords(self.mp_pose.PoseLandmark.LEFT_HIP)
        l_knee     = get_coords(self.mp_pose.PoseLandmark.LEFT_KNEE)
        l_ankle    = get_coords(self.mp_pose.PoseLandmark.LEFT_ANKLE)

        return [
            self.calculate_angle(r_shoulder, r_elbow, r_wrist),
            self.calculate_angle(l_shoulder, l_elbow, l_wrist),
            self.calculate_angle(r_hip,      r_knee,  r_ankle),
            self.calculate_angle(l_hip,      l_knee,  l_ankle),
        ]

    def compute_pose_score(self, player_angles):
        """
        Returns:
          limb_scores  – list of 4 per-limb scores (0–100)
          total_score  – weighted average (0–100)
          grade        – letter grade string
          color        – BGR color tuple for the grade
        """
        limb_scores = [
            self.angle_error_to_score(abs(self.target_angles[i] - player_angles[i]))
            for i in range(4)
        ]
        total_score = round(sum(limb_scores) / 4)
        grade, color = self.score_to_grade(total_score)
        return limb_scores, total_score, grade, color

    def set_target_picture(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Could not load {image_path}")
            return None

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose_image.process(img_rgb)

        if results.pose_landmarks:
            self.target_angles = self.get_body_angles(results.pose_landmarks.landmark)
            self.mp_drawing.draw_landmarks(img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        return img

    def process_frame(self, frame):
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose_video.process(image_rgb)

        display_frame = frame.copy()
        total_score = 0
        is_perfect = False

        if results.pose_landmarks:
            player_angles = self.get_body_angles(results.pose_landmarks.landmark)
            limb_scores, total_score, grade, color = self.compute_pose_score(player_angles)

            is_perfect = (total_score >= 95)

            # -- Main score badge --
            cv2.putText(display_frame, f"{grade}  {total_score}/100",
                        (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3, cv2.LINE_AA)

            # -- Per-limb breakdown (bottom-left) --
            h = display_frame.shape[0]
            for i, (name, sc) in enumerate(zip(self.limb_names, limb_scores)):
                bar_x, bar_y = 40, h - 130 + i * 28
                bar_w = int(sc * 1.2)   # max ~120px at 100
                _, seg_color = self.score_to_grade(sc)
                cv2.rectangle(display_frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 16), seg_color, -1)
                cv2.putText(display_frame, f"{name}: {sc}",
                            (bar_x + bar_w + 6, bar_y + 13),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            if is_perfect:
                cv2.putText(display_frame, "PERFECT!", (40, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 215, 255), 2, cv2.LINE_AA)

            self.mp_drawing.draw_landmarks(
                display_frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)

        return display_frame, total_score, is_perfect