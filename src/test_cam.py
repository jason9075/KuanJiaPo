"""Utility for testing camera input.

This module is intentionally simple and is not run during automated tests.
If OpenCV (``cv2``) is not available, the ``main`` function will simply exit
without raising an ImportError so that ``unittest`` discovery does not fail.
"""

try:
    import cv2
except Exception:  # pragma: no cover - handled for environments without cv2
    cv2 = None

VIDEO_SOURCE = 0


def main():
    if cv2 is None:
        print("OpenCV is not installed; skipping camera test.")
        return

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        # Display the resulting frame
        cv2.imshow("frame", frame)
        if cv2.waitKey(1) == ord("q"):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
