import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
import cv2
import os

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
        self.root.geometry("850x650")
        self.root.configure(bg=BG_COLOR)
        self.model = YOLO("fire_8n30.pt")
        self.image_path = None

        # Title label
        title = tk.Label(self.root, text="🔥 Fire Detection with YOLOv8 🔥", font=("Segoe UI", 22, "bold"), bg=BG_COLOR, fg=FG_COLOR)
        title.pack(pady=(20, 10))

        # Image display frame
        img_frame = tk.Frame(self.root, bg=BG_COLOR, highlightbackground=FG_COLOR, highlightthickness=2, bd=0)
        img_frame.pack(pady=10)
        self.img_label = tk.Label(img_frame, bg=BG_COLOR)
        self.img_label.pack(padx=10, pady=10)
        self.display_size = (700, 500)

        # Result label
        self.result_label = tk.Label(self.root, text="", font=LABEL_FONT, bg=BG_COLOR, fg=FG_COLOR)
        self.result_label.pack(pady=10)

        # Button frame
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=10)
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

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")])
        if file_path:
            self.image_path = file_path
            img = Image.open(file_path)
            img.thumbnail(self.display_size)
            self.tk_img = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.tk_img)
            self.result_label.config(text="")

    def predict(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        try:
            conf_thresh = self.confidence_var.get()
            results = self.model(self.image_path, conf=conf_thresh)
            img = cv2.imread(self.image_path)
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
            img_pil.thumbnail(self.display_size)
            self.tk_img = ImageTk.PhotoImage(img_pil)
            self.img_label.config(image=self.tk_img)
            if fire_detected:
                self.result_label.config(text="🔥 FIRE DETECTED! 🔥", fg="#ff5959")
            else:
                self.result_label.config(text="No fire detected.", fg="#6fff57")
        except Exception as e:
            messagebox.showerror("Prediction Error", str(e))

    def reset(self):
        self.image_path = None
        self.img_label.config(image="")
        self.result_label.config(text="")


def main():
    root = tk.Tk()
    app = FireDetectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
