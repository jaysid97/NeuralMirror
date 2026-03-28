"""
NeuralMirror — Webcam Pulse Detector
Uses remote photoplethysmography (rPPG) to extract BPM from subtle
skin colour changes captured by an ordinary RGB webcam.

Algorithm:
  1. Detect face with Haar cascade.
  2. Sample the mean green channel intensity inside the forehead ROI.
  3. Buffer ~30 s of samples at camera FPS.
  4. Band-pass filter → HeartPy peak analysis → BPM + HRV.
"""

import time
import threading
import platform
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import cv2
import heartpy as hp
import numpy as np

from config import (
    CAMERA_INDEX,
    FRAME_BUFFER_SECONDS,
    TARGET_FPS,
    HP_SAMPLE_RATE,
    HP_BAND_LOW,
    HP_BAND_HIGH,
    ROI_SCALE,
)


@dataclass
class PulseReading:
    bpm: float
    sdnn: float            # HRV metric (ms) — standard deviation of NN intervals
    rmssd: float           # HRV metric (ms) — root mean square of successive differences
    confidence: float      # 0.0 – 1.0 quality score
    timestamp: float = field(default_factory=time.time)

    @property
    def stress_index(self) -> float:
        """
        Composite stress index (0 = calm, 1 = highly stressed).
        High BPM + low HRV = high stress.
        """
        bpm_norm = min(max((self.bpm - 50) / 110, 0.0), 1.0)
        hrv_norm = 1.0 - min(self.rmssd / 80.0, 1.0)  # >80 ms RMSSD is healthy
        return round((bpm_norm * 0.6 + hrv_norm * 0.4) * self.confidence, 3)


