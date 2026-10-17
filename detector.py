import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceDetector:
    """
    Lightweight Deep Learning Face Detector powered by MediaPipe BlazeFace.
    Runs at 100+ FPS, consuming < 50MB RAM.
    """
    def __init__(self, model_path: str, min_confidence: float = 0.6):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=min_confidence
        )
        self.detector = vision.FaceDetector.create_from_options(options)

    def detect(self, bgr_frame: np.ndarray):
        """
        Detect faces in a BGR OpenCV frame.
        Returns:
            list of dicts: [
                {
                    'bbox': (x, y, w, h),
                    'confidence': float,
                    'keypoints': [(x, y), ...]
                }, ...
            ]
        """
        h, w, _ = bgr_frame.shape
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.detector.detect(mp_image)
        faces = []

        if not result or not result.detections:
            return faces

        for detection in result.detections:
            bbox = detection.bounding_box
            # Ensure coordinates stay within frame bounds
            bx = max(0, int(bbox.origin_x))
            by = max(0, int(bbox.origin_y))
            bw = min(w - bx, int(bbox.width))
            bh = min(h - by, int(bbox.height))

            score = 0.0
            if detection.categories:
                score = float(detection.categories[0].score)

            keypoints = []
            if detection.keypoints:
                for kp in detection.keypoints:
                    kx = int(kp.x * w)
                    ky = int(kp.y * h)
                    keypoints.append((kx, ky))

            faces.append({
                'bbox': (bx, by, bw, bh),
                'confidence': score,
                'keypoints': keypoints
            })

        return faces
