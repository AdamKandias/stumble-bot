import pyautogui
import time
import cv2
import numpy as np
from mss import mss
import random
import threading
import keyboard
import json
import os
import platform

# Import untuk window detection (Mac vs Windows)
if platform.system() == 'Darwin':  # macOS
    try:
        from AppKit import NSWorkspace, NSApplication
        MAC_AVAILABLE = True
    except ImportError:
        MAC_AVAILABLE = False
        print("⚠️ AppKit tidak tersedia, menggunakan fallback")
elif platform.system() == 'Windows':
    try:
        import pygetwindow as gw
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
else:
    MAC_AVAILABLE = False
    WINDOWS_AVAILABLE = False

auto_control_active = False
auto_control_thread = None
bot_paused = False

# Tracking untuk recovery choose_event
choose_event_start_time = None
in_recovery_mode = False
last_esc_press_time = None

# Tracking untuk event_menu counter
event_menu_consecutive_count = 0

# Tracking untuk leave_game counter
leave_game_consecutive_count = 0

# Load konfigurasi dari JSON
def load_config():
    """Load konfigurasi dari config.json"""
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Default config jika file tidak ada
        print("⚠️ config.json tidak ditemukan, menggunakan konfigurasi default")
        return {
            "game_area": {"top": 40, "left": 0, "width": 1024, "height": 768},
            "button_templates": {
                "ok": {"image": "ok.png", "click_pos": [485, 710]},
                "ok2": {"image": "ok2.png", "click_pos": [524, 540]},
                "event_menu": {"image": "event_menu.png", "click_pos": [471, 733]},
                "choose_event": {"image": "choose_event.png", "click_pos": [232, 423]},
                "play_event": {"image": "play_event.png", "click_pos": [652, 700]},
                "leave_game": {"image": "leave_game.png", "click_pos": [50, 720]},
                "claim": {"image": "claim.png", "click_pos": [800, 650]},
                "continue": {"image": "continue.png", "click_pos": [178, 694]},
                "skip": {"image": "skip.png", "click_pos": [100, 45]}
            },
            "settings": {
                "choose_event_timeout": 70,
                "esc_press_interval": 15,
                "event_menu_click_threshold": 3,
                "leave_game_esc_threshold": 3,
                "detection_threshold": 0.8
            }
        }

# Load konfigurasi
CONFIG = load_config()
GAME_AREA = CONFIG['game_area']
BUTTON_TEMPLATES = CONFIG['button_templates']
SETTINGS = CONFIG['settings']

# Convert click_pos dari list ke tuple untuk kompatibilitas
for name, config in BUTTON_TEMPLATES.items():
    if isinstance(config['click_pos'], list):
        config['click_pos'] = tuple(config['click_pos'])

