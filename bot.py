import pyautogui
import time
import cv2
import numpy as np
from mss import mss
import random
import threading
import keyboard

auto_control_active = False
auto_control_thread = None
bot_paused = False

# Konfigurasi dasar
GAME_AREA = {
    "top": 40,
    "left": 0,
    "width": 1024,
    "height": 768
}

BUTTON_TEMPLATES = {
    "event_menu": {
        "image": "event_menu.png", 
        "click_pos": (471, 733) 
    },
    "choose_event": {
        "image": "choose_event.png", 
        "click_pos": (532, 423) 
    },
    "play_event": {
        "image": "play_event.png",
        "click_pos": (712, 700)
    },
    "leave_game": { 
        "image": "leave_game.png",
        "click_pos": (50 , 720)
    },
    "claim": {
        "image": "claim.png",
        "click_pos": (800, 650)
    },
    "continue": {
        "image": "continue.png",
        "click_pos": (178, 694)
    },
    "skip": {
        "image": "skip.png",
        "click_pos": (100, 45)
    },
    "ok": {
        "image": "ok.png",
        "click_pos": (485, 710)
    },
}
 
sct = mss()

class ButtonDetector:
    def __init__(self, show_preview=False):
        self.show_preview = show_preview
        self.templates = {}
        self.load_templates()
        
        if self.show_preview:
            cv2.namedWindow('Bot Preview', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Bot Preview', 800, 600)
            cv2.setMouseCallback('Bot Preview', self.on_mouse_click)
            self.last_click_pos = None  # simpan posisi klik terakhir

    
    def load_templates(self):
        """Memuat semua template tombol"""
        print("\n🔧 Konfigurasi Tombol yang Aktif:")
        for name, config in BUTTON_TEMPLATES.items():
            try:
                template = cv2.imread(config['image'], cv2.IMREAD_COLOR)
                if template is None:
                    print(f"⚠️ {name}: Template tidak ditemukan ({config['image']})")
                    continue
                
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                self.templates[name] = {
                    "template": template,
                    "click_pos": config['click_pos'],
                    "threshold": 0.8,
                    "color": (np.random.randint(0, 255), 
                             np.random.randint(0, 255), 
                             np.random.randint(0, 255))  # Warna unik untuk setiap tombol
                }
                print(f"✅ {name}:")
                print(f"   - File: {config['image']}")
                print(f"   - Posisi klik: {config['click_pos']}")
            except Exception as e:
                print(f"❌ Gagal memuat template {name}: {str(e)}")
    
    def draw_button_config(self, frame):
        """Menggambar konfigurasi tombol di preview"""
        for name, data in self.templates.items():
            # Gambar titik klik
            cv2.circle(frame, data['click_pos'], 8, data['color'], -1)
            cv2.putText(frame, f"{name} (click)", 
                       (data['click_pos'][0] + 15, data['click_pos'][1] + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, data['color'], 2)
            
            # Gambar area template (jika ada)
            if 'template' in data:
                h, w = data['template'].shape
                cv2.rectangle(frame, 
                            (data['click_pos'][0] - w//2, data['click_pos'][1] - h//2),
                            (data['click_pos'][0] + w//2, data['click_pos'][1] + h//2),
                            data['color'], 1)
        if self.last_click_pos:
            cv2.circle(frame, self.last_click_pos, 5, (255, 255, 255), -1)
            cv2.putText(frame, f"{self.last_click_pos}", 
                        (self.last_click_pos[0] + 10, self.last_click_pos[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def detect_buttons(self, frame):
        """Mendeteksi tombol dan menampilkan preview"""
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected = []
        
        if self.show_preview:
            self.draw_button_config(frame)
        
        for name, data in self.templates.items():
            if 'template' not in data:
                continue
                
            template = data["template"]
            res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > data["threshold"]:
                detected.append({
                    "name": name,
                    "position": max_loc,
                    "confidence": max_val,
                    "click_pos": data["click_pos"],
                    "color": data["color"]
                })
                
                if self.show_preview:
                    h, w = template.shape
                    top_left = max_loc
                    bottom_right = (top_left[0] + w, top_left[1] + h)
                    cv2.rectangle(frame, top_left, bottom_right, data['color'], 2)
                    cv2.putText(frame, f"{name} ({max_val:.2f})", 
                               (top_left[0], top_left[1]-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, data['color'], 2)
        
        if self.show_preview:
            cv2.imshow('Bot Preview', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                exit()
        
        return detected

    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"🖱️ Klik di posisi Preview: ({x}, {y})")
            self.last_click_pos = (x, y)


def get_game_frame():
    img = np.array(sct.grab(GAME_AREA))
    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def click_in_game(x_rel, y_rel):
    x_abs = GAME_AREA['left'] + x_rel
    y_abs = GAME_AREA['top'] + y_rel
    pyautogui.click(x=x_abs, y=y_abs)

def auto_game_control():
    global auto_control_active
    print("🎮 Auto Control Aktif")

    while auto_control_active:
        pyautogui.press('space')
        arrow = random.choice(['left', 'right', 'up', 'down', '1'])
        pyautogui.keyDown(arrow)
        time.sleep(0.2)
        pyautogui.keyUp(arrow)
        time.sleep(0.3)

def keyboard_listener():
    global bot_paused
    while True:
        if keyboard.is_pressed('p'):  # Tekan 'p' untuk pause/resume
            bot_paused = not bot_paused
            if bot_paused:
                print("⏸️ Bot dijeda.")
            else:
                print("▶️ Bot dilanjutkan.")
            time.sleep(1)  # Hindari multiple toggle karena tombol ditekan lama


def main():
    global bot_paused
    global auto_control_active
    print("🎮 Stumble Guys Bot") 
    print("="*40)
    
    # Tampilkan info konfigurasi
    print(f"\n🖥️ Area Game:")
    print(f"Top: {GAME_AREA['top']}, Left: {GAME_AREA['left']}")
    print(f"Width: {GAME_AREA['width']}, Height: {GAME_AREA['height']}")
    
    print("\nPilih mode:")
    print("1. Run Bot (Silent Mode)")
    print("2. Run Bot with Preview")
    print("3. Exit")
    
    choice = input("\nPilihan (1-3): ")
    
    if choice == '3':
        exit()
    
    show_preview = (choice == '2')
    detector = ButtonDetector(show_preview=show_preview)
    
    print("\n🤖 Bot Aktif")
    print("Tekan Ctrl+C untuk menghentikan")
    
    # Mulai listener keyboard
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()

    try:
        while True:
            if not bot_paused:
                frame = get_game_frame()
                buttons = detector.detect_buttons(frame)
                
                for btn in buttons:
                    print(f"🎯 Detected {btn['name']} (Confidence: {btn['confidence']:.2f})")
                    click_in_game(*btn['click_pos'])

                    if btn['name'] == 'play_event':
                        if not auto_control_active:
                            auto_control_active = True
                            auto_control_thread = threading.Thread(target=auto_game_control)
                            auto_control_thread.start()
                            print("▶️ Mulai kontrol otomatis...")

                    if btn['name'] == 'leave_game' or btn['name'] == 'claim' or btn['name'] == 'continue':
                        if auto_control_active:
                            auto_control_active = False
                            if auto_control_thread:
                                auto_control_thread.join()
                            print("⏹️ Kontrol otomatis dihentikan.")

                time.sleep(1)
            else:
                # Tetap ambil frame agar preview tidak freeze
                if detector.show_preview:
                    frame = get_game_frame()
                    detector.draw_button_config(frame)
                    cv2.imshow('Bot Preview', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

    except KeyboardInterrupt:
        print("\nBot dihentikan.")
        if show_preview:
            cv2.destroyAllWindows()

if __name__ == "__main__": 
     main()