import threading
import time
import uuid
import cv2
import os
from deepface import DeepFace
import numpy as np
from prometheus_client import Counter, start_http_server
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

# Prometheus counters
NEW_PERSON_COUNTER = Counter("new_person_total", "Number of new persons detected")
DETECTION_ERROR_COUNTER = Counter(
    "detection_errors_total", "Number of detection errors"
)
FRAMES_PROCESSED = Counter("frames_processed_total", "Frames processed")

FRAME_PATH = "./static/screenshot/frame.jpg"
SAVE_API_URL = os.getenv("SAVE_API_URL", "")
INTERVAL_SEC = int(os.getenv("INTERVAL_SEC"))
PERSON_INTERVAL_MIN = int(os.getenv("PERSON_INTERVAL_MIN"))
FACE_CONF_THR = float(os.getenv("FACE_CONF_THR"))


class Person:
    def __init__(self, face_vector):
        self.uuid = str(uuid.uuid4())
        self.face_vector = face_vector
        self.timestamp = datetime.now()


def is_similar(vector1, vector2, threshold=0.6):
    cos_sim = np.dot(vector1, vector2) / (
        np.linalg.norm(vector1) * np.linalg.norm(vector2)
    )
    return ((cos_sim + 1) / 2) > threshold


def save_event(frame, bbox, confidence):
    # GMT +8
    date_str = (datetime.now() + timedelta(hours=8)).strftime("%Y%m%d")
    time_str = (datetime.now() + timedelta(hours=8)).strftime("%H%M%S")
    os.makedirs(f"./static/screenshot/{date_str}", exist_ok=True)
    image_path = f"./static/screenshot/{date_str}/{time_str}.jpg"
    cv2.imwrite(image_path, frame)
    requests.post(
        SAVE_API_URL,
        json={
            "image_path": image_path,
            "bbox_x": bbox["x"],
            "bbox_y": bbox["y"],
            "bbox_w": bbox["w"],
            "bbox_h": bbox["h"],
            "confidence": confidence,
        },
    )


def detect_faces():
    start_http_server(8001)
    video_sources = [0, 1, 2, 3]
    cap = None

    for source in video_sources:
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            print(f"Using video source {source}")
            break
        cap.release()
        cap = None

    if cap is None or not cap.isOpened():
        print("No available video source found.")
        DETECTION_ERROR_COUNTER.inc()
        return

    person_dict = {}
    last_frame_time = 0

    while True:
        ret, frame = cap.read()
        if ret:
            FRAMES_PROCESSED.inc()
        if not ret:
            print("Failed to read from video source.")
            DETECTION_ERROR_COUNTER.inc()
            cap.release()
            time.sleep(0.1)

            for source in video_sources:
                cap = cv2.VideoCapture(source)
                if cap.isOpened():
                    print(f"Using video source {source}")
                    break
                cap.release()
                cap = None

            if cap is None or not cap.isOpened():
                print("No available video source found.")
                DETECTION_ERROR_COUNTER.inc()
                time.sleep(5)
                continue

            time.sleep(0.1)
            continue

        # Save the frame to avoid partial write issues
        temp_frame_path = FRAME_PATH.split(".jpg")[0] + ".tmp.jpg"
        cv2.imwrite(temp_frame_path, frame)
        os.replace(temp_frame_path, FRAME_PATH)

        if time.time() - last_frame_time < INTERVAL_SEC:
            time.sleep(0.1)  # Avoid busy waiting
            continue

        print(f"Number of people: {len(person_dict)}")
        last_frame_time = time.time()

        frame_copy = frame.copy()
        try:
            detections = DeepFace.represent(
                frame_copy,
                model_name="ArcFace",
                enforce_detection=False,
                detector_backend="mtcnn",
            )
        except Exception as e:
            print(f"Detection error: {e}")
            DETECTION_ERROR_COUNTER.inc()
            continue

        if isinstance(detections, dict):
            detections = [detections]

        for detection in detections:
            confidence = detection.get("face_confidence", 0.0)
            if confidence < FACE_CONF_THR:
                continue
            face_vector = detection["embedding"]
            face_area = detection["facial_area"]

            for person in person_dict.values():
                if is_similar(face_vector, person.face_vector):
                    if datetime.now() - person.timestamp > timedelta(
                        minutes=PERSON_INTERVAL_MIN
                    ):
                        person.timestamp = datetime.now()
                        person.face_vector = face_vector
                        save_event(frame, face_area, confidence)
                        print(f"Person {person.uuid} updated.")
                    break
            else:
                new_person = Person(face_vector)
                person_dict[new_person.uuid] = new_person
                save_event(frame, face_area, confidence)
                NEW_PERSON_COUNTER.inc()
                print(f"New person detected: {new_person.uuid}")

        time.sleep(0.1)  # Avoid busy waiting

    cap.release()


if __name__ == "__main__":
    detect_faces()
