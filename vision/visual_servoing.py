"""Spearhead visual servoing without ROS2 dependencies."""

import os
import time

from config import VisionConfig


class SpearheadTrack:
    def __init__(self, track_id, initial_x, initial_y, label, mask_pts, buffer_size=5):
        self.track_id = track_id
        self.buffer = [[initial_x, initial_y]]
        self.buffer_size = buffer_size
        self.missed_frames = 0
        self.last_x = initial_x
        self.last_y = initial_y
        self.label = label
        self.mask_pts = mask_pts

    def update(self, x, y, label, mask_pts):
        np = _lazy_numpy()
        self.buffer.append([x, y])
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)
        self.missed_frames = 0
        smoothed = np.mean(self.buffer, axis=0)
        self.last_x = float(smoothed[0])
        self.last_y = float(smoothed[1])
        self.label = label
        self.mask_pts = mask_pts

    def get_smoothed_coords(self):
        np = _lazy_numpy()
        smoothed = np.mean(self.buffer, axis=0)
        return float(smoothed[0]), float(smoothed[1])


class SpearheadVisualServo:
    """Aligns the robot horizontally to the configured spearhead class."""

    def __init__(self, config=VisionConfig):
        self.config = config
        self.cv2 = _lazy_cv2()
        self.np = _lazy_numpy()
        self.torch = _lazy_torch()
        yolo_cls = _lazy_yolo()

        self.model_path = self._resolve_model_path(config.SPEARHEAD_MODEL_PATH)
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Spearhead YOLO model not found: {self.model_path}")

        self.model = yolo_cls(self.model_path)
        self.cap = None
        self.active_tracks = []
        self.next_track_id = 0
        self.selected_track_id = None
        self.last_cmd_time = 0.0

    def _resolve_model_path(self, model_path):
        if os.path.isabs(model_path):
            return model_path
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(workspace_root, model_path)

    def _open_camera(self):
        self.cap = self.cv2.VideoCapture(self.config.CAMERA_INDEX)
        self.cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
        self.cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)
        self.cap.set(self.cv2.CAP_PROP_FPS, self.config.TARGET_FPS)
        self.cap.set(self.cv2.CAP_PROP_BUFFERSIZE, self.config.LOW_LATENCY_BUFFER_SIZE)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {self.config.CAMERA_INDEX}")

    def read_latest_frame(self):
        """Drop stale buffered frames and return the newest available frame."""
        if self.cap is None:
            self._open_camera()

        flush_count = max(0, int(self.config.FRAME_FLUSH_COUNT))
        for _ in range(flush_count):
            self.cap.grab()
        return self.cap.read()

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.config.SHOW_DEBUG_WINDOW:
            self.cv2.destroyAllWindows()

    def compute_left_command(self, best_track, err_x_px, scale, min_step, max_step, sign):
        err_norm, _ = best_track.get_smoothed_coords()
        move_dist = abs(err_norm) * scale
        move_dist = max(min_step, move_dist)
        move_dist = min(max_step, move_dist)

        # err_x > 0: object appears right of target line, so shift robot right.
        left_cmd = -move_dist if err_x_px > 0 else move_dist
        return left_cmd * sign

    def align(
        self,
        robot,
        pixel_tolerance=None,
        scale=None,
        min_step=None,
        max_step=None,
        delay=None,
        sign=None,
        motion_timeout=5.0,
        align_timeout=None,
    ):
        """
        Strafe left/right until the target class is horizontally locked.

        Returns True when the target is locked. The final forward approach and
        gripper sequence intentionally remain owned by the FSM.
        """
        if pixel_tolerance is None:
            pixel_tolerance = self.config.PIXEL_TOLERANCE_X
        if scale is None:
            scale = self.config.SPEARHEAD_STRAFE_M_PER_NORM_ERROR
        if min_step is None:
            min_step = self.config.SPEARHEAD_MIN_STRAFE_M
        if max_step is None:
            max_step = getattr(self.config, "SPEARHEAD_MAX_STRAFE_M", 0.05)
        if delay is None:
            delay = self.config.SPEARHEAD_ACTION_DELAY_SEC
        if sign is None:
            sign = self.config.SPEARHEAD_STRAFE_SIGN
        if align_timeout is None:
            align_timeout = self.config.SPEARHEAD_ALIGN_TIMEOUT_SEC

        self._open_camera()
        start_time = time.time()

        try:
            while time.time() - start_time < align_timeout:
                ret, frame = self.read_latest_frame()
                if not ret:
                    print("[VISION] Gagal membaca frame kamera.")
                    time.sleep(0.05)
                    continue

                processed, best_track, err_x_px, _ = self.process_frame(frame)
                self._show_debug(processed)

                if best_track is None:
                    time.sleep(0.03)
                    continue

                if abs(err_x_px) <= pixel_tolerance:
                    print(f"[VISION] Spearhead sejajar dengan garis target vertikal: {err_x_px:.1f}px.")
                    return True

                if time.time() - self.last_cmd_time < delay:
                    continue

                left_cmd = self.compute_left_command(
                    best_track, err_x_px, scale, min_step, max_step, sign
                )

                print(f"[VISION] Koreksi strafe: left={left_cmd:.3f}m err_x={err_x_px:.1f}px")
                robot.move_relative(left=-left_cmd)
                if not robot.wait_until_idle(timeout=motion_timeout):
                    return False
                self.last_cmd_time = time.time()

            print("[VISION] Timeout alignment spearhead.")
            return False
        finally:
            self.close()

    def detect_apriltag(self):
        """
        Detect an AprilTag marker from the configured camera.

        Returns:
            tuple(bool, int | None): (detected, tag_id)

        This uses OpenCV ArUco's AprilTag dictionary when available. If the
        installed OpenCV build has no aruco module, it safely reports no tag.
        """
        if self.cap is None:
            self._open_camera()

        ret, frame = self.read_latest_frame()
        if not ret:
            return False, None

        aruco = getattr(self.cv2, "aruco", None)
        if aruco is None:
            return False, None

        dictionary_id = getattr(aruco, "DICT_APRILTAG_36h11", None)
        if dictionary_id is None:
            return False, None

        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        dictionary = aruco.getPredefinedDictionary(dictionary_id)

        if hasattr(aruco, "ArucoDetector"):
            detector = aruco.ArucoDetector(dictionary)
            corners, ids, _ = detector.detectMarkers(gray)
        else:
            corners, ids, _ = aruco.detectMarkers(gray, dictionary)

        detected = ids is not None and len(ids) > 0
        tag_id = int(ids[0][0]) if detected else None

        if self.config.SHOW_DEBUG_WINDOW:
            if detected:
                aruco.drawDetectedMarkers(frame, corners, ids)
            self.cv2.imshow("AprilTag Detector", frame)
            self.cv2.waitKey(1)

        return detected, tag_id

    def process_frame(self, color_image):
        height, width = color_image.shape[:2]
        if height == 0 or width == 0:
            return color_image, None, 0.0, 0.0

        target_x = width * self.config.SPEARHEAD_TARGET_X_RATIO
        target_y = height * self.config.SPEARHEAD_TARGET_Y_RATIO
        device = "cuda" if self.torch.cuda.is_available() else "cpu"

        results = self.model(
            color_image,
            verbose=False,
            conf=self.config.SPEARHEAD_CONF_THRESHOLD,
            imgsz=self.config.SPEARHEAD_IMGSZ,
            device=device,
        )

        new_centroids = self._extract_centroids(results, target_x, target_y, width, height)
        self._update_tracks(new_centroids)
        best_track = self._get_preferred_track()

        err_x_px = 0.0
        err_y_px = 0.0
        if best_track:
            err_norm_x, err_norm_y = best_track.get_smoothed_coords()
            err_x_px = err_norm_x * (width / 2.0)
            err_y_px = err_norm_y * (height / 2.0)

        self._draw_debug(color_image, target_x, target_y)
        return color_image, best_track, err_x_px, err_y_px

    def _extract_centroids(self, results, target_x, target_y, width, height):
        class_filter = {name.lower() for name in self.config.SPEARHEAD_CLASS_NAMES}
        new_centroids = []

        for result in results:
            if result.masks is None:
                continue

            for i, mask in enumerate(result.masks.xy):
                if len(mask) == 0:
                    continue

                cls_id = int(result.boxes.cls[i])
                label = self.model.names[cls_id]
                if class_filter and label.lower() not in class_filter:
                    continue

                cx = int(self.np.mean(mask[:, 0]))
                cy = int(self.np.mean(mask[:, 1]))
                norm_x = float((cx - target_x) / (width / 2.0))
                norm_y = float((cy - target_y) / (height / 2.0))
                new_centroids.append((norm_x, norm_y, label, mask))

        return new_centroids

    def _update_tracks(self, new_centroids):
        if not self.active_tracks:
            for x, y, label, mask in new_centroids:
                self._spawn_track(x, y, label, mask)
            return

        dists = []
        for track in self.active_tracks:
            track_x, track_y = track.get_smoothed_coords()
            dists.append([
                self.np.hypot(x - track_x, y - track_y)
                for x, y, _, _ in new_centroids
            ])

        dists = self.np.array(dists)
        matched_tracks = set()
        matched_centroids = set()

        if dists.size > 0:
            for flat_idx in self.np.argsort(dists, axis=None):
                track_idx, cent_idx = self.np.unravel_index(flat_idx, dists.shape)
                if track_idx in matched_tracks or cent_idx in matched_centroids:
                    continue
                if dists[track_idx, cent_idx] > self.config.SPEARHEAD_GATE_THRESHOLD:
                    continue

                x, y, label, mask = new_centroids[cent_idx]
                self.active_tracks[track_idx].update(x, y, label, mask)
                matched_tracks.add(track_idx)
                matched_centroids.add(cent_idx)

        for idx, track in enumerate(self.active_tracks):
            if idx not in matched_tracks:
                track.missed_frames += 1

        for idx, (x, y, label, mask) in enumerate(new_centroids):
            if idx not in matched_centroids:
                self._spawn_track(x, y, label, mask)

        self.active_tracks = [
            track
            for track in self.active_tracks
            if track.missed_frames <= self.config.SPEARHEAD_MAX_MISSED_FRAMES
        ]

    def _spawn_track(self, x, y, label, mask_pts):
        track = SpearheadTrack(
            self.next_track_id,
            x,
            y,
            label,
            mask_pts,
            self.config.SPEARHEAD_BUFFER_SIZE,
        )
        self.active_tracks.append(track)
        self.next_track_id += 1

    def _get_preferred_track(self):
        if not self.active_tracks:
            self.selected_track_id = None
            return None

        if self.selected_track_id is not None:
            for track in self.active_tracks:
                if track.track_id == self.selected_track_id:
                    return track
            self.selected_track_id = None

        preferred_track = min(self.active_tracks, key=lambda track: track.get_smoothed_coords()[0])
        self.selected_track_id = preferred_track.track_id
        return preferred_track

    def _draw_debug(self, color_image, target_x, target_y):
        height, width = color_image.shape[:2]

        for track in self.active_tracks:
            smoothed_x, smoothed_y = track.get_smoothed_coords()
            cx_pixel = int((smoothed_x * (width / 2.0)) + target_x)
            cy_pixel = int((smoothed_y * (height / 2.0)) + target_y)

            if track.mask_pts is not None:
                pts = self.np.array(track.mask_pts, dtype=self.np.int32)
                color = (255, 255, 0) if track.track_id == self.selected_track_id else (0, 255, 0)
                self.cv2.polylines(color_image, [pts], True, color, 2)

            dot_color = (255, 255, 0) if track.track_id == self.selected_track_id else (0, 0, 255)
            self.cv2.circle(color_image, (cx_pixel, cy_pixel), 6, dot_color, -1)
            self.cv2.putText(
                color_image,
                track.label,
                (cx_pixel + 8, cy_pixel - 8),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                dot_color,
                2,
            )

        self.cv2.line(
            color_image,
            (int(target_x), 0),
            (int(target_x), height),
            (255, 0, 0),
            2,
        )

    def _show_debug(self, frame):
        if not self.config.SHOW_DEBUG_WINDOW:
            return
        self.cv2.imshow("Spearhead Vision System", frame)
        key = self.cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            raise KeyboardInterrupt


def _lazy_cv2():
    import cv2
    return cv2


def _lazy_numpy():
    import numpy as np
    return np


def _lazy_torch():
    import torch
    return torch


def _lazy_yolo():
    from ultralytics import YOLO
    return YOLO
