
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import cv2
from fire_detection_logic import FireVideoProcessor

class TestFireVideoProcessor(unittest.TestCase):
    def setUp(self):
        # Mock YOLO to avoid loading actual model
        with patch('fire_detection_logic.YOLO') as MockYOLO:
            self.processor = FireVideoProcessor("dummy_path")
            self.processor.model = MagicMock()
            self.processor.names = {0: "fire"}

    @patch('cv2.VideoCapture')
    def test_load_video_success(self, MockCapture):
        # Setup mock capture
        cap = MockCapture.return_value
        cap.isOpened.return_value = True
        cap.get.return_value = 30.0  # FPS
        
        result = self.processor.load_video("test.mp4")
        
        self.assertTrue(result)
        self.assertEqual(self.processor.fps, 30.0)
        cap.get.assert_called()

    @patch('cv2.VideoCapture')
    def test_process_next_frame_with_fire(self, MockCapture):
        # Setup processor with a mocked capture
        cap = MockCapture.return_value
        cap.isOpened.return_value = True
        cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
        self.processor.cap = cap
        
        # Mock detection result
        mock_result = MagicMock()
        mock_box = MagicMock()
        mock_box.conf = [0.9]
        mock_box.cls = [0]
        mock_box.xyxy = [np.array([10, 10, 50, 50])]
        mock_result.boxes = [mock_box]
        self.processor.model.return_value = [mock_result]
        
        # Run process
        frame, fire_detected, status = self.processor.process_next_frame(conf_thresh=0.5)
        
        self.assertEqual(status, "ok")
        self.assertTrue(fire_detected)
        self.assertIsNotNone(frame)
        self.processor.model.assert_called()

    def test_process_next_frame_no_video(self):
        self.processor.cap = None
        frame, fire_detected, status = self.processor.process_next_frame()
        self.assertEqual(status, "error")

if __name__ == '__main__':
    unittest.main()
