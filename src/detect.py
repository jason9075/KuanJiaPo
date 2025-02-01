import time
import uuid
import cv2
import os
from deepface import DeepFace
import numpy as np
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

VIDEO_SOURCE = os.getenv("VIDEO_SOURCE")
SAVE_API_URL = os.getenv("SAVE_API_URL")
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


def save_event(frame, bbox):
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
        },
    )


def detect_faces():
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    person_dict = {}
    last_frame_time = 0

    while cap.isOpened():
        if time.time() - last_frame_time < INTERVAL_SEC:
            cap.grab()
            continue

        ret, frame = cap.read()
        if not ret:
            break

        last_frame_time = time.time()

        try:
            detections = DeepFace.represent(
                frame.copy(),
                model_name="ArcFace",
                enforce_detection=False,
                detector_backend="mediapipe",
            )
        except Exception as e:
            print(f"Detection error: {e}")
            continue

        if isinstance(detections, dict):
            detections = [detections]

        for detection in detections:
            confidence = detection["face_confidence"]
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
                        save_event(frame, face_area)
                        print(f"Person {person.uuid} updated.")
                    break
            else:
                new_person = Person(face_vector)
                person_dict[new_person.uuid] = new_person
                save_event(frame, face_area)
                print(f"New person detected: {new_person.uuid}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_faces()