# Load settings
CHOOSE_EVENT_TIMEOUT = SETTINGS.get('choose_event_timeout', 70)
ESC_PRESS_INTERVAL = SETTINGS.get('esc_press_interval', 15)
EVENT_MENU_CLICK_THRESHOLD = SETTINGS.get('event_menu_click_threshold', 3)
LEAVE_GAME_ESC_THRESHOLD = SETTINGS.get('leave_game_esc_threshold', 3)
DETECTION_THRESHOLD = SETTINGS.get('detection_threshold', 0.8)
 
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
                # Convert click_pos ke tuple jika masih list
                click_pos = config['click_pos']
                if isinstance(click_pos, list):
                    click_pos = tuple(click_pos)
                self.templates[name] = {
                    "template": template,
                    "click_pos": click_pos,
                    "threshold": DETECTION_THRESHOLD,
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

class WindowInfo:
    """Class untuk menyimpan info window"""
    def __init__(self, title, left, top, width, height):
        self.title = title
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.visible = True

def list_windows():
    """List semua window yang terbuka"""
    windows = []
    import subprocess
    
    if platform.system() == 'Darwin':  # macOS
        try:
            # Metode 1: Gunakan AppKit jika tersedia
            if MAC_AVAILABLE:
                try:
                    workspace = NSWorkspace.sharedWorkspace()
                    running_apps = workspace.runningApplications()
                    
                    for app in running_apps:
                        if app.isActive() or not app.isHidden():
                            app_name = app.localizedName()
                            if app_name and app_name not in ['', 'WindowServer', 'Dock', 'Finder']:
                                # Coba dapatkan window bounds dengan AppleScript (lebih cepat)
                                try:
                                    bounds_script = f'''
                                    tell application "System Events"
                                        try
                                            set appProcess to first process whose name is "{app_name}"
                                            if exists window 1 of appProcess then
                                                set winBounds to bounds of window 1 of appProcess
                                                return winBounds
                                            end if
                                        end try
                                    end tell
                                    '''
                                    bounds_result = subprocess.run(
                                        ['osascript', '-e', bounds_script],
                                        capture_output=True,
                                        text=True,
                                        timeout=1
                                    )
                                    if bounds_result.returncode == 0 and bounds_result.stdout.strip():
                                        bounds = [int(x.strip()) for x in bounds_result.stdout.strip().split(',')]
                                        if len(bounds) == 4:
                                            left, top, right, bottom = bounds
                                            width = right - left
                                            height = bottom - top
                                            if width > 100 and height > 100:  # Filter window yang terlalu kecil
                                                windows.append(WindowInfo(
                                                    app_name,
                                                    left, top, width, height
                                                ))
                                                continue
                                except:
                                    pass
                                
                                # Fallback: tambahkan dengan default size
                                windows.append(WindowInfo(
                                    app_name,
                                    0, 0, 1024, 768
                                ))
                except Exception as e:
                    print(f"⚠️ AppKit error: {str(e)}")
            
            # Metode 2: Jika AppKit gagal, gunakan AppleScript sederhana
            if not windows:
                try:
                    # List aplikasi yang sedang berjalan (lebih cepat)
                    script = 'tell application "System Events" to get name of every process whose background only is false'
                    result = subprocess.run(
                        ['osascript', '-e', script],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        # Parse hasil: "app1, app2, app3"
                        app_names = [name.strip().strip('"') for name in result.stdout.strip().split(',') if name.strip()]
                        
                        # Filter aplikasi yang tidak relevan
                        exclude = ['WindowServer', 'Dock', 'Finder', 'loginwindow', 'kernel_task']
                        app_names = [app for app in app_names if app not in exclude]
                        
                        for app_name in app_names[:20]:  # Limit untuk performa
                            windows.append(WindowInfo(
                                app_name,
                                0, 0, 1024, 768  # Default size, user bisa adjust
                            ))
                except Exception as e:
                    print(f"⚠️ AppleScript error: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ Error mendapatkan list windows (Mac): {str(e)}")
            
    elif platform.system() == 'Windows':
        try:
            if WINDOWS_AVAILABLE:
                all_windows = gw.getAllWindows()
                for w in all_windows:
                    if w.visible and w.title.strip():
                        windows.append(WindowInfo(
                            w.title,
                            w.left,
                            w.top,
                            w.width,
                            w.height
                        ))
        except Exception as e:
            print(f"⚠️ Error mendapatkan list windows (Windows): {str(e)}")
    
    # Remove duplicates berdasarkan title
    seen = set()
    unique_windows = []
    for win in windows:
        if win.title not in seen:
            seen.add(win.title)
            unique_windows.append(win)
    
    return unique_windows

def select_window():
    """Pilih window untuk di-detect"""
    global GAME_AREA, CONFIG
    
    print("\n🪟 Pilih Window/Aplikasi untuk di-detect:")
    print("="*50)
    
    windows = list_windows()
    
    if not windows:
        print("❌ Tidak ada window yang ditemukan!")
        print("\n💡 Kemungkinan penyebab:")
        print("   1. Aplikasi belum terbuka - Pastikan aplikasi (UTM, dll) sudah dibuka")
        print("   2. Permission belum diberikan - Di Mac perlu permission Accessibility")
        print("      → System Preferences → Security & Privacy → Privacy → Accessibility")
        print("      → Tambahkan Terminal/Python dan centang checkbox")
        print("      → Restart Terminal setelah memberikan permission")
        print("   3. Atau gunakan konfigurasi manual di config.json")
        
        manual = input("\n📝 Masukkan nama aplikasi manual? (y/n, default=n): ").lower()
        if manual == 'y':
            app_name = input("Nama aplikasi: ").strip()
            if app_name:
                # Coba dapatkan bounds
                try:
                    import subprocess
                    script = f'''
                    tell application "System Events"
                        try
                            set appProcess to first process whose name is "{app_name}"
                            if exists window 1 of appProcess then
                                set winBounds to bounds of window 1 of appProcess
                                return winBounds
                            end if
                        end try
                    end tell
                    '''
                    result = subprocess.run(
                        ['osascript', '-e', script],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        bounds = [int(x.strip()) for x in result.stdout.strip().split(',')]
                        if len(bounds) == 4:
                            left, top, right, bottom = bounds
                            width = right - left
                            height = bottom - top
                            GAME_AREA = {"top": top, "left": left, "width": width, "height": height}
                            CONFIG['game_area'] = GAME_AREA
                            CONFIG['selected_window'] = app_name
                            print(f"✅ Window ditemukan: {app_name} ({width}x{height})")
                            return True
                except:
                    pass
                
                # Jika gagal, gunakan default
                print(f"⚠️ Tidak bisa mendapatkan ukuran window, gunakan default")
                GAME_AREA = {"top": 0, "left": 0, "width": 1024, "height": 768}
                CONFIG['game_area'] = GAME_AREA
                CONFIG['selected_window'] = app_name
                return True
        
        return False
    
    # Tampilkan list windows
    print(f"\n📋 Ditemukan {len(windows)} window:")
    for i, window in enumerate(windows, 1):
        size_info = f"{window.width}x{window.height}" if window.width > 0 and window.height > 0 else "ukuran tidak valid"
        print(f"  {i}. {window.title[:60]} ({size_info})")
    
    print(f"\n  0. Gunakan konfigurasi manual (skip)")
    
    try:
        choice = input("\nPilih window (0-{}): ".format(len(windows)))
        choice = int(choice)
        
        if choice == 0:
            print("✅ Menggunakan konfigurasi manual dari config.json")
            return True
        
        if 1 <= choice <= len(windows):
            selected_window = windows[choice - 1]
            
            # Dapatkan posisi dan ukuran window
            left = selected_window.left
            top = selected_window.top
            width = selected_window.width
            height = selected_window.height
            
            print(f"\n✅ Window dipilih: {selected_window.title}")
            print(f"   Posisi: ({left}, {top})")
            print(f"   Ukuran: {width}x{height}")
            
            # Update game_area
            GAME_AREA = {
                "top": top,
                "left": left,
                "width": width,
                "height": height
            }
            
            # Update config dan simpan
            CONFIG['game_area'] = GAME_AREA
            CONFIG['selected_window'] = selected_window.title
            
            # Simpan ke config.json
            try:
                with open("config.json", 'w', encoding='utf-8') as f:
                    json.dump(CONFIG, f, indent=2, ensure_ascii=False)
                print("💾 Konfigurasi disimpan ke config.json")
            except Exception as e:
                print(f"⚠️ Gagal menyimpan config: {str(e)}")
            
            return True
        else:
            print("❌ Pilihan tidak valid!")
            return False
            
    except ValueError:
        print("❌ Input tidak valid! Harus angka.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def refresh_window_selection():
    """Refresh window selection jika window sudah dipilih sebelumnya"""
    global GAME_AREA, CONFIG
    
    # Cek apakah ada selected_window di config
    if 'selected_window' in CONFIG and CONFIG['selected_window']:
        window_title = CONFIG['selected_window']
        print(f"\n🔍 Mencari window: {window_title}")
        
        try:
            windows = list_windows()
            # Cari window dengan title yang sama
            for window in windows:
                if window.title == window_title or window_title in window.title:
                    # Update game_area
                    GAME_AREA = {
                        "top": window.top,
                        "left": window.left,
                        "width": window.width,
                        "height": window.height
                    }
                    CONFIG['game_area'] = GAME_AREA
                    print(f"✅ Window ditemukan: {window.title}")
                    print(f"   Posisi: ({window.left}, {window.top})")
                    print(f"   Ukuran: {window.width}x{window.height}")
                    return True
            
            print(f"⚠️ Window '{window_title}' tidak ditemukan!")
            print("💡 Window mungkin sudah ditutup atau berganti nama.")
            return False
            
        except Exception as e:
            print(f"⚠️ Error mencari window: {str(e)}")
            return False
    
    return False


def main():
    global bot_paused
    global auto_control_active
    global choose_event_start_time
    global in_recovery_mode
    global last_esc_press_time
    global event_menu_consecutive_count
    global leave_game_consecutive_count
    global GAME_AREA, CONFIG
    
    print("🎮 Stumble Guys Bot") 
    print("="*40)
    
    # Coba refresh window selection dari config
    window_found = refresh_window_selection()
    
    # Tampilkan info konfigurasi
    print(f"\n🖥️ Area Game:")
    print(f"Top: {GAME_AREA['top']}, Left: {GAME_AREA['left']}")
    print(f"Width: {GAME_AREA['width']}, Height: {GAME_AREA['height']}")
    if 'selected_window' in CONFIG and CONFIG['selected_window']:
        print(f"Window: {CONFIG['selected_window']}")
    
    # Tanya apakah ingin pilih window baru
    if not window_found or input("\n🪟 Pilih window baru? (y/n, default=n): ").lower() == 'y':
        if not select_window():
            print("⚠️ Menggunakan konfigurasi manual dari config.json")
    
    # Tampilkan info konfigurasi setelah update
    print(f"\n🖥️ Area Game (Final):")
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
                
                # Prioritaskan ok dan ok2 jika terdeteksi
                ok_button = None
                ok2_button = None
                other_buttons = []
                choose_event_button = None
                event_menu_button = None
                leave_game_button = None
                
                for btn in buttons:
                    if btn['name'] == 'ok':
                        ok_button = btn
                    elif btn['name'] == 'ok2':
                        ok2_button = btn
                    elif btn['name'] == 'choose_event':
                        choose_event_button = btn
                    elif btn['name'] == 'event_menu':
                        # Simpan event_menu tanpa filter confidence
                        event_menu_button = btn
                    elif btn['name'] == 'leave_game':
                        # Simpan leave_game untuk counter tracking
                        leave_game_button = btn
                    else:
                        other_buttons.append(btn)
                
                # Handle counter event_menu
                if event_menu_button:
                    event_menu_consecutive_count += 1
                    print(f"📊 event_menu terdeteksi ({event_menu_consecutive_count}/{EVENT_MENU_CLICK_THRESHOLD} berturut-turut) - Confidence: {event_menu_button['confidence']:.2f}")
                else:
                    # Reset counter jika event_menu tidak terdeteksi
                    if event_menu_consecutive_count > 0:
                        print(f"✅ event_menu tidak terdeteksi, reset counter (sebelumnya: {event_menu_consecutive_count})")
                        event_menu_consecutive_count = 0
                
                # Handle counter leave_game
                if leave_game_button:
                    leave_game_consecutive_count += 1
                    print(f"📊 leave_game terdeteksi ({leave_game_consecutive_count}/{LEAVE_GAME_ESC_THRESHOLD} berturut-turut) - Confidence: {leave_game_button['confidence']:.2f}")
                    
                    # Jika sudah 3 kali berturut-turut, tekan ESC
                    if leave_game_consecutive_count >= LEAVE_GAME_ESC_THRESHOLD:
                        print(f"🔧 leave_game terdeteksi {leave_game_consecutive_count} kali berturut-turut, tekan ESC")
                        pyautogui.press('esc')
                        time.sleep(0.5)
                        # Reset counter
                        leave_game_consecutive_count = 0
                else:
                    # Reset counter jika leave_game tidak terdeteksi
                    if leave_game_consecutive_count > 0:
                        print(f"✅ leave_game tidak terdeteksi, reset counter (sebelumnya: {leave_game_consecutive_count})")
                        leave_game_consecutive_count = 0
                
                # Klik ok atau ok2 terlebih dahulu jika ada (prioritas tertinggi)
                if ok2_button:
                    print(f"🎯 Detected {ok2_button['name']} (Confidence: {ok2_button['confidence']:.2f}) - PRIORITAS")
                    click_in_game(*ok2_button['click_pos'])
                    time.sleep(0.5)  # Beri waktu untuk modal tertutup
                    # Reset choose_event timer dan counter jika ok2 diklik
                    choose_event_start_time = None
                    in_recovery_mode = False
                    last_esc_press_time = None
                    event_menu_consecutive_count = 0
                    leave_game_consecutive_count = 0
                elif ok_button:
                    print(f"🎯 Detected {ok_button['name']} (Confidence: {ok_button['confidence']:.2f}) - PRIORITAS")
                    click_in_game(*ok_button['click_pos'])
                    time.sleep(0.5)  # Beri waktu untuk modal tertutup
                    # Reset choose_event timer dan counter jika ok diklik
                    choose_event_start_time = None
                    in_recovery_mode = False
                    last_esc_press_time = None
                    event_menu_consecutive_count = 0
                    leave_game_consecutive_count = 0
                else:
                    # Handle recovery mode untuk choose_event loading bug
                    if choose_event_button:
                        current_time = time.time()
                        
                        # Mulai tracking waktu jika baru pertama kali terdeteksi
                        if choose_event_start_time is None:
                            choose_event_start_time = current_time
                            print(f"⏱️ Mulai tracking choose_event...")
                        
                        # Cek apakah sudah timeout (70 detik)
                        elapsed_time = current_time - choose_event_start_time
                        if elapsed_time >= CHOOSE_EVENT_TIMEOUT and not in_recovery_mode:
                            print(f"⚠️ choose_event terdeteksi selama {elapsed_time:.1f} detik - MULAI RECOVERY MODE")
                            in_recovery_mode = True
                        
                        # Jika dalam recovery mode, tekan ESC setiap 15 detik sampai event_menu terdeteksi
                        if in_recovery_mode:
                            if event_menu_button:
                                # event_menu terdeteksi, recovery berhasil
                                print(f"✅ Recovery berhasil! event_menu terdeteksi")
                                choose_event_start_time = None
                                in_recovery_mode = False
                                last_esc_press_time = None
                                # Klik event_menu untuk masuk lagi
                                print(f"🎯 Detected {event_menu_button['name']} (Confidence: {event_menu_button['confidence']:.2f})")
                                click_in_game(*event_menu_button['click_pos'])
                                time.sleep(1)
                            else:
                                # Tekan ESC untuk recovery (hanya setiap 15 detik)
                                should_press_esc = False
                                if last_esc_press_time is None:
                                    # ESC belum pernah ditekan, tekan sekarang
                                    should_press_esc = True
                                else:
                                    # Cek apakah sudah 15 detik sejak ESC terakhir
                                    time_since_last_esc = current_time - last_esc_press_time
                                    if time_since_last_esc >= ESC_PRESS_INTERVAL:
                                        should_press_esc = True
                                
                                if should_press_esc:
                                    print(f"🔧 Tekan ESC untuk recovery... (elapsed: {elapsed_time:.1f}s)")
                                    pyautogui.press('esc')
                                    last_esc_press_time = current_time
                                    time.sleep(0.5)
                                else:
                                    time_since_last_esc = current_time - last_esc_press_time
                                    print(f"⏳ Menunggu untuk tekan ESC lagi... ({ESC_PRESS_INTERVAL - time_since_last_esc:.1f}s lagi)")
                        else:
                            # Normal flow: klik choose_event
                            print(f"🎯 Detected {choose_event_button['name']} (Confidence: {choose_event_button['confidence']:.2f}) - Elapsed: {elapsed_time:.1f}s")
                            click_in_game(*choose_event_button['click_pos'])
                    else:
                        # choose_event tidak terdeteksi, reset timer
                        if choose_event_start_time is not None:
                            print(f"✅ choose_event tidak terdeteksi lagi, reset timer")
                            choose_event_start_time = None
                            in_recovery_mode = False
                            last_esc_press_time = None
                    
                    # Handle event_menu: jika sudah 3 kali berturut-turut, klik ok2. Jika belum, klik event_menu normal
                    if event_menu_button and not in_recovery_mode:
                        if event_menu_consecutive_count >= EVENT_MENU_CLICK_THRESHOLD:
                            # Sudah 3 kali berturut-turut, klik ok2
                            ok2_pos = BUTTON_TEMPLATES['ok2']['click_pos']
                            print(f"🔧 event_menu terdeteksi {event_menu_consecutive_count} kali berturut-turut, klik ok2 di posisi {ok2_pos}")
                            click_in_game(*ok2_pos)
                            time.sleep(0.5)
                            # Reset counter dan timer
                            event_menu_consecutive_count = 0
                            choose_event_start_time = None
                            in_recovery_mode = False
                            last_esc_press_time = None
                        else:
                            # Belum mencapai threshold, klik event_menu normal
                            # JANGAN reset counter di sini, biarkan counter terus bertambah sampai mencapai 3
                            # Counter hanya di-reset jika event_menu tidak terdeteksi lagi (berarti berhasil diklik)
                            print(f"🎯 Detected {event_menu_button['name']} (Confidence: {event_menu_button['confidence']:.2f})")
                            click_in_game(*event_menu_button['click_pos'])
                            # Reset choose_event timer saat klik event_menu
                            choose_event_start_time = None
                            last_esc_press_time = None
                            # Counter TIDAK di-reset di sini, akan di-reset jika event_menu tidak terdeteksi di iterasi berikutnya
                    
                    # Klik tombol lain seperti biasa
                    for btn in other_buttons:
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
                            # Reset choose_event timer saat keluar dari game
                            choose_event_start_time = None
                            in_recovery_mode = False
                            last_esc_press_time = None
                            # Reset leave_game counter saat keluar dari game
                            leave_game_consecutive_count = 0
                    
                    # Handle leave_game: jika belum mencapai threshold, klik normal
                    # (jika sudah >= 3, ESC sudah ditekan di bagian counter di atas)
                    if leave_game_button and leave_game_consecutive_count < LEAVE_GAME_ESC_THRESHOLD:
                        print(f"🎯 Detected {leave_game_button['name']} (Confidence: {leave_game_button['confidence']:.2f})")
                        click_in_game(*leave_game_button['click_pos'])
                        # Reset choose_event timer saat klik leave_game
                        choose_event_start_time = None
                        in_recovery_mode = False
                        last_esc_press_time = None
                        # Counter TIDAK di-reset di sini, akan di-reset jika leave_game tidak terdeteksi di iterasi berikutnya

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