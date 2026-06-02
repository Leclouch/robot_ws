#!/usr/bin/env python3
"""Test spearhead vision alignment with optional left/right robot correction.

This script only corrects strafe left/right. It never moves forward, turns,
or actuates arm/gripper.

Keyboard:
  q      quit
  space  toggle auto correction
  m      run one correction step
  e      send emergency stop
"""

import argparse
import os
import sys
import time


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import VisionConfig
from hardware.serial_interface import RobotController
from vision.visual_servoing import SpearheadVisualServo


def wait_connection(robot, timeout_s):
    print(f"[TEST] Waiting for Teensy connection for up to {timeout_s:.1f}s...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if robot.is_connected:
            print("[TEST] Teensy connected.")
            return True
        time.sleep(0.2)
    print("[TEST] Teensy not connected.")
    return False


def compute_left_command(best_track, err_x_px, args):
    err_norm, _ = best_track.get_smoothed_coords()
    move_dist = abs(err_norm) * args.scale
    move_dist = max(args.min_step, move_dist)
    move_dist = min(args.max_step, move_dist)

    # err_x > 0: object appears right of target line, so shift robot right.
    left_cmd = -move_dist if err_x_px > 0 else move_dist
    return left_cmd * args.sign


def run_correction(robot, best_track, err_x_px, args):
    if best_track is None:
        print("[VISION] No target; correction skipped.")
        return False

    if abs(err_x_px) <= args.pixel_tolerance:
        print(f"[VISION] Locked: horizontal error {err_x_px:.1f}px.")
        return True

    left_cmd = compute_left_command(best_track, err_x_px, args)
    print(f"[VISION] Move correction: left={left_cmd:.3f}m err_x={err_x_px:.1f}px")
    robot.move_relative(left=-left_cmd)
    return robot.wait_until_idle(timeout=args.motion_timeout)


def draw_status(cv2, frame, best_track, err_x_px, auto_enabled, move_enabled):
    if best_track is None:
        status = "NO TARGET"
        color = (0, 0, 255)
    else:
        status = f"err_x={err_x_px:.1f}px"
        color = (0, 255, 255)

    mode = f"move={'ON' if move_enabled else 'OFF'} auto={'ON' if auto_enabled else 'OFF'}"
    cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, mode, (20, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(
        frame,
        "space auto  m step  e estop  q quit",
        (20, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )


def main():
    parser = argparse.ArgumentParser(description="Spearhead vision left/right alignment test.")
    parser.add_argument("--move", action="store_true", help="Allow sending left/right movement to Teensy.")
    parser.add_argument("--auto", action="store_true", help="Start with automatic correction enabled.")
    parser.add_argument("--no-gui", action="store_true", help="Disable OpenCV window for faster/headless testing.")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--imgsz", type=int, default=None)
    parser.add_argument("--flush", type=int, default=None)
    parser.add_argument("--connect-timeout", type=float, default=15.0)
    parser.add_argument("--motion-timeout", type=float, default=5.0)
    parser.add_argument("--pixel-tolerance", type=float, default=VisionConfig.PIXEL_TOLERANCE_X)
    parser.add_argument("--scale", type=float, default=VisionConfig.SPEARHEAD_STRAFE_M_PER_NORM_ERROR)
    parser.add_argument("--min-step", type=float, default=VisionConfig.SPEARHEAD_MIN_STRAFE_M)
    parser.add_argument("--max-step", type=float, default=0.05, help="Max correction step in meters.")
    parser.add_argument("--delay", type=float, default=VisionConfig.SPEARHEAD_ACTION_DELAY_SEC)
    parser.add_argument("--sign", type=float, default=VisionConfig.SPEARHEAD_STRAFE_SIGN)
    args = parser.parse_args()

    if args.no_gui:
        VisionConfig.SHOW_DEBUG_WINDOW = False
    if args.width is not None:
        VisionConfig.FRAME_WIDTH = args.width
    if args.height is not None:
        VisionConfig.FRAME_HEIGHT = args.height
    if args.imgsz is not None:
        VisionConfig.SPEARHEAD_IMGSZ = args.imgsz
    if args.flush is not None:
        VisionConfig.FRAME_FLUSH_COUNT = args.flush

    cv2 = __import__("cv2")
    vision = SpearheadVisualServo()
    robot = None
    auto_enabled = bool(args.auto)
    last_cmd_time = 0.0

    if args.move:
        robot = RobotController()
        if not wait_connection(robot, args.connect_timeout):
            robot.close()
            return 1
        print("[TEST] Robot movement is ENABLED. Only left/right strafe corrections will be sent.")
    else:
        print("[TEST] Visual-only mode. Pass --move to allow left/right robot correction.")

    vision._open_camera()
    print("[TEST] Spearhead vision alignment test started.")

    try:
        while True:
            ret, frame = vision.read_latest_frame()
            if not ret:
                print("[VISION] Failed to capture frame.")
                time.sleep(0.05)
                continue

            processed, best_track, err_x_px, _ = vision.process_frame(frame)
            draw_status(cv2, processed, best_track, err_x_px, auto_enabled, args.move)

            key = 255
            if not args.no_gui:
                cv2.imshow("Spearhead Alignment Test", processed)
                key = cv2.waitKey(1) & 0xFF
            elif best_track is not None:
                print(f"[VISION] err_x={err_x_px:.1f}px auto={auto_enabled}")

            if key == ord("q"):
                break
            if key == ord(" "):
                auto_enabled = not auto_enabled
                print(f"[TEST] Auto correction {'enabled' if auto_enabled else 'disabled'}.")
            elif key == ord("e"):
                if robot:
                    robot.e_stop()
                print("[TEST] E-Stop sent." if robot else "[TEST] E-Stop skipped; no robot connection.")
            elif key == ord("m"):
                if robot:
                    run_correction(robot, best_track, err_x_px, args)
                    last_cmd_time = time.time()
                else:
                    print("[TEST] Step skipped; run with --move to control robot.")

            if auto_enabled and robot and time.time() - last_cmd_time >= args.delay:
                run_correction(robot, best_track, err_x_px, args)
                last_cmd_time = time.time()
    finally:
        vision.close()
        if robot:
            robot.e_stop()
            robot.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
