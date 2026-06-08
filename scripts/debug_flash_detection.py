#!/usr/bin/env python3
"""
debug_flash_detection.py
========================
Live camera channel monitor to calibrate the green flash detection threshold.

Usage:
    source .venv/bin/activate
    python scripts/debug_flash_detection.py

How to use:
    1. Run this script and point the camera at the area where the green light will appear.
    2. Wait a few seconds for the baseline to stabilize (shown in the printout).
    3. Flash your green light and watch the Green value spike.
    4. Note the peak Green value, the baseline, and compare vs Blue and Red.
    5. Use those numbers to set the thresholds in arena_1.py and teleop_wasd.py.

Press Ctrl+C or 'q' in the OpenCV window to exit.
"""

import os
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import cv2
from config import VisionConfig


def main():
    cap = cv2.VideoCapture(VisionConfig.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, VisionConfig.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VisionConfig.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, VisionConfig.TARGET_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {VisionConfig.CAMERA_INDEX}")
        return

    print("=" * 55)
    print("  🔦 GREEN FLASH DETECTION CALIBRATION TOOL")
    print("=" * 55)
    print("  Warming up camera (15 frames)...")

    # Warm-up: discard early frames so auto-exposure settles
    for _ in range(15):
        cap.grab()

    baseline_green = None

    print("  Camera ready. Watch the live values below.")
    print("  Flash your green light to see the spike.")
    print("  Press [q] in the OpenCV window or Ctrl+C to exit.")
    print("-" * 55)
    print(f"  {'Blue':>8}  {'Green':>8}  {'Red':>8}  {'G-Baseline':>12}  {'G>B+R?':>7}")
    print("-" * 55)

    try:
        while True:
            # Flush stale frames
            cap.grab()
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            blue  = float(frame[:, :, 0].mean())
            green = float(frame[:, :, 1].mean())
            red   = float(frame[:, :, 2].mean())

            # Initialize baseline on first valid frame
            if baseline_green is None:
                baseline_green = green

            delta = green - baseline_green
            green_dominant = green > max(blue, red) + 8.0
            trigger = delta > 15.0 and green_dominant

            status = "🟢 DETECTED" if trigger else "         "

            print(
                f"  {blue:8.2f}  {green:8.2f}  {red:8.2f}  "
                f"{delta:+12.2f}  {'YES' if green_dominant else 'NO':>7}  {status}",
                flush=True
            )

            # Slowly update baseline (adapts to room lighting drift)
            if not trigger:
                baseline_green = 0.99 * baseline_green + 0.01 * green

            # Show live video
            cv2.putText(
                frame,
                f"G:{green:.1f}  B:{blue:.1f}  R:{red:.1f}  delta:{delta:+.1f}",
                (5, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )
            if trigger:
                cv2.putText(frame, "GREEN FLASH DETECTED!", (5, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Flash Calibration", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n[DONE] Exited calibration tool.")
        if baseline_green is not None:
            print(f"  Final baseline green value: {baseline_green:.2f}")
        print("  Use the delta & dominance values above to tune the thresholds.")


if __name__ == "__main__":
    main()