class PulseDetector:
    """Real-time rPPG pulse detector backed by a background capture thread."""

    _FACE_CASCADE = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    @staticmethod
    def _has_valid_frames(cap: cv2.VideoCapture) -> bool:
        """Check if camera backend returns non-black frames."""
        good = 0
        for _ in range(8):
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            # Some backends open but deliver all-black frames on Windows.
            if float(frame.mean()) > 3.0:
                good += 1
        return good >= 2

    def __init__(self) -> None:
        self._buffer: deque[float] = deque(
            maxlen=FRAME_BUFFER_SECONDS * TARGET_FPS
        )
        self._latest: Optional[PulseReading] = None
        self._started_at: float = 0.0
        self._face_seen_recently: bool = False
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None

    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    def _open_camera() -> Optional[cv2.VideoCapture]:
        """Open camera with index/backend fallback to avoid black or invalid feeds."""
        # Try configured index first, then a small set of common alternatives.
        candidate_indices = [CAMERA_INDEX, 0, 1, 2]
        seen: set[int] = set()

        for idx in candidate_indices:
            if idx in seen:
                continue
            seen.add(idx)

            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap and cap.isOpened() and PulseDetector._has_valid_frames(cap):
                    print(f"[PulseDetector] Using camera index {idx} (DirectShow).")
                    return cap
                if cap:
                    cap.release()

            # Fallback to default backend (often MSMF on Windows).
            cap = cv2.VideoCapture(idx)
            if cap and cap.isOpened() and PulseDetector._has_valid_frames(cap):
                print(f"[PulseDetector] Using camera index {idx} (default backend).")
                return cap
            if cap:
                cap.release()

        return None

    def start(self) -> None:
        """Start background webcam capture thread."""
        self._running = True
        self._started_at = time.time()
        self._cap = self._open_camera()
        if not self._cap:
            self._running = False
            raise RuntimeError(
                "Unable to open webcam. Close other apps using the camera and retry."
            )
        self._cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        print("[PulseDetector] Camera started.")

    def stop(self) -> None:
        """Stop the capture thread and release hardware."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        print("[PulseDetector] Camera released.")

    def get_latest(self) -> Optional[PulseReading]:
        """Return the most recent PulseReading (thread-safe)."""
        with self._lock:
            return self._latest

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Blocking read of the current annotated frame for live preview.
        Returns None if the camera isn't open.
        """
        if self._cap and self._cap.isOpened():
            ok, frame = self._cap.read()
            if ok:
                return self._annotate(frame)
        return None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        while self._running:
            if not self._cap or not self._cap.isOpened():
                time.sleep(0.05)
                continue
            ok, frame = self._cap.read()
            if not ok:
                continue

            signal = self._extract_signal(frame)
            if signal is not None:
                self._buffer.append(signal)

            # Start analysis sooner so users see BPM faster during startup.
            # Analyse after ~3 seconds of valid signal for faster initial feedback.
            min_samples = min(int(TARGET_FPS * 3), int(FRAME_BUFFER_SECONDS * TARGET_FPS))
            if len(self._buffer) >= min_samples:
                reading = self._analyse()
                if reading:
                    with self._lock:
                        self._latest = reading

    def _extract_signal(self, frame: np.ndarray) -> Optional[float]:
        """Detect face, return mean green-channel value of forehead ROI."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # More sensitive face detection (lower minNeighbors, smaller minSize)
        faces = self._FACE_CASCADE.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=4, minSize=(80, 80)
        )
        if len(faces) == 0:
            self._face_seen_recently = False
            return None
        self._face_seen_recently = True
        x, y, w, h = faces[0]
        # Forehead ROI: top 25 % of face, centred horizontally
        roi_y1 = y + int(h * 0.05)
        roi_y2 = y + int(h * 0.30)
        roi_x1 = x + int(w * 0.25)
        roi_x2 = x + int(w * 0.75)
        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        if roi.size == 0:
            return None
        return float(np.mean(roi[:, :, 1]))  # green channel

    def _analyse(self) -> Optional[PulseReading]:
        """Run HeartPy on the buffered signal and return a PulseReading."""
        signal = np.array(self._buffer, dtype=np.float64)
        try:
            filtered = hp.filter_signal(
                signal,
                cutoff=[HP_BAND_LOW, HP_BAND_HIGH],
                sample_rate=HP_SAMPLE_RATE,
                filtertype="bandpass",
                order=3,
            )
            _, measures = hp.process(filtered, sample_rate=HP_SAMPLE_RATE)
            bpm = float(measures["bpm"])
            sdnn = float(measures.get("sdnn", 0.0) or 0.0)
            rmssd = float(measures.get("rmssd", 0.0) or 0.0)

            # HeartPy can occasionally emit NaN/inf during unstable calibration windows.
            # Ignore those frames and keep the UI in "calibrating" state.
            if not (np.isfinite(bpm) and np.isfinite(sdnn) and np.isfinite(rmssd)):
                return None

            # Clamp occasional negative HRV artifacts to zero.
            sdnn = max(sdnn, 0.0)
            rmssd = max(rmssd, 0.0)

            # Confidence: penalise if BPM outside physiological range
            confidence = 1.0 if 40 <= bpm <= 200 else 0.4
            return PulseReading(bpm=bpm, sdnn=sdnn, rmssd=rmssd, confidence=confidence)
        except Exception:
            return None

    def _annotate(self, frame: np.ndarray) -> np.ndarray:
        """Draw BPM overlay on the live frame."""
        reading = self.get_latest()
        if reading and np.isfinite(reading.bpm) and np.isfinite(reading.stress_index):
            label = f"BPM: {reading.bpm:.0f}  Stress: {reading.stress_index:.2f}"
            cv2.putText(
                frame, label, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 128), 2, cv2.LINE_AA,
            )
        else:
            elapsed = int(max(time.time() - self._started_at, 0))
            if self._face_seen_recently:
                label = f"Calibrating... hold still ({elapsed}s)"
            else:
                label = "No face detected - center your face in good light"
            cv2.putText(
                frame,
                label,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 220, 255),
                2,
                cv2.LINE_AA,
            )
        return frame
