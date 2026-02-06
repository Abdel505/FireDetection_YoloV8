import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import time
from fire_detection_logic import FireVideoProcessor
import serial
import serial.tools.list_ports

# Modern color scheme
BG_COLOR = "#232946"
FG_COLOR = "#eebbc3"
BTN_COLOR = "#393e46"
BTN_ACTIVE = "#eebbc3"
BTN_TEXT = "#232946"
SLIDER_COLOR = "#b8c1ec"
LABEL_FONT = ("Segoe UI", 16, "bold")
BTN_FONT = ("Segoe UI", 12, "bold")

class FireDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fire Detection with YOLOv8")
        self.root.geometry("850x430")
        self.root.configure(bg=BG_COLOR)
        
        # Initialize the logic processor
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_name = "fire_8n.pt"
        model_path = os.path.join(base_dir, "models", model_name)

        # Check if model exists in src/models, if not check root/models
        if not os.path.exists(model_path):
            possible_path = os.path.join(base_dir, "..", "models", model_name)
            if os.path.exists(possible_path):
                model_path = possible_path

        self.processor = FireVideoProcessor(model_path)
        self.video_path = None
        self.is_running = False
        self.after_id = None
        self.last_fire_state = False

        # --- ESP32 Serial Connection ---
        self.ser = self.detect_and_connect_esp32()
        
        # Title label
        title = tk.Label(self.root, text="🔥 Fire Detection with YOLOv8 🔥", font=("Segoe UI", 22, "bold"), bg=BG_COLOR, fg=FG_COLOR)
        title.pack(pady=(20, 10))

        # Image display frame
        img_frame = tk.Frame(self.root, bg=BG_COLOR, highlightbackground=FG_COLOR, highlightthickness=2, bd=0)
        img_frame.pack(pady=3)
        self.display_size = (300, 200)
        self.placeholder_img = Image.new("RGB", self.display_size, "black")
        self.tk_img = ImageTk.PhotoImage(self.placeholder_img)
        self.img_label = tk.Label(img_frame, image=self.tk_img, bg=BG_COLOR)
        self.img_label.pack(padx=10, pady=2)

        # Result label
        self.result_label = tk.Label(self.root, text="", font=LABEL_FONT, bg=BG_COLOR, fg=FG_COLOR)
        self.result_label.pack(pady=2)

        # Button frame
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=2)
        self.load_btn = tk.Button(btn_frame, text="Load Video", command=self.load_video, width=15, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.load_btn.grid(row=0, column=0, padx=10)
        self.reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset, width=15, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.reset_btn.grid(row=0, column=1, padx=10)

        # Confidence threshold slider
        slider_frame = tk.Frame(self.root, bg=BG_COLOR)
        slider_frame.pack(pady=10)
        tk.Label(slider_frame, text="Confidence Threshold:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=(0, 10))
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.conf_slider = tk.Scale(slider_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, resolution=0.1, variable=self.confidence_var, length=300,
                                    bg=BG_COLOR, fg=FG_COLOR, troughcolor=SLIDER_COLOR, highlightbackground=FG_COLOR, font=BTN_FONT, bd=0)
        self.conf_slider.pack(side=tk.LEFT)

        # Auto-reload setup
        self.script_path = os.path.abspath(__file__)
        self.last_mtime = os.stat(self.script_path).st_mtime
        self.check_reload()

    def detect_and_connect_esp32(self):
        """Automatically detects and connects to an ESP32 device."""
        try:
            ports = serial.tools.list_ports.comports()
            # Common identifiers for ESP32 USB drivers
            target_descriptors = ["CP210", "CH340", "USB Serial", "USB-to-Serial", "USB UART"]
            for port in ports:
                if any(desc in port.description for desc in target_descriptors):
                    print(f"Connecting to ESP32 on {port.device} ({port.description})...")
                    return serial.Serial(port.device, 115200, timeout=1)
            print("Warning: No ESP32-like device found.")
            return None
        except Exception as e:
            print(f"Warning: Could not connect to ESP32. {e}")
            return None

    def check_reload(self):
        try:
            current_mtime = os.stat(self.script_path).st_mtime
            if current_mtime != self.last_mtime:
                print("Code change detected. Restarting...")
                self.root.destroy()
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"Error checking reload: {e}")
        self.root.after(1000, self.check_reload)

    def resize_to_fixed_size(self, img_pil):
        return img_pil.resize(self.display_size, Image.LANCZOS)

    def load_video(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")])
        if file_path:
            self.video_path = file_path
            if self.processor.load_video(file_path):
                # Get a preview frame
                frame_rgb, success = self.processor.get_first_frame()
                if success:
                    img_pil = Image.fromarray(frame_rgb)
                    img_fixed = self.resize_to_fixed_size(img_pil)
                    self.tk_img = ImageTk.PhotoImage(img_fixed)
                    self.img_label.config(image=self.tk_img)
                self.result_label.config(text="Video Loaded")
                
                if not self.is_running:
                    self.predict()
            else:
                messagebox.showerror("Error", "Failed to load video.")

    def predict(self):
        if not self.video_path:
            messagebox.showwarning("No Video", "Please load a video first.")
            return
        self.is_running = True
        self.process_frame()

    def process_frame(self):
        start_time = time.time()
        if not self.is_running:
            return
        
        conf_thresh = self.confidence_var.get()
        frame_rgb, fire_detected, status = self.processor.process_next_frame(conf_thresh)
        
        if status == "finished":
            self.is_running = False
            self.result_label.config(text="Video Finished")
            return
        elif status == "error":
            self.is_running = False
            return
            
        # Update Image
        if frame_rgb is not None:
            img_pil = Image.fromarray(frame_rgb)
            img_fixed = self.resize_to_fixed_size(img_pil)
            self.tk_img = ImageTk.PhotoImage(img_fixed)
            self.img_label.config(image=self.tk_img)
        
        # Update Status Label
        if fire_detected:
            # Send signal only if state changed to avoid flooding serial
            if not self.last_fire_state and self.ser:
                self.ser.write(b"FIRE\n")
            self.last_fire_state = True
            self.result_label.config(text="🔥 FIRE DETECTED! 🔥", fg="#ff5959")
        else:
            if self.last_fire_state and self.ser:
                self.ser.write(b"SAFE\n")
            self.last_fire_state = False
            self.result_label.config(text="No fire detected.", fg="#6fff57")
            
        # Schedule next frame
        processing_time = (time.time() - start_time) * 1000
        delay = int(max(1, (1000 / self.processor.fps) - processing_time))
        self.root.after(delay, self.process_frame)

    def reset(self):
        self.is_running = False
        self.processor.release_video()
        self.video_path = None
        self.tk_img = ImageTk.PhotoImage(self.placeholder_img)
        self.img_label.config(image=self.tk_img)
        self.result_label.config(text="")
        # Turn off alarm on reset
        if self.ser:
            self.ser.write(b"RESET\n")
        self.last_fire_state = False


def main():
    root = tk.Tk()
    app = FireDetectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
