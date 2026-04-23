import cv2, mediapipe as mp, numpy as np, math, time


class BalanceTest:
    CAL_T = 5
    TEST_T = 10
    HAND_MARGIN = 40
    HIP_MARGIN = 15

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.draw = mp.solutions.drawing_utils

        self.phase = "calibration"
        self.start = time.time()
        self.hand_list = []
        self.hip_list = []
        self.hand_th = None
        self.hip_th = None
        self.hand_fail = False
        self.hip_fail = False
        self.result = ""

    # ─── Geometry helpers ────────────────────────────────────────────────────

    @staticmethod
    def dist(p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    @staticmethod
    def angle(v1, v2):
        v1, v2 = np.array(v1), np.array(v2)
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return None
        c = np.dot(v1, v2) / (n1 * n2)
        return math.degrees(math.acos(np.clip(c, -1, 1)))

    # ─── Signal extraction ───────────────────────────────────────────────────

    def get_signals(self, lm, w, h):
        PL = self.mp_pose.PoseLandmark

        lw = (lm[PL.LEFT_WRIST.value].x * w,  lm[PL.LEFT_WRIST.value].y * h)
        rw = (lm[PL.RIGHT_WRIST.value].x * w, lm[PL.RIGHT_WRIST.value].y * h)
        hand = self.dist(lw, rw)

        def vec(landmark):
            return np.array([lm[landmark.value].x,
                             lm[landmark.value].y,
                             lm[landmark.value].z])

        lhip, rhip   = vec(PL.LEFT_HIP),      vec(PL.RIGHT_HIP)
        lsho, rsho   = vec(PL.LEFT_SHOULDER),  vec(PL.RIGHT_SHOULDER)
        lknee        = vec(PL.LEFT_KNEE)

        mid_hip = (lhip + rhip) / 2
        mid_sho = (lsho + rsho) / 2
        hip = self.angle(mid_sho - mid_hip, lknee - lhip)

        return hand, hip

    # ─── Phases ──────────────────────────────────────────────────────────────

    def calibration_phase(self, frame, now, hand, hip):
        if hand is not None: self.hand_list.append(hand)
        if hip  is not None: self.hip_list.append(hip)

        left = max(0, self.CAL_T - (now - self.start))
        cv2.putText(frame, f"CALIBRATION {left:.1f}s", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        if now - self.start >= self.CAL_T and self.hand_list and self.hip_list:
            self.hand_th = np.mean(self.hand_list) + self.HAND_MARGIN
            self.hip_th  = np.mean(self.hip_list)  + self.HIP_MARGIN
            self.phase   = "testing"
            self.start   = time.time()

    def testing_phase(self, frame, now, hand, hip):
        left     = max(0, self.TEST_T - (now - self.start))
        hand_err = hand is not None and hand > self.hand_th
        hip_err  = hip  is not None and hip  > self.hip_th
        self.hand_fail |= hand_err
        self.hip_fail  |= hip_err

        cv2.putText(frame, f"TESTING {left:.1f}s", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        if hand is not None:
            cv2.putText(frame, f"Hand: {hand:.1f}/{self.hand_th:.1f}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 0, 255) if hand_err else (255, 255, 255), 2)
        if hip is not None:
            cv2.putText(frame, f"Hip: {hip:.1f}/{self.hip_th:.1f}", (20, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 0, 255) if hip_err else (255, 255, 255), 2)

        if self.hand_fail or self.hip_fail:
            self.result = "FAIL"
            self.phase  = "done"
        elif now - self.start >= self.TEST_T:
            self.result = "PASS"
            self.phase  = "done"

    def done_phase(self, frame):
        color = (0, 255, 0) if self.result == "PASS" else (0, 0, 255)
        cv2.putText(frame, f"RESULT: {self.result}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
        cv2.putText(frame, f"Hand: {'FAIL' if self.hand_fail else 'OK'}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Hip: {'FAIL' if self.hip_fail else 'OK'}", (20, 135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press Q to quit", (20, 170),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # ─── Main loop ───────────────────────────────────────────────────────────

    def run(self):
        cap = cv2.VideoCapture(0)

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            res = self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            now = time.time()
            hand = hip = None

            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                self.draw.draw_landmarks(frame, res.pose_landmarks,
                                         self.mp_pose.POSE_CONNECTIONS)
                hand, hip = self.get_signals(lm, w, h)

            if   self.phase == "calibration": self.calibration_phase(frame, now, hand, hip)
            elif self.phase == "testing":     self.testing_phase(frame, now, hand, hip)
            else:                             self.done_phase(frame)

            cv2.imshow("Balance Test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.pose.close()


if __name__ == "__main__":
    BalanceTest().run()