#!/usr/bin/env python3
"""
GUI Editor untuk mengedit konfigurasi tombol bot
Memungkinkan user untuk:
- Mengganti gambar template
- Mengatur posisi klik
- Preview gambar dan posisi
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import cv2
from PIL import Image, ImageTk
import numpy as np
from mss import mss

class ButtonEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Stumble Bot - Button Configuration Editor")
        self.root.geometry("1200x800")
        
        self.config_file = "config.json"
        self.config = self.load_config()
        self.current_button = None
        self.sct = mss()
        
        # Frame utama
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame kiri - List tombol
        left_frame = ttk.LabelFrame(main_frame, text="Daftar Tombol", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Listbox untuk tombol
        self.button_listbox = tk.Listbox(left_frame, width=20, height=15)
        self.button_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.button_listbox.bind('<<ListboxSelect>>', self.on_button_select)
        
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.button_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.button_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Refresh list
        self.refresh_button_list()
        
        # Frame kanan - Editor
        right_frame = ttk.LabelFrame(main_frame, text="Editor Konfigurasi", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Info tombol yang dipilih
        self.info_label = ttk.Label(right_frame, text="Pilih tombol dari list untuk mulai edit", font=("Arial", 12, "bold"))
        self.info_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Preview gambar
        preview_frame = ttk.LabelFrame(right_frame, text="Preview Gambar Template", padding="10")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Tidak ada gambar")
        self.preview_label.grid(row=0, column=0)
        
        # Frame untuk edit gambar
        image_frame = ttk.Frame(right_frame)
        image_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(image_frame, text="Ganti Gambar Template", command=self.change_image).grid(row=0, column=0, padx=5)
        ttk.Button(image_frame, text="Ambil Screenshot", command=self.capture_screenshot).grid(row=0, column=1, padx=5)
        
        self.image_path_label = ttk.Label(image_frame, text="")
        self.image_path_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Frame untuk edit posisi klik
        pos_frame = ttk.LabelFrame(right_frame, text="Posisi Klik", padding="10")
        pos_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(pos_frame, text="X:").grid(row=0, column=0, padx=5)
        self.x_entry = ttk.Entry(pos_frame, width=10)
        self.x_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(pos_frame, text="Y:").grid(row=0, column=2, padx=5)
        self.y_entry = ttk.Entry(pos_frame, width=10)
        self.y_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(pos_frame, text="Ambil dari Preview", command=self.get_pos_from_preview).grid(row=0, column=4, padx=5)
        
        # Frame untuk game area
        game_area_frame = ttk.LabelFrame(right_frame, text="Game Area", padding="10")
        game_area_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(game_area_frame, text="Top:").grid(row=0, column=0, padx=5)
        self.top_entry = ttk.Entry(game_area_frame, width=10)
        self.top_entry.grid(row=0, column=1, padx=5)
        self.top_entry.insert(0, str(self.config['game_area']['top']))
        
        ttk.Label(game_area_frame, text="Left:").grid(row=0, column=2, padx=5)
        self.left_entry = ttk.Entry(game_area_frame, width=10)
        self.left_entry.grid(row=0, column=3, padx=5)
        self.left_entry.insert(0, str(self.config['game_area']['left']))
        
        ttk.Label(game_area_frame, text="Width:").grid(row=1, column=0, padx=5)
        self.width_entry = ttk.Entry(game_area_frame, width=10)
        self.width_entry.grid(row=1, column=1, padx=5)
        self.width_entry.insert(0, str(self.config['game_area']['width']))
        
        ttk.Label(game_area_frame, text="Height:").grid(row=1, column=2, padx=5)
        self.height_entry = ttk.Entry(game_area_frame, width=10)
        self.height_entry.grid(row=1, column=3, padx=5)
        self.height_entry.insert(0, str(self.config['game_area']['height']))
        
        # Frame untuk settings
        settings_frame = ttk.LabelFrame(right_frame, text="Settings", padding="10")
        settings_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(settings_frame, text="Detection Threshold:").grid(row=0, column=0, padx=5)
        self.threshold_entry = ttk.Entry(settings_frame, width=10)
        self.threshold_entry.grid(row=0, column=1, padx=5)
        self.threshold_entry.insert(0, str(self.config['settings']['detection_threshold']))
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Simpan Konfigurasi", command=self.save_config).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Reset ke Default", command=self.reset_config).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Test Preview", command=self.test_preview).grid(row=0, column=2, padx=5)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
    
    def load_config(self):
        """Load konfigurasi dari JSON"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Default config
            return {
                "game_area": {"top": 40, "left": 0, "width": 1024, "height": 768},
                "button_templates": {},
                "settings": {"detection_threshold": 0.8}
            }
    
    def save_config(self):
        """Simpan konfigurasi ke JSON"""
        try:
            # Update game area
            self.config['game_area'] = {
                "top": int(self.top_entry.get()),
                "left": int(self.left_entry.get()),
                "width": int(self.width_entry.get()),
                "height": int(self.height_entry.get())
            }
            
            # Update settings
            self.config['settings']['detection_threshold'] = float(self.threshold_entry.get())
            
            # Update current button if selected
            if self.current_button:
                try:
                    x = int(self.x_entry.get())
                    y = int(self.y_entry.get())
                    self.config['button_templates'][self.current_button]['click_pos'] = [x, y]
                except ValueError:
                    pass
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Sukses", "Konfigurasi berhasil disimpan!")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan konfigurasi: {str(e)}")
    
    def reset_config(self):
        """Reset konfigurasi ke default"""
        if messagebox.askyesno("Konfirmasi", "Yakin ingin reset ke default?"):
            # Load default dari bot.py structure
            default_config = {
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
            self.config = default_config
            self.save_config()
            self.refresh_button_list()
            messagebox.showinfo("Sukses", "Konfigurasi direset ke default!")
    
    def refresh_button_list(self):
        """Refresh list tombol"""
        self.button_listbox.delete(0, tk.END)
        for button_name in self.config['button_templates'].keys():
            self.button_listbox.insert(tk.END, button_name)
    
    def on_button_select(self, event):
        """Handler ketika tombol dipilih dari list"""
        selection = self.button_listbox.curselection()
        if not selection:
            return
        
        button_name = self.button_listbox.get(selection[0])
        self.current_button = button_name
        button_config = self.config['button_templates'][button_name]
        
        # Update info label
        self.info_label.config(text=f"Edit: {button_name}")
        
        # Update preview gambar
        image_path = button_config['image']
        self.image_path_label.config(text=f"File: {image_path}")
        self.load_preview_image(image_path)
        
        # Update posisi klik
        click_pos = button_config['click_pos']
        self.x_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(click_pos[0]))
        self.y_entry.delete(0, tk.END)
        self.y_entry.insert(0, str(click_pos[1]))
    
    def load_preview_image(self, image_path):
        """Load dan tampilkan preview gambar"""
        if not os.path.exists(image_path):
            self.preview_label.config(image='', text=f"File tidak ditemukan: {image_path}")
            return
        
        try:
            img = Image.open(image_path)
            # Resize untuk preview (max 300x300)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text='')
            self.preview_label.image = photo  # Keep a reference
        except Exception as e:
            self.preview_label.config(image='', text=f"Error loading image: {str(e)}")
    
    def change_image(self):
        """Ganti gambar template"""
        if not self.current_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        
        filename = filedialog.askopenfilename(
            title="Pilih Gambar Template",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        
        if filename:
            # Copy file ke direktori project dengan nama yang sesuai
            button_config = self.config['button_templates'][self.current_button]
            new_filename = button_config['image']
            
            try:
                import shutil
                shutil.copy2(filename, new_filename)
                self.image_path_label.config(text=f"File: {new_filename}")
                self.load_preview_image(new_filename)
                messagebox.showinfo("Sukses", f"Gambar berhasil diganti!")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal mengganti gambar: {str(e)}")
    
    def capture_screenshot(self):
        """Ambil screenshot dari game area"""
        if not self.current_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        
        try:
            game_area = self.config['game_area']
            monitor = {
                "top": game_area['top'],
                "left": game_area['left'],
                "width": game_area['width'],
                "height": game_area['height']
            }
            
            screenshot = np.array(self.sct.grab(monitor))
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Tampilkan preview dan biarkan user crop
            self.show_crop_dialog(screenshot)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengambil screenshot: {str(e)}")
    
    def show_crop_dialog(self, screenshot):
        """Tampilkan dialog untuk crop screenshot"""
        crop_window = tk.Toplevel(self.root)
        crop_window.title("Crop Screenshot")
        crop_window.geometry("800x600")
        
        # Convert untuk display
        display_img = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        display_img = Image.fromarray(display_img)
        display_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(display_img)
        
        label = ttk.Label(crop_window, image=photo)
        label.pack(padx=10, pady=10)
        label.image = photo
        
        def save_cropped():
            # Untuk simplicity, simpan full screenshot
            # User bisa edit manual dengan tool lain
            button_config = self.config['button_templates'][self.current_button]
            filename = button_config['image']
            cv2.imwrite(filename, screenshot)
            self.load_preview_image(filename)
            messagebox.showinfo("Sukses", "Screenshot disimpan sebagai template!")
            crop_window.destroy()
        
        ttk.Button(crop_window, text="Simpan sebagai Template", command=save_cropped).pack(pady=10)
        ttk.Button(crop_window, text="Batal", command=crop_window.destroy).pack()
    
    def get_pos_from_preview(self):
        """Ambil posisi dari preview (akan dibuka di window terpisah)"""
        if not self.current_button:
            messagebox.showwarning("Peringatan", "Pilih tombol terlebih dahulu!")
            return
        
        # Buka preview dengan OpenCV untuk klik
        game_area = self.config['game_area']
        monitor = {
            "top": game_area['top'],
            "left": game_area['left'],
            "width": game_area['width'],
            "height": game_area['height']
        }
        
        screenshot = np.array(self.sct.grab(monitor))
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        clicked_pos = [None]
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                clicked_pos[0] = (x, y)
                print(f"Klik di: ({x}, {y})")
        
        cv2.namedWindow('Klik untuk pilih posisi (Tekan Q untuk tutup)', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Klik untuk pilih posisi (Tekan Q untuk tutup)', mouse_callback)
        
        while True:
            cv2.imshow('Klik untuk pilih posisi (Tekan Q untuk tutup)', screenshot)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or clicked_pos[0]:
                break
        
        cv2.destroyAllWindows()
        
        if clicked_pos[0]:
            x, y = clicked_pos[0]
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(y))
            messagebox.showinfo("Sukses", f"Posisi diset ke: ({x}, {y})")
    
    def test_preview(self):
        """Test preview dengan bot detector"""
        messagebox.showinfo("Info", "Fitur ini akan membuka preview bot dengan konfigurasi saat ini.\nJalankan bot dengan mode preview untuk test.")


def main():
    root = tk.Tk()
    app = ButtonEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

