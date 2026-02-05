import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
import cv2
import os
import numpy as np
import sys

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
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_name = "fire_8l.pt"
        model_path = os.path.join(base_dir, "models", model_name)

        # Check if model exists in src/models, if not check root/models
        if not os.path.exists(model_path):
            possible_path = os.path.join(base_dir, "..", "models", model_name)
            if os.path.exists(possible_path):
                model_path = possible_path

        self.model = YOLO(model_path)
        self.image_path = None

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
        self.load_btn = tk.Button(btn_frame, text="Load Image", command=self.load_image, width=15, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.load_btn.grid(row=0, column=0, padx=10)
        self.predict_btn = tk.Button(btn_frame, text="Predict", command=self.predict, width=15, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.predict_btn.grid(row=0, column=1, padx=10)
        self.reset_btn = tk.Button(btn_frame, text="Reset", command=self.reset, width=15, font=BTN_FONT, bg=BTN_COLOR, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=BTN_TEXT, bd=0, relief="ridge", highlightthickness=2, highlightbackground=FG_COLOR)
        self.reset_btn.grid(row=0, column=2, padx=10)

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

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")])
        if file_path:
            self.image_path = file_path
            img = Image.open(file_path)
            img_fixed = self.resize_to_fixed_size(img)
            self.tk_img = ImageTk.PhotoImage(img_fixed)
            self.img_label.config(image=self.tk_img)
            self.result_label.config(text="")

    def predict(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        try:
            conf_thresh = self.confidence_var.get()
            results = self.model(self.image_path, conf=conf_thresh)
            # Use imdecode to handle paths with special characters (e.g., "Università")
            img = cv2.imdecode(np.fromfile(self.image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            fire_detected = False
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if float(box.conf[0]) >= conf_thresh:
                        fire_detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(img, (x1, y1), (x2, y2), (238, 187, 195), 3)
                        label = f"{self.model.names[int(box.cls[0])]}: {box.conf[0]:.2f}"
                        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (238, 187, 195), 2)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_fixed = self.resize_to_fixed_size(img_pil)
            self.tk_img = ImageTk.PhotoImage(img_fixed)
            self.img_label.config(image=self.tk_img)
            if fire_detected:
                self.result_label.config(text="🔥 FIRE DETECTED! 🔥", fg="#ff5959")
            else:
                self.result_label.config(text="No fire detected.", fg="#6fff57")
        except Exception as e:
            messagebox.showerror("Prediction Error", str(e))

    def reset(self):
        self.image_path = None
        self.tk_img = ImageTk.PhotoImage(self.placeholder_img)
        self.img_label.config(image=self.tk_img)
        self.result_label.config(text="")


def main():
    root = tk.Tk()
    app = FireDetectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
