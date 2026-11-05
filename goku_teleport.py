"""
=============================================================================
   GOKU ANIME TECHNIQUES: INSTANT TRANSMISSION & KAMEHAMEHA
=============================================================================
Combines two legendary Dragon Ball techniques:

1. ⚡ INSTANT TRANSMISSION (Teleport):
   - Pose: Two fingers on forehead/temple (hold ~0.4s)
   - Effect: Anime speedlines warp -> teleport to Live Screen or Empty Room!
   - Repeat pose to reappear!

2. 💥 KAMEHAMEHA:
   - Pose: Cup both hands together at your hip / chest
   - Effect: Glowing cyan Ki orb forms with electric lightning arcs
   - Chant: KA... ME... HA... ME...
   - Fire: Push hands forward toward camera (or release) -> ...HAAAAA!!!!!!
   - Gigantic beam blast, shockwaves, screen shake & roar sound FX!

Controls:
  [Fingers to Forehead]     : Instant Transmission (Teleport)
  [Both Hands Cupped at Hip]: Charge Kamehameha (Push forward to FIRE!)
  [K]                       : Instant manual Kamehameha trigger
  [SPACE] or [T]            : Instant manual Teleport toggle
  [P]                       : Show / Hide Picture-in-Picture (PIP) box
  [C]                       : Toggle POV meme caption banner
  [R]                       : Rotate camera 90° clockwise (0°, 90°, 180°, 270°)
  [F]                       : Toggle horizontal mirror flip (selfie / rear camera)
  [M]                       : Toggle Mode (LIVE DESKTOP SCREEN vs EMPTY ROOM)
  [B]                       : Capture current frame as room background
  [D]                       : Toggle debug HUD / target zone
  [S]                       : Toggle sound effects
  [Q] or [ESC]              : Quit
=============================================================================
"""

import os
import sys
import time
import math
import wave
import threading
import argparse
import numpy as np
import cv2

# Windows native async audio
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Mediapipe tasks vision
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

# Virtual camera support (OBS / pyvirtualcam)
try:
    import pyvirtualcam
    HAS_PYVIRTUALCAM = True
except ImportError:
    HAS_PYVIRTUALCAM = False

# Screen capture support
try:
    from PIL import ImageGrab
    HAS_PIL_GRAB = True
except ImportError:
    HAS_PIL_GRAB = False

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False


# ---------------------------------------------------------------------------
# Zero-Lag Threaded Camera (Eliminates DroidCam / Wi-Fi Stream Buffer Latency)
# ---------------------------------------------------------------------------
class ZeroLagCamera:
    """
    Spawns a dedicated thread that continuously pulls frames from the camera
    or network stream and discards accumulated buffer queues.
    Guarantees 0ms lag even over Wi-Fi / DroidCam.
    """
    def __init__(self, src, width=None, height=None, fps=30):
        self.src = src
        self.is_url = not str(src).isdigit()

        if self.is_url:
            # Network stream (DroidCam / IP camera)
            print(f"[INFO] Connecting to network stream: {src}")
            self.cap = cv2.VideoCapture(str(src))
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            cam_idx = int(src)
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(cam_idx)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if width and height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if fps:
            self.cap.set(cv2.CAP_PROP_FPS, fps)

        self.stopped = False
        self.latest_frame = None
        self.lock = threading.Lock()

        # Grab first frame
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.latest_frame = frame
        else:
            # Try once more
            time.sleep(0.1)
            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            with self.lock:
                self.latest_frame = frame

    def read(self):
        with self.lock:
            if self.latest_frame is None:
                return False, None
            return True, self.latest_frame.copy()

    def get(self, prop_id):
        return self.cap.get(prop_id)

    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=0.4)
        self.cap.release()


