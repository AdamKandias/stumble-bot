import pyautogui
import time
import cv2
import numpy as np
from mss import mss

# Load template ELIMINATED
template = cv2.imread('eliminated.png')
scale_percent = 50  # misalnya perkecil 50%
width = int(template.shape[1] * scale_percent / 100)
height = int(template.shape[0] * scale_percent / 100)
template = cv2.resize(template, (width, height), interpolation=cv2.INTER_AREA)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
tH, tW = template_gray.shape[:2]

# Area game di layar (ubah sesuai posisi window game kamu)
monitor = {"top": 100, "left": 100, "width": 800, "height": 600}    
sct = mss()

def get_game_frame():
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return frame

def is_eliminated(frame):
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    fH, fW = frame_gray.shape[:2]
    if fH < tH or fW < tW:
        print("⚠️ Frame terlalu kecil dibanding template!")
        return False

    result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    print(f"[DEBUG] Confidence match: {max_val:.2f}")
    return max_val > 0.85  # bisa disesuaikan

def detect_red_obstacle(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if cv2.contourArea(cnt) > 300:
            return True
    return False

def auto_play():
    print("Bot aktif. Tekan Ctrl+C untuk keluar.")
    while True:
        frame = get_game_frame()

        if is_eliminated(frame):
            print("[!] Tereliminasi. Klik 'Play Again'.")
            pyautogui.click(x=900, y=650)  # Ubah X,Y sesuai posisi tombol
            time.sleep(5)
            continue

        if detect_red_obstacle(frame):
            print("→ Rintangan terdeteksi. Lompat!")
            pyautogui.press('space')
        else:
            pyautogui.keyDown('up')
            time.sleep(0.2)
            pyautogui.keyUp('up')

        time.sleep(0.1)  # Delay frame (10 fps)

try:
    auto_play()
except KeyboardInterrupt:
    print("\nBot dihentikan.")
