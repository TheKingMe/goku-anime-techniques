# 💥 Goku Anime Techniques: Instant Transmission & Kamehameha

Combines two legendary Dragon Ball techniques in your webcam / video calls (Zoom, Google Meet, Teams, Discord):

---

## ⚡ Real-Time Zero-Lag Performance (DroidCam / Wi-Fi Streams)
- **Threaded Buffer Flushing**: OpenCV normally buffers frames over Wi-Fi, causing growing delay. Our new **`ZeroLagCamera`** continuously flushes the internal queue in a background thread, ensuring **0 ms latency** and true real-time video!
- **Fast Downscaled AI Inference**: MediaPipe runs on an optimized downscaled resolution for lightning-fast detection (~20ms), boosting framerates to **30+ FPS**.
- **Live FPS Counter**: Displays real-time framerate on screen (`FPS: 30.0 (ZERO-LAG)`).

---

## 🥋 The Two Techniques

### 1. ⚡ Instant Transmission (Teleport)
- **Pose**: Touch your forehead or temple with two fingers (hold ~0.4s).
- **Effect**: Anime speedlines and vertical warp glitch -> you vanish into your **Live Desktop Screen** (or empty room).
- **Return**: Put fingers back on your forehead to warp back onto camera!

### 2. 💥 Kamehameha (Smooth & Strict Proximity)
- **Pose**: Cup **both hands close together** (palms/wrists touching or within a few centimeters) at your hip, ribs, or chest.
- **Strict Activation**: Only activates when **both hands are genuinely close together** (will not trigger accidentally when hands are apart).
- **Smooth Ki Orb**: Stabilized position tracking, breathing pulse glow, and crackling lightning sparks.
- **Chant**:
  - `KA...`
  - `ME...`
  - `HA...`
  - `ME... (PUSH FORWARD TO FIRE!)`
- **Firing**: Push both hands forward toward the camera!
- **Effect**: **`...HAAAAAAA!!!!!!!`** — Smooth expanding beam core, shockwave rings, and decaying camera shake.

---

## 🚀 Quick Start

### 1. Run with Laptop / USB Webcam
```bash
python goku_teleport.py
```

### 2. Run with Phone Camera (DroidCam over Wi-Fi, 0ms Lag)
```bash
python goku_teleport.py --camera http://192.168.1.XXX:4747/video
```
> **Phone Orientation Tip**:
> - If your phone video is sideways or upside down, use `--rotate 90` (or `180`, `270`). You can also tap **`R`** at any time while the window is open to rotate 90° live!
> - If using your phone's rear camera and you don't want mirror reflection, add `--no-flip` (or tap **`F`** live).

### 3. In Google Meet / Zoom / Teams:
- Open Settings ➔ Video ➔ Select Camera: **`OBS Virtual Camera`**.

---

## 🎮 Controls & Shortcuts

| Action / Key | What it Does |
|---|---|
| **Two Fingers to Forehead** | Instant Transmission: Teleport / Reappear |
| **Both Hands Cupped Close** | Charge **Kamehameha** (Push forward to FIRE!) |
| `K` | Instant manual **Kamehameha** blast test |
| `SPACE` or `T` | Instant manual **Teleport** toggle |
| `P` or `H` | **Hide / Show Picture-in-Picture (PIP)** box |
| `C` | Toggle **POV meme caption banner** |
| `R` | **Rotate camera 90°** clockwise (0° -> 90° -> 180° -> 270°) |
| `F` | Toggle **mirror flip** (selfie / rear camera) |
| `M` | Switch Teleport destination: Live Screen 💻 vs Empty Room 👻 |
| `B` | Capture current room background |
| `D` | Toggle Debug HUD & target zone |
| `S` | Toggle sound FX |
| `Q` or `ESC` | Quit |