# ---------------------------------------------------------------------------
# Screen Capturer (Live Desktop Streaming)
# ---------------------------------------------------------------------------
class ScreenCapturer:
    def __init__(self, target_w=1280, target_h=720):
        self.target_w = target_w
        self.target_h = target_h
        self.sct = None
        self.last_frame = None

        if HAS_MSS:
            try:
                self.sct = mss.MSS()
            except Exception:
                self.sct = None

    def capture(self) -> np.ndarray:
        frame = None

        if self.sct is not None:
            try:
                mon = self.sct.monitors[1]
                sct_img = self.sct.grab(mon)
                arr = np.frombuffer(sct_img.raw, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 4))
                frame = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            except Exception:
                pass

        if frame is None and HAS_PIL_GRAB:
            try:
                shot = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
            except Exception:
                pass

        if frame is not None:
            if frame.shape[1] != self.target_w or frame.shape[0] != self.target_h:
                frame = cv2.resize(frame, (self.target_w, self.target_h), interpolation=cv2.INTER_LINEAR)
            self.last_frame = frame
            return frame

        if self.last_frame is not None:
            return self.last_frame

        placeholder = np.zeros((self.target_h, self.target_w, 3), dtype=np.uint8)
        cv2.putText(placeholder, "LIVE SCREEN SHARING", (self.target_w // 4, self.target_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3, cv2.LINE_AA)
        return placeholder


# ---------------------------------------------------------------------------
# Audio Synthesis (Dragon Ball Sound Effects)
# ---------------------------------------------------------------------------
def ensure_all_sounds():
    """Generates all required DBZ sounds if missing."""
    sounds = {
        "teleport": "teleport.wav",
        "charge": "kamehameha_charge.wav",
        "blast": "kamehameha_fire.wav"
    }

    sr = 44100

    # 1. Teleport sound
    if not (os.path.exists(sounds["teleport"]) and os.path.getsize(sounds["teleport"]) > 1000):
        duration = 0.42
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        split = int(sr * 0.07)
        p1 = np.linspace(900, 3600, split)
        p2 = 3600 * np.exp(-16 * (t[split:] - 0.07))
        phase = 2 * np.pi * np.cumsum(np.concatenate([p1, p2])) / sr
        carrier = 0.65 * np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.10 * np.sin(3 * phase)
        noise = np.random.normal(0, 0.2, len(t)) * np.exp(-32 * t)
        amp = np.exp(-6.5 * t) * (1 - np.exp(-85 * t))
        sig = (carrier + noise) * amp
        sig = (sig / (np.max(np.abs(sig)) + 1e-6) * 32767).astype(np.int16)
        with wave.open(sounds["teleport"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(sig.tobytes())

    # 2. Kamehameha Charge sound
    if not (os.path.exists(sounds["charge"]) and os.path.getsize(sounds["charge"]) > 1000):
        dur_c = 1.3
        t_c = np.linspace(0, dur_c, int(sr * dur_c), endpoint=False)
        pitch_c = np.linspace(160, 700, len(t_c))
        phase_c = 2 * np.pi * np.cumsum(pitch_c) / sr
        hum = (0.5 * np.sin(phase_c) + 0.3 * np.sin(2 * phase_c)) * (1 + 0.18 * np.sin(2 * np.pi * 14 * t_c))
        sizzle = np.random.normal(0, 0.15, len(t_c)) * (t_c / dur_c)
        sig_c = (hum + sizzle) * np.linspace(0.2, 1.0, len(t_c))
        sig_c = (sig_c / (np.max(np.abs(sig_c)) + 1e-6) * 32767).astype(np.int16)
        with wave.open(sounds["charge"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(sig_c.tobytes())

    # 3. Kamehameha Blast sound
    if not (os.path.exists(sounds["blast"]) and os.path.getsize(sounds["blast"]) > 1000):
        dur_f = 1.0
        t_f = np.linspace(0, dur_f, int(sr * dur_f), endpoint=False)
        boom = np.sin(2 * np.pi * 95 * np.exp(-12 * t_f) * t_f) * np.exp(-4 * t_f)
        beam_phase = 2 * np.pi * np.cumsum(np.linspace(440, 190, len(t_f))) / sr
        beam = 0.4 * np.sin(beam_phase) + 0.3 * np.sin(1.5 * beam_phase)
        noise = np.random.normal(0, 0.4, len(t_f)) * np.exp(-2.5 * t_f)
        sig_f = (boom * 0.6 + beam * 0.4 + noise * 0.5) * np.exp(-2.0 * t_f)
        sig_f = (sig_f / (np.max(np.abs(sig_f)) + 1e-6) * 32767).astype(np.int16)
        with wave.open(sounds["blast"], "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(sig_f.tobytes())

    return sounds


def play_sound(sound_path: str, enabled: bool = True):
    """Plays sound asynchronously without blocking video processing."""
    if not enabled or not HAS_WINSOUND or not os.path.exists(sound_path):
        return
    try:
        winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Visual Effects: Teleport Warp & Kamehameha Blast
# ---------------------------------------------------------------------------
def apply_teleport_fx(frame_from: np.ndarray, frame_to: np.ndarray, progress: float) -> np.ndarray:
    """Applies anime teleport speedlines and vertical slice displacement."""
    progress = np.clip(progress, 0.0, 1.0)
    h, w, _ = frame_from.shape

    base = frame_from.copy() if progress < 0.5 else frame_to.copy()
    intensity = np.sin(progress * np.pi)

    # Vertical slice displacement
    num_displaced = int(w * 0.35 * intensity)
    if num_displaced > 0:
        cols = np.random.choice(w, num_displaced, replace=False)
        for col in cols:
            shift = int(np.random.normal(0, 30 * intensity))
            base[:, col] = np.roll(base[:, col], shift, axis=0)

    # Vertical speedlines
    lines_img = np.zeros_like(base)
    num_lines = int(60 * intensity)
    for _ in range(num_lines):
        x = np.random.randint(0, w)
        l_len = np.random.randint(int(h * 0.25), int(h * 0.85))
        y0 = np.random.randint(0, max(1, h - l_len))
        y1 = min(h - 1, y0 + l_len)
        b_val = np.random.randint(210, 256)
        color = (b_val, b_val, 255)
        cv2.line(lines_img, (x, y0), (x, y1), color, np.random.choice([1, 2, 3], p=[0.75, 0.2, 0.05]))

    lines_img = cv2.GaussianBlur(lines_img, (3, 3), 0)
    alpha = min(0.85, 0.9 * intensity)
    out = np.clip(base.astype(np.float32) + lines_img.astype(np.float32) * alpha, 0, 255).astype(np.uint8)

    if intensity > 0.65:
        flash_val = int(50 * ((intensity - 0.65) / 0.35))
        out = cv2.add(out, np.full_like(out, (flash_val, flash_val, flash_val)))

    return out


def draw_kamehameha_charge(img: np.ndarray, center: tuple, progress: float, time_val: float) -> np.ndarray:
    """Draws a smooth, pulsating cyan Ki energy sphere with electric sparks."""
    out = img.copy()
    cx, cy = center

    # Smooth breathing pulse
    pulse = 1.0 + 0.06 * math.sin(time_val * 14)
    radius = int((20 + 48 * progress) * pulse)

    # Soft glowing multi-layered aura
    glow = np.zeros_like(img)
    cv2.circle(glow, (cx, cy), int(radius * 1.8), (255, 120, 10), -1)  # Deep blue aura
    cv2.circle(glow, (cx, cy), int(radius * 1.3), (255, 220, 60), -1)  # Bright cyan
    cv2.circle(glow, (cx, cy), radius, (255, 255, 200), -1)            # Inner core
    cv2.circle(glow, (cx, cy), int(radius * 0.6), (255, 255, 255), -1) # Core white

    # Lightning sparks
    num_sparks = int(3 + 6 * progress)
    for _ in range(num_sparks):
        angle = np.random.uniform(0, 2 * np.pi)
        length = np.random.uniform(radius * 0.8, radius * 2.0)
        pts = [(cx, cy)]
        for seg in [0.4, 0.75, 1.0]:
            r_seg = length * seg
            jitter = np.random.uniform(-10, 10)
            x_seg = int(cx + r_seg * math.cos(angle) + jitter * math.sin(angle))
            y_seg = int(cy + r_seg * math.sin(angle) - jitter * math.cos(angle))
            pts.append((x_seg, y_seg))
        for i in range(len(pts) - 1):
            cv2.line(glow, pts[i], pts[i+1], (255, 255, 220), 1)

    glow = cv2.GaussianBlur(glow, (25, 25), 0)
    out = cv2.addWeighted(out, 1.0, glow, 0.85, 0)
    cv2.circle(out, (cx, cy), int(radius * 0.5), (255, 255, 255), -1)

    return out


def draw_kamehameha_beam(img: np.ndarray, origin: tuple, progress: float) -> np.ndarray:
    """Draws a smooth, massive Kamehameha beam blast with shockwaves and fading shake."""
    h, w, _ = img.shape
    ox, oy = origin
    out = img.copy()

    # Smooth decaying camera shake
    shake_intensity = int((1.0 - progress) * 14)
    if shake_intensity > 0:
        dx = int(np.random.uniform(-shake_intensity, shake_intensity))
        dy = int(np.random.uniform(-shake_intensity, shake_intensity))
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        out = cv2.warpAffine(out, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    beam_layer = np.zeros_like(img)
    # Easing curve
    ease = math.sin(progress * math.pi * 0.5)
    intensity = max(0.0, 1.0 - (progress ** 1.8))

    # Expanding beam core
    core_r = int(90 + 280 * ease)
    cv2.circle(beam_layer, (ox, oy), int(core_r * 1.5), (255, 140, 20), -1)
    cv2.circle(beam_layer, (ox, oy), core_r, (255, 230, 90), -1)
    cv2.circle(beam_layer, (ox, oy), int(core_r * 0.65), (255, 255, 255), -1)

    # Concentric shockwave rings
    for mult in [1.6, 2.3, 3.1]:
        ring_r = int(core_r * mult)
        ring_thickness = max(1, int(5 * intensity))
        cv2.circle(beam_layer, (ox, oy), ring_r, (255, 220, 110), ring_thickness)

    # Soften beam layer
    beam_layer = cv2.GaussianBlur(beam_layer, (25, 25), 0)
    out = cv2.addWeighted(out, 1.0, beam_layer, min(1.0, 0.9 * intensity), 0)

    # Whiteout flash at ignition
    if progress < 0.22:
        flash_p = (0.22 - progress) / 0.22
        flash_val = int(100 * flash_p)
        out = cv2.add(out, np.full_like(out, (flash_val, flash_val, flash_val)))

    return out


def apply_camera_transforms(frame: np.ndarray, rotation: int, flip_horizontal: bool) -> np.ndarray:
    """
    Applies camera rotation (0, 90, 180, 270) and horizontal mirror flip.
    Ensures phone camera feeds (e.g. DroidCam) are oriented correctly.
    """
    if frame is None:
        return None
    if rotation == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if flip_horizontal:
        frame = cv2.flip(frame, 1)
    return frame


def draw_meme_caption(img: np.ndarray, text: str) -> np.ndarray:
    """
    Renders a viral TikTok/Reels style meme caption banner at the top of the video
    with a translucent dark pill background, border, and crisp typography.
    """
    if not text:
        return img
    h, w, _ = img.shape
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = max(0.65, min(1.05, w / 1150.0))
    thickness = 2
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

    pad_x = 22
    pad_y = 12
    cx = w // 2
    top_y = 18

    x1 = max(10, cx - tw // 2 - pad_x)
    y1 = top_y
    x2 = min(w - 10, cx + tw // 2 + pad_x)
    y2 = top_y + th + pad_y * 2

    # Translucent black background banner
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (18, 18, 18), -1)
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 255), 2)
    alpha = 0.72
    out = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # Crisp white text with black outline for high contrast
    tx = cx - tw // 2
    ty = top_y + th + pad_y - 2
    cv2.putText(out, text, (tx, ty), font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(out, text, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return out


# ---------------------------------------------------------------------------
# Goku Dual Technique Detector (Teleport & Kamehameha)
# ---------------------------------------------------------------------------
class GokuTechniqueDetector:
    """
    Detects both:
    1. Instant Transmission: Fingers to forehead/temple.
    2. Kamehameha: Both hands cupped together at hip/chest.
    """
    def __init__(self, pose_model="pose_landmarker.task", hand_model="hand_landmarker.task"):
        self.pose_detector = None
        self.hand_detector = None
        self.last_forehead = None
        self.last_seen_time = 0.0

        if HAS_MEDIAPIPE and os.path.exists(pose_model):
            try:
                base_p = python.BaseOptions(model_asset_path=pose_model)
                self.pose_detector = vision.PoseLandmarker.create_from_options(
                    vision.PoseLandmarkerOptions(
                        base_options=base_p,
                        running_mode=vision.RunningMode.IMAGE,
                        num_poses=1,
                        min_pose_detection_confidence=0.3,
                        min_pose_presence_confidence=0.3
                    )
                )
            except Exception as e:
                print(f"[WARNING] PoseLandmarker init: {e}")

        if HAS_MEDIAPIPE and os.path.exists(hand_model):
            try:
                base_h = python.BaseOptions(model_asset_path=hand_model)
                self.hand_detector = vision.HandLandmarker.create_from_options(
                    vision.HandLandmarkerOptions(
                        base_options=base_h,
                        running_mode=vision.RunningMode.IMAGE,
                        num_hands=2,
                        min_hand_detection_confidence=0.3,
                        min_hand_presence_confidence=0.3
                    )
                )
            except Exception as e:
                print(f"[WARNING] HandLandmarker init: {e}")

    def detect(self, frame_bgr: np.ndarray):
        h, w, _ = frame_bgr.shape
        now = time.time()

        # Fast downscaled inference for real-time 30+ FPS
        max_dim = 480
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            dw, dh = int(w * scale), int(h * scale)
            detect_frame = cv2.resize(frame_bgr, (dw, dh), interpolation=cv2.INTER_NEAREST)
        else:
            detect_frame = frame_bgr

        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(detect_frame, cv2.COLOR_BGR2RGB))

        forehead_box = None
        forehead_center = None
        eye_dist = 0.06
        pose_hand_in_zone = False
        pose_kame_cupped = False
        pose_hands_center = None

        # 1. Pose Tracking
        if self.pose_detector is not None:
            try:
                p_res = self.pose_detector.detect(mp_img)
                if p_res.pose_landmarks and len(p_res.pose_landmarks) > 0:
                    p = p_res.pose_landmarks[0]
                    l_eye, r_eye = p[2], p[5]
                    eye_dist = max(0.02, np.hypot(l_eye.x - r_eye.x, l_eye.y - r_eye.y))
                    mid_x = (l_eye.x + r_eye.x) / 2
                    mid_y = (l_eye.y + r_eye.y) / 2

                    forehead_x = mid_x
                    forehead_y = mid_y - 0.55 * eye_dist
                    forehead_center = (int(forehead_x * w), int(forehead_y * h))

                    span_x = max(0.12, 2.4 * eye_dist)
                    span_y_up = max(0.14, 3.0 * eye_dist)
                    span_y_down = max(0.04, 0.6 * eye_dist)

                    box_x1 = int((mid_x - span_x) * w)
                    box_x2 = int((mid_x + span_x) * w)
                    box_y1 = int((mid_y - span_y_up) * h)
                    box_y2 = int((mid_y + span_y_down) * h)
                    forehead_box = (max(0, box_x1), max(0, box_y1), min(w - 1, box_x2), min(h - 1, box_y2))

                    self.last_forehead = (forehead_center, forehead_box, eye_dist)
                    self.last_seen_time = now

                    # Teleport wrist check
                    for idx_lm in [19, 20, 15, 16]:
                        px, py = int(p[idx_lm].x * w), int(p[idx_lm].y * h)
                        if (box_x1 <= px <= box_x2 and box_y1 <= py <= box_y2):
                            pose_hand_in_zone = True
                            break

                    # Check Kamehameha pose from Pose (wrists strictly close together, below eye level)
                    w_dist = np.hypot(p[15].x - p[16].x, p[15].y - p[16].y)
                    # Strict proximity: wrists must be within 0.12 (genuinely touching/cupped)
                    if w_dist < 0.12 and p[15].y > (mid_y + 0.1) and p[16].y > (mid_y + 0.1):
                        pose_kame_cupped = True
                        pose_hands_center = (int((p[15].x + p[16].x) / 2 * w), int((p[15].y + p[16].y) / 2 * h))
            except Exception:
                pass

        if forehead_box is None and self.last_forehead is not None and (now - self.last_seen_time < 2.5):
            forehead_center, forehead_box, eye_dist = self.last_forehead

        if forehead_box is None:
            bx1, bx2 = int(w * 0.25), int(w * 0.75)
            by1, by2 = int(h * 0.08), int(h * 0.48)
            forehead_box = (bx1, by1, bx2, by2)
            forehead_center = (int((bx1 + bx2) / 2), int((by1 + by2) / 2))

        is_touching_forehead = False
        is_charging_kame = False
        kame_center = None
        detected_fingertips = []

        # 2. Hand Tracking
        if self.hand_detector is not None:
            try:
                h_res = self.hand_detector.detect(mp_img)
                if h_res.hand_landmarks:
                    bx1, by1, bx2, by2 = forehead_box
                    hands_info = []

                    for hand in h_res.hand_landmarks:
                        wrist = hand[0]
                        idx_tip = hand[8]
                        mid_tip = hand[12]
                        idx_mcp = hand[5]
                        pinky_mcp = hand[17]
                        palm_cx = (wrist.x + idx_mcp.x + pinky_mcp.x) / 3
                        palm_cy = (wrist.y + idx_mcp.y + pinky_mcp.y) / 3
                        hands_info.append({"wrist": wrist, "palm": (palm_cx, palm_cy)})

                        pt_idx = (int(idx_tip.x * w), int(idx_tip.y * h))
                        pt_mid = (int(mid_tip.x * w), int(mid_tip.y * h))
                        detected_fingertips.extend([pt_idx, pt_mid])

                        # Check Teleport pose (forehead touch)
                        d_idx_tip = np.hypot(wrist.x - idx_tip.x, wrist.y - idx_tip.y)
                        d_idx_pip = np.hypot(wrist.x - hand[6].x, wrist.y - hand[6].y)
                        is_extended = (d_idx_tip > d_idx_pip * 0.85) if eye_dist > 0.04 else True

                        idx_in = (bx1 <= pt_idx[0] <= bx2 and by1 <= pt_idx[1] <= by2)
                        mid_in = (bx1 <= pt_mid[0] <= bx2 and by1 <= pt_mid[1] <= by2)
                        mcp_in = (bx1 <= int(idx_mcp.x * w) <= bx2 and by1 <= int(idx_mcp.y * h) <= by2)
                        dist_ctr = np.hypot(pt_idx[0] - forehead_center[0], pt_idx[1] - forehead_center[1])
                        thresh_px = max(80, int(eye_dist * w * 2.8))

                        if (idx_in or mid_in or mcp_in or dist_ctr < thresh_px) and is_extended:
                            is_touching_forehead = True

                    # Check Kamehameha pose: BOTH hands must be close together (cupped)
                    if len(hands_info) >= 2:
                        w1, w2 = hands_info[0]["wrist"], hands_info[1]["wrist"]
                        p1, p2 = hands_info[0]["palm"], hands_info[1]["palm"]

                        dist_wrists = np.hypot(w1.x - w2.x, w1.y - w2.y)
                        dist_palms = np.hypot(p1[0] - p2[0], p1[1] - p2[1])
                        min_dist = min(dist_wrists, dist_palms)

                        # Strict proximity: hands must be within 0.12 (touching or cupped close)
                        mid_hand_y = (p1[1] + p2[1]) / 2
                        if min_dist < 0.12 and mid_hand_y > (forehead_center[1] / h + 0.12):
                            is_charging_kame = True
                            kame_center = (int((p1[0] + p2[0]) / 2 * w), int(mid_hand_y * h))
            except Exception:
                pass

        if not is_touching_forehead and pose_hand_in_zone:
            is_touching_forehead = True

        if not is_charging_kame and pose_kame_cupped:
            is_charging_kame = True
            kame_center = pose_hands_center

        debug_data = {
            "forehead_box": forehead_box,
            "forehead_center": forehead_center,
            "fingertips": detected_fingertips,
            "kame_center": kame_center
        }

        return is_touching_forehead, is_charging_kame, kame_center, debug_data


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Goku Anime Techniques (Teleport & Kamehameha)")
    parser.add_argument("--camera", type=str, default="0",
                        help="Webcam device index (e.g. 0, 1) or DroidCam Wi-Fi URL (e.g. http://192.168.1.50:4747/video)")
    parser.add_argument("--video", type=str, default=None, help="Video file instead of webcam (for testing)")
    parser.add_argument("--output", type=str, default=None, help="Save processed video to file")
    parser.add_argument("--width", type=int, default=1280, help="Target camera width")
    parser.add_argument("--height", type=int, default=720, help="Target camera height")
    parser.add_argument("--fps", type=int, default=30, help="Target frame rate")
    parser.add_argument("--virtual-camera", action="store_true", default=True,
                        help="Stream to OBS Virtual Camera for Google Meet / Zoom / Teams (default: True)")
    parser.add_argument("--no-vcam", dest="virtual_camera", action="store_false",
                        help="Disable virtual camera streaming")
    parser.add_argument("--hold-time", type=float, default=0.45, help="Teleport hold duration (seconds)")
    parser.add_argument("--mode", type=str, choices=["screen", "bg"], default="screen",
                        help="Teleport destination: 'screen' (live desktop screen) or 'bg' (empty room)")
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0,
                        help="Rotate camera feed (0, 90, 180, 270 degrees) - perfect for phone cameras / DroidCam")
    parser.add_argument("--no-flip", action="store_true",
                        help="Disable horizontal mirror flip (recommended for phone rear camera)")
    parser.add_argument("--caption", type=str, default="POV: How to leave a meeting like Goku",
                        help="POV meme caption overlay (default: 'POV: How to leave a meeting like Goku')")
    parser.add_argument("--no-caption", action="store_true", help="Start with meme caption hidden")
    parser.add_argument("--no-pip", action="store_true", help="Start with Picture-in-Picture hidden")
    parser.add_argument("--sound", action="store_true", default=True, help="Enable sound effects")
    parser.add_argument("--bg-path", type=str, default="background.jpg", help="Path to saved background image")
    args = parser.parse_args()

    sounds = ensure_all_sounds()

    print("\n" + "=" * 70)
    print(" 💥 GOKU ANIME TECHNIQUES: INSTANT TRANSMISSION & KAMEHAMEHA 💥")
    print("=" * 70)
    print(f"  * Mode: [{'LIVE DESKTOP SCREEN' if args.mode == 'screen' else 'EMPTY ROOM BACKGROUND'}]")
    print("  * [Two Fingers to Forehead] : Teleport / Reappear")
    print("  * [Cup Both Hands at Hip]   : Charge Kamehameha (Push forward to FIRE!)")
    print("  * [K]                       : Instant manual Kamehameha test")
    print("  * [SPACE] / [T]             : Instant manual Teleport toggle")
    print("  * [C]                       : Toggle POV meme caption banner")
    print("  * [R]                       : Rotate camera 90° clockwise (0° -> 90° -> 180° -> 270°)")
    print("  * [F]                       : Toggle horizontal mirror flip (selfie / rear camera)")
    print("  * [P]                       : Show / Hide PIP box")
    print("  * [M]                       : Toggle Mode between LIVE SCREEN & EMPTY ROOM")
    print("  * [B]                       : Capture clean room background")
    print("  * [D]                       : Toggle debug HUD & target zone")
    print("  * [Q]                       : Quit")
    print("=" * 70 + "\n")

    rotation_angle = args.rotate
    flip_mirror = not args.no_flip if not args.video else False

    if args.video:
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            print(f"[FATAL] Cannot open video file: {args.video}")
            return
        ret, frame = cap.read()
        if ret and frame is not None:
            frame = apply_camera_transforms(frame, rotation_angle, flip_mirror)
            actual_h, actual_w, _ = frame.shape
        else:
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if rotation_angle in (90, 270):
                actual_w, actual_h = actual_h, actual_w
    else:
        # ZeroLagCamera for 0ms lag on both webcams and DroidCam streams
        cap = ZeroLagCamera(args.camera, width=args.width, height=args.height, fps=args.fps)
        if not cap.isOpened():
            print(f"[FATAL] Camera '{args.camera}' not accessible. Exiting.")
            return

        # Wait a moment for initial frame
        for _ in range(15):
            ret, frame = cap.read()
            if ret and frame is not None:
                frame = apply_camera_transforms(frame, rotation_angle, flip_mirror)
                actual_h, actual_w, _ = frame.shape
                break
            time.sleep(0.1)
        else:
            if rotation_angle in (90, 270):
                actual_w, actual_h = args.height, args.width
            else:
                actual_w, actual_h = args.width, args.height

    print(f"[INFO] Camera stream ready (Zero-Lag active): {actual_w}x{actual_h}")

    screen_capturer = ScreenCapturer(target_w=actual_w, target_h=actual_h)

    vcam = None
    if args.virtual_camera:
        if HAS_PYVIRTUALCAM:
            try:
                vcam = pyvirtualcam.Camera(width=actual_w, height=actual_h, fps=args.fps, fmt=pyvirtualcam.PixelFormat.BGR)
                print(f"[SUCCESS] Virtual camera active: {vcam.device}")
                print("  ================================================================")
                print("  👉 IN GOOGLE MEET / ZOOM / TEAMS:")
                print("     1. Open Video Settings")
                print(f"     2. Select camera: '{vcam.device}'")
                print("  ================================================================")
            except Exception as e:
                print(f"[WARNING] Virtual camera could not be created: {e}")
        else:
            print("[WARNING] pyvirtualcam not installed.")

    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, args.fps, (actual_w, actual_h))

    detector = GokuTechniqueDetector("pose_landmarker.task", "hand_landmarker.task")

    background = None
    if os.path.exists(args.bg_path):
        loaded_bg = cv2.imread(args.bg_path)
        if loaded_bg is not None:
            background = cv2.resize(loaded_bg, (actual_w, actual_h))

    # Teleport states
    is_teleported = False
    is_transitioning = False
    teleport_mode = args.mode
    trans_start_time = 0.0
    trans_duration = 0.35
    trans_direction = "out"
    teleport_hold_start = None

    # Kamehameha states
    kame_state = "IDLE"          # "IDLE", "CHARGING", "FIRING"
    kame_charge_start = None
    kame_charge_duration = 1.3   # seconds to reach 100%
    kame_fire_start = None
    kame_fire_duration = 0.8     # blast duration
    kame_last_center = (actual_w // 2, actual_h // 2)
    smooth_kame_center = None

    show_pip = not args.no_pip
    show_caption = not args.no_caption
    caption_text = args.caption
    debug_mode = True
    sound_enabled = args.sound

    # Performance FPS tracking
    fps_history = []
    last_frame_time = time.time()
    current_fps = 30.0

    print("[INFO] Goku techniques ready!\n")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            if args.video:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            else:
                time.sleep(0.03)
                continue

        # Apply rotation (e.g. for phone cameras/DroidCam) and mirror flip
        frame = apply_camera_transforms(frame, rotation_angle, flip_mirror)

        # Dynamic dimension check if rotated at runtime
        cur_h, cur_w = frame.shape[:2]
        if cur_w != actual_w or cur_h != actual_h:
            actual_w, actual_h = cur_w, cur_h
            screen_capturer.target_w = actual_w
            screen_capturer.target_h = actual_h
            if background is not None:
                background = cv2.resize(background, (actual_w, actual_h))

        if background is None:
            background = frame.copy()
            cv2.imwrite(args.bg_path, background)

        if teleport_mode == "screen":
            alt_frame = screen_capturer.capture()
        else:
            alt_frame = background.copy()

        now = time.time()
        dt = now - last_frame_time
        last_frame_time = now
        if dt > 0:
            fps_history.append(1.0 / dt)
            if len(fps_history) > 15:
                fps_history.pop(0)
            current_fps = sum(fps_history) / len(fps_history)

        is_teleport_touch, is_kame_cupped, kame_center_detected, debug_info = detector.detect(frame)

        # -------------------------------------------------------------------
        # 1. Teleport Logic (Instant Transmission)
        # -------------------------------------------------------------------
        teleport_charge_ratio = 0.0
        if is_teleport_touch and not is_transitioning and kame_state == "IDLE":
            if teleport_hold_start is None:
                teleport_hold_start = now
                target_str = "Returning" if is_teleported else f"Teleporting to {teleport_mode.upper()}"
                print(f"[{target_str}] Forehead touch detected! Charging...")

            elapsed_hold = now - teleport_hold_start
            teleport_charge_ratio = min(1.0, elapsed_hold / args.hold_time)

            if teleport_charge_ratio >= 1.0:
                is_transitioning = True
                trans_start_time = now
                trans_direction = "in" if is_teleported else "out"
                teleport_hold_start = None

                action_name = "⚡ REAPPEAR! ⚡" if is_teleported else f"⚡ TELEPORTED TO {teleport_mode.upper()}! ⚡"
                print(action_name)
                play_sound(sounds["teleport"], sound_enabled)
        else:
            teleport_hold_start = None

        # -------------------------------------------------------------------
        # 2. Kamehameha Logic
        # -------------------------------------------------------------------
        kame_charge_pct = 0.0

        if kame_center_detected is not None:
            if smooth_kame_center is None:
                smooth_kame_center = kame_center_detected
            else:
                # Smooth Exponential Moving Average to prevent any jitter
                sx = int(smooth_kame_center[0] * 0.72 + kame_center_detected[0] * 0.28)
                sy = int(smooth_kame_center[1] * 0.72 + kame_center_detected[1] * 0.28)
                smooth_kame_center = (sx, sy)
            kame_last_center = smooth_kame_center

        if kame_state == "IDLE":
            if is_kame_cupped and not is_teleported and not is_transitioning:
                kame_state = "CHARGING"
                kame_charge_start = now
                print("⚡ [KAMEHAMEHA] Hands cupped close! KA... ME... HA... ME...")
                play_sound(sounds["charge"], sound_enabled)

        elif kame_state == "CHARGING":
            elapsed_charge = now - kame_charge_start
            kame_charge_pct = min(1.0, elapsed_charge / kame_charge_duration)

            # Fire if hands pushed forward / separated after charging >= 70%
            if not is_kame_cupped:
                if kame_charge_pct >= 0.70:
                    kame_state = "FIRING"
                    kame_fire_start = now
                    print("💥💥💥 [KAMEHAMEHA] ...HAAAAAA!!!!!! 💥💥💥")
                    play_sound(sounds["blast"], sound_enabled)
                else:
                    kame_state = "IDLE"
                    kame_charge_start = None
                    smooth_kame_center = None
            elif kame_charge_pct >= 1.0 and elapsed_charge > 2.0:
                # Auto-fire after holding at full charge
                kame_state = "FIRING"
                kame_fire_start = now
                print("💥💥💥 [KAMEHAMEHA] ...HAAAAAA!!!!!! 💥💥💥")
                play_sound(sounds["blast"], sound_enabled)

        elif kame_state == "FIRING":
            fire_elapsed = now - kame_fire_start
            if fire_elapsed >= kame_fire_duration:
                kame_state = "IDLE"
                kame_fire_start = None
                smooth_kame_center = None

        # -------------------------------------------------------------------
        # 3. Base Frame Composition
        # -------------------------------------------------------------------
        if is_transitioning:
            trans_elapsed = now - trans_start_time
            trans_progress = trans_elapsed / trans_duration
            if trans_progress >= 1.0:
                is_transitioning = False
                is_teleported = (trans_direction == "out")
                output_frame = alt_frame.copy() if is_teleported else frame.copy()
            else:
                if trans_direction == "out":
                    output_frame = apply_teleport_fx(frame, alt_frame, trans_progress)
                else:
                    output_frame = apply_teleport_fx(alt_frame, frame, trans_progress)
        else:
            output_frame = alt_frame.copy() if is_teleported else frame.copy()

        # Apply Kamehameha visual FX on output frame
        if kame_state == "CHARGING":
            output_frame = draw_kamehameha_charge(output_frame, kame_last_center, kame_charge_pct, now)
        elif kame_state == "FIRING":
            blast_progress = (now - kame_fire_start) / kame_fire_duration
            output_frame = draw_kamehameha_beam(output_frame, kame_last_center, blast_progress)

        # Apply POV Meme Caption Overlay (burns into virtual camera, preview, and recording)
        if show_caption and caption_text:
            output_frame = draw_meme_caption(output_frame, caption_text)

        preview_frame = output_frame.copy()

        # -------------------------------------------------------------------
        # 4. HUD, PIP, and Overlays
        # -------------------------------------------------------------------
        # PIP Thumbnail (when teleported)
        if is_teleported and not is_transitioning and show_pip:
            pip_h, pip_w = int(actual_h * 0.28), int(actual_w * 0.28)
            pip_img = cv2.resize(frame, (pip_w, pip_h))
            cv2.rectangle(pip_img, (0, 0), (pip_w - 1, pip_h - 1), (0, 255, 255), 2)
            preview_frame[actual_h - pip_h - 15 : actual_h - 15, actual_w - pip_w - 15 : actual_w - 15] = pip_img
            cv2.putText(preview_frame, "PIP: TOUCH FOREHEAD TO RETURN (P: HIDE)",
                        (actual_w - pip_w - 15, actual_h - pip_h - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)

        # Kamehameha Chant Overlay
        if kame_state == "CHARGING":
            if kame_charge_pct < 0.25:
                chant = "KA..."
            elif kame_charge_pct < 0.50:
                chant = "KA... ME..."
            elif kame_charge_pct < 0.75:
                chant = "KA... ME... HA..."
            else:
                chant = "KA... ME... HA... ME... (PUSH FORWARD TO FIRE!)"
            cv2.putText(preview_frame, chant, (actual_w // 2 - 250, actual_h - 60),
                        cv2.FONT_HERSHEY_TRIPLEX, 1.0, (255, 240, 100), 2, cv2.LINE_AA)

        elif kame_state == "FIRING":
            cv2.putText(preview_frame, "...HAAAAAAA!!!!!!!", (actual_w // 2 - 220, actual_h // 2),
                        cv2.FONT_HERSHEY_TRIPLEX, 1.6, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(preview_frame, "...HAAAAAAA!!!!!!!", (actual_w // 2 - 220, actual_h // 2),
                        cv2.FONT_HERSHEY_TRIPLEX, 1.6, (255, 200, 50), 2, cv2.LINE_AA)

        # Teleport Charging Bar
        if teleport_charge_ratio > 0.0:
            bar_w, bar_h = 320, 30
            bx, by = 20, actual_h - 48
            cv2.rectangle(preview_frame, (bx - 2, by - 2), (bx + bar_w + 2, by + bar_h + 2), (0, 0, 0), -1)
            fill_w = int(bar_w * teleport_charge_ratio)
            cv2.rectangle(preview_frame, (bx, by), (bx + fill_w, by + bar_h), (0, 215, 255), -1)
            cv2.rectangle(preview_frame, (bx, by), (bx + bar_w, by + bar_h), (255, 255, 255), 2)
            pct = int(teleport_charge_ratio * 100)
            cv2.putText(preview_frame, f"⚡ TELEPORT: {pct}%", (bx + 12, by + 21),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 2, cv2.LINE_AA)

        # Debug HUD
        if debug_mode and debug_info and not is_teleported and kame_state == "IDLE":
            fbox = debug_info["forehead_box"]
            if fbox is not None:
                bx1, by1, bx2, by2 = fbox
                color = (0, 255, 0) if is_teleport_touch else (255, 200, 0)
                cv2.rectangle(preview_frame, (bx1, by1), (bx2, by2), color, 2)
                tag = "⚡ IN ZONE! (HOLD TO TELEPORT)" if is_teleport_touch else "TARGET: TOUCH FOREHEAD"
                cv2.putText(preview_frame, tag, (bx1, max(20, by1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)

            for pt in debug_info["fingertips"]:
                cv2.circle(preview_frame, pt, 7, (0, 255, 0) if is_teleport_touch else (0, 165, 255), -1)
                cv2.circle(preview_frame, pt, 9, (255, 255, 255), 1)

            mode_lbl = f"MODE [M]: {'DESKTOP SCREEN' if teleport_mode == 'screen' else 'EMPTY ROOM'} | ROT [R]: {rotation_angle}°"
            cv2.putText(preview_frame, mode_lbl, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(preview_frame, f"FPS: {current_fps:.1f} (ZERO-LAG)", (actual_w - 180, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(preview_frame, "POSE 1: FINGERS ON FOREHEAD -> TELEPORT", (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(preview_frame, "POSE 2: CUP HANDS AT HIP -> KAMEHAMEHA", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)

        # Output to virtual cam and writer
        if vcam is not None:
            try:
                if output_frame.shape[1] != vcam.width or output_frame.shape[0] != vcam.height:
                    send_frame = cv2.resize(output_frame, (vcam.width, vcam.height))
                else:
                    send_frame = output_frame
                vcam.send(send_frame)
            except Exception:
                pass
        if writer is not None:
            writer.write(output_frame)

        # Show preview window
        cv2.imshow("Webcam - Goku Techniques (Teleport & Kamehameha)", preview_frame)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('k'), ord('K')):  # Instant Kamehameha test
            kame_state = "FIRING"
            kame_fire_start = now
            kame_last_center = (actual_w // 2, actual_h // 2 + 50)
            print("💥 [MANUAL KAMEHAMEHA] ...HAAAAAA!!!!!!")
            play_sound(sounds["blast"], sound_enabled)
        elif key in (ord(' '), ord('t'), ord('T')):  # Manual Teleport toggle
            if not is_transitioning:
                is_transitioning = True
                trans_start_time = now
                trans_direction = "in" if is_teleported else "out"
                play_sound(sounds["teleport"], sound_enabled)
        elif key in (ord('p'), ord('P'), ord('h'), ord('H')):  # Toggle PIP
            show_pip = not show_pip
            print(f"[PIP] Picture-in-Picture: {'SHOWN' if show_pip else 'HIDDEN'}")
        elif key in (ord('c'), ord('C')):  # Toggle POV caption
            show_caption = not show_caption
            print(f"[CAPTION] POV Banner: {'SHOWN' if show_caption else 'HIDDEN'}")
        elif key in (ord('r'), ord('R')):  # Rotate camera 90 degrees
            rotation_angle = (rotation_angle + 90) % 360
            print(f"[CAMERA] Rotation: {rotation_angle}°")
        elif key in (ord('f'), ord('F')):  # Toggle horizontal flip
            flip_mirror = not flip_mirror
            print(f"[CAMERA] Mirror flip: {'ENABLED' if flip_mirror else 'DISABLED'}")
        elif key in (ord('m'), ord('M')):  # Mode toggle
            teleport_mode = "bg" if teleport_mode == "screen" else "screen"
            print(f"[MODE] Teleport destination: {teleport_mode.upper()}")
        elif key in (ord('b'), ord('B')):
            background = frame.copy()
            cv2.imwrite(args.bg_path, background)
            print(f"[INFO] Background updated -> {args.bg_path}")
        elif key in (ord('d'), ord('D')):
            debug_mode = not debug_mode
        elif key in (ord('s'), ord('S')):
            sound_enabled = not sound_enabled

    cap.release()
    if writer is not None:
        writer.release()
    if vcam is not None:
        vcam.close()
    cv2.destroyAllWindows()
    print("[INFO] Script stopped.")


if __name__ == "__main__":
    main()
