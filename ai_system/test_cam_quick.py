import cv2
import sys

print("Testing camera access...")
print(f"OpenCV version: {cv2.__version__}")

# Try camera index 0
for idx in [0, 1]:
    print(f"\n--- Testing camera index {idx} ---")
    cap = cv2.VideoCapture(idx)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"  [OK] Camera {idx} works! Frame size: {frame.shape}")
        else:
            print(f"  [X] Camera {idx} opened but cannot read frame")
        cap.release()
    else:
        print(f"  [X] Camera {idx} cannot be opened")

# Try with DirectShow backend (Windows)
print("\n--- Testing camera 0 with DirectShow backend ---")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"  [OK] Camera 0 (DirectShow) works! Frame size: {frame.shape}")
    else:
        print(f"  [X] Camera 0 (DirectShow) opened but cannot read frame")
    cap.release()
else:
    print(f"  [X] Camera 0 (DirectShow) cannot be opened")

print("\nDone.")
