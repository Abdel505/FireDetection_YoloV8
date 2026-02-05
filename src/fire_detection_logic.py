
import cv2
import numpy as np
from ultralytics import YOLO

class FireVideoProcessor:
    """
    Handles video processing and fire detection logic using YOLOv8.
    Separated from the GUI for better testability and modularity.
    """
    def __init__(self, model_path="models/fire_8n.pt"):
        self.model = YOLO(model_path)
        self.cap = None
        self.fps = 30
        self.last_boxes = []
        self.frame_count = 0
        self.names = self.model.names

    def load_video(self, video_path):
        """
        Loads a video file.
        Returns:
            bool: True if video loaded successfully, False otherwise.
        """
        self.cap = cv2.VideoCapture(video_path)
        if self.cap.isOpened():
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            # Handle invalid FPS values
            if not self.fps or self.fps <= 0:
                self.fps = 30
            self.frame_count = 0
            self.last_boxes = []
            return True
        return False

    def release_video(self):
        """Releases the video capture resource."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_first_frame(self):
        """
        Gets the first frame for preview purposes without advancing substantially.
        Returns:
            tuple: (frame_rgb, success)
        """
        if not self.cap or not self.cap.isOpened():
            return None, False

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if ret:
            # Convert to RGB for GUI display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Reset pointer so playing starts from beginning
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return frame_rgb, True
        return None, False

    def process_next_frame(self, conf_thresh=0.5, process_interval=3):
        """
        Reads and processes the next frame from the video.
        
        Args:
            conf_thresh (float): Confidence threshold for detection.
            process_interval (int): Run detection every N frames.
            
        Returns:
            tuple: (frame_rgb, fire_detected, status)
                frame_rgb: The processed frame in RGB (or None if finished/error)
                fire_detected: Boolean indicating if fire was detected
                status: String status ("ok", "finished", "error")
        """
        if not self.cap or not self.cap.isOpened():
            return None, False, "error"
            
        ret, frame = self.cap.read()
        if not ret:
            return None, False, "finished"
            
        # Run detection logic periodically
        if self.frame_count % process_interval == 0:
            self.last_boxes = []
            results = self.model(frame, conf=conf_thresh, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    if float(box.conf[0]) >= conf_thresh:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = f"{self.names[int(box.cls[0])]}: {box.conf[0]:.2f}"
                        self.last_boxes.append((x1, y1, x2, y2, label))
        
        # Draw cached boxes on every frame
        fire_detected = False
        for (x1, y1, x2, y2, label) in self.last_boxes:
            fire_detected = True
            # Color: (238, 187, 195) is #eebbc3 in BGR (approx)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (195, 187, 238), 3)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (195, 187, 238), 2)
            
        self.frame_count += 1
        
        # Convert to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return frame_rgb, fire_detected, "ok"
