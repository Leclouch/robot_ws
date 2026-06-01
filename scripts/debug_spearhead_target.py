#!/usr/bin/env python3
"""Visual-only tuner for spearhead target ratios.

Keyboard:
  a/d  move target line left/right
  p    print current ratios
  q    quit
"""

import os
import sys
import argparse


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import VisionConfig
from vision.visual_servoing import SpearheadVisualServo


STEP = 0.005


def clamp_ratio(value):
    return max(0.0, min(1.0, value))


def print_ratios(target_x_ratio):
    print(
        "[TARGET] "
        f"SPEARHEAD_TARGET_X_RATIO = {target_x_ratio:.4f}"
    )


def main():
    parser = argparse.ArgumentParser(description="Visual-only spearhead target-line tuner.")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--imgsz", type=int, default=None)
    parser.add_argument("--flush", type=int, default=None)
    args = parser.parse_args()

    if args.width is not None:
        VisionConfig.FRAME_WIDTH = args.width
    if args.height is not None:
        VisionConfig.FRAME_HEIGHT = args.height
    if args.imgsz is not None:
        VisionConfig.SPEARHEAD_IMGSZ = args.imgsz
    if args.flush is not None:
        VisionConfig.FRAME_FLUSH_COUNT = args.flush

    cv2 = __import__("cv2")

    servo = SpearheadVisualServo()
    target_x_ratio = float(VisionConfig.SPEARHEAD_TARGET_X_RATIO)

    servo._open_camera()
    print("[DEBUG] Spearhead target tuner started.")
    print_ratios(target_x_ratio)

    try:
        while True:
            ret, frame = servo.read_latest_frame()
            if not ret:
                print("[DEBUG] Failed to capture frame.")
                continue

            original_x = VisionConfig.SPEARHEAD_TARGET_X_RATIO
            VisionConfig.SPEARHEAD_TARGET_X_RATIO = target_x_ratio
            try:
                processed, best_track, err_x_px, _ = servo.process_frame(frame)
            finally:
                VisionConfig.SPEARHEAD_TARGET_X_RATIO = original_x

            status = "NO TARGET"
            color = (0, 0, 255)
            if best_track is not None:
                status = f"horizontal err={err_x_px:.1f}px"
                color = (0, 255, 255)

            cv2.putText(
                processed,
                status,
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
            )
            cv2.putText(
                processed,
                f"target line x={target_x_ratio:.4f}",
                (20, 62),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                processed,
                "a/d target line  p print  q quit",
                (20, processed.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Spearhead Target Tuner", processed)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("a"):
                target_x_ratio = clamp_ratio(target_x_ratio - STEP)
            elif key == ord("d"):
                target_x_ratio = clamp_ratio(target_x_ratio + STEP)
            elif key == ord("p"):
                print_ratios(target_x_ratio)
    finally:
        print_ratios(target_x_ratio)
        servo.close()


if __name__ == "__main__":
    main()
