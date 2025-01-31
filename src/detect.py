import cv2
import requests
import time

STREAM_URL = "rtmp://localhost:1935/live/camera"
SAVE_API_URL = "http://localhost:8000/api/save"


def detect_faces():
    cap = cv2.VideoCapture(STREAM_URL)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for x, y, w, h in faces:
            # Draw rectangle around the face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Save face event via API
            image_path = f"./screenshot/{int(time.time())}.jpg"
            cv2.imwrite(image_path, frame)

            requests.post(
                SAVE_API_URL,
                json={"image_path": image_path, "bbox": f"{x},{y},{w},{h}"},
            )

        cv2.imshow("Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_faces()
