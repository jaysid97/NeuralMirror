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

    def __init__(self) -> None:
        self._buffer: deque[float] = deque(
            maxlen=FRAME_BUFFER_SECONDS * TARGET_FPS
        )
        self._latest: Optional[PulseReading] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start background webcam capture thread."""
        self._running = True
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
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

            if len(self._buffer) >= FRAME_BUFFER_SECONDS * TARGET_FPS * 0.5:
                reading = self._analyse()
                if reading:
                    with self._lock:
                        self._latest = reading

    def _extract_signal(self, frame: np.ndarray) -> Optional[float]:
        """Detect face, return mean green-channel value of forehead ROI."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._FACE_CASCADE.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(120, 120)
        )
        if len(faces) == 0:
            return None
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
            bpm = measures["bpm"]
            sdnn = measures.get("sdnn", 0.0)
            rmssd = measures.get("rmssd", 0.0)
            # Confidence: penalise if BPM outside physiological range
            confidence = 1.0 if 40 <= bpm <= 200 else 0.4
            return PulseReading(bpm=bpm, sdnn=sdnn, rmssd=rmssd, confidence=confidence)
        except Exception:
            return None

    def _annotate(self, frame: np.ndarray) -> np.ndarray:
        """Draw BPM overlay on the live frame."""
        reading = self.get_latest()
        if reading:
            label = f"BPM: {reading.bpm:.0f}  Stress: {reading.stress_index:.2f}"
            cv2.putText(
                frame, label, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 128), 2, cv2.LINE_AA,
            )
        return frame
