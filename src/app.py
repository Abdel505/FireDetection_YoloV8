import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading
import importlib

# Modern color scheme (matching existing files)
BG_COLOR = "#232946"
FG_COLOR = "#eebbc3"
BTN_COLOR = "#393e46"
BTN_ACTIVE = "#eebbc3"
BTN_TEXT = "#232946"
TITLE_FONT = ("Segoe UI", 18, "bold")
BTN_FONT = ("Segoe UI", 12, "bold")

# Global placeholders for imported modules
Fire_interface_v = None
RealTimeFire = None

def preload_modules():
    """Background thread to import heavy modules."""
    global Fire_interface_v, RealTimeFire
    try:
        if Fire_interface_v is None:
            # This triggers imports of ultralytics, torch, cv2, etc.
            Fire_interface_v = importlib.import_module("Fire_interface_v")
            print("Preloaded Fire_interface_v")
            
        if RealTimeFire is None:
            RealTimeFire = importlib.import_module("RealTimeFire")
            print("Preloaded RealTimeFire")
    except Exception as e:
        print(f"Error preloading modules: {e}")

class MainLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fire Detection Launcher")
        self.root.geometry("450x300")
        self.root.configure(bg=BG_COLOR)
        
        # Center the window
        self.center_window(450, 300)

        # Title
        title_label = tk.Label(self.root, text="Fire Detection System", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR)
        title_label.pack(pady=(40, 30))

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        # Button 1: Video File Detection
        self.btn_video = tk.Button(btn_frame, text="📁 Video File Detection", command=self.launch_video_interface, 
                                   width=25, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, 
                                   activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, 
                                   bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.btn_video.pack(pady=10)

        # Button 2: Real-Time Camera
        self.btn_camera = tk.Button(btn_frame, text="📷 Real-Time Camera", command=self.launch_camera_interface, 
                                    width=25, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, 
                                    activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, 
                                    bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.btn_camera.pack(pady=10)

        # Status Label (hidden mostly)
        self.status_label = tk.Label(self.root, text="", font=("Segoe UI", 9), bg=BG_COLOR, fg=FG_COLOR)
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        # Start preloading
        threading.Thread(target=preload_modules, daemon=True).start()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def launch_video_interface(self):
        global Fire_interface_v
        if Fire_interface_v is None:
            self.status_label.config(text="Loading detection modules...")
            self.root.update()
            try:
                Fire_interface_v = importlib.import_module("Fire_interface_v")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load module: {e}")
                self.status_label.config(text="")
                return
        
        self.status_label.config(text="")
        
        
        # Hide main window
        self.root.withdraw()
        
        # Create Toplevel window
        window = tk.Toplevel(self.root)
        
        def on_back():
            self.root.deiconify()
            
        app = Fire_interface_v.FireDetectionApp(window, on_back=on_back)

    def launch_camera_interface(self):
        global RealTimeFire
        if RealTimeFire is None:
            self.status_label.config(text="Loading detection modules...")
            self.root.update()
            try:
                RealTimeFire = importlib.import_module("RealTimeFire")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load module: {e}")
                self.status_label.config(text="")
                return

        self.status_label.config(text="")
        
        # Hide main window
        self.root.withdraw()

        # Create Toplevel window
        window = tk.Toplevel(self.root)
        
        def on_back():
            self.root.deiconify()

        app = RealTimeFire.RealTimeFireApp(window, on_back=on_back)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainLauncherApp(root)
    root.mainloop()
