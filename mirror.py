"""
NeuralMirror — Main Entry Point
Orchestrates the pulse detector, AI brain, and voice output in a live loop.

Run:
    python mirror.py [--no-voice] [--interval 30] [--futurecast]

Controls (while the webcam window is open):
    Q         → quit
    SPACE     → trigger an immediate AI insight
    C         → open live chat prompt in terminal
    R         → reset AI conversation history
    F         → toggle FutureCast mode
    V         → cycle AI voice style (oracle/tactical/poetic)
"""

from __future__ import annotations

import argparse
import json
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import cv2

from config import STRESS_BPM_HIGH, STRESS_BPM_LOW
from pulse_detector import PulseDetector
from ai_brain import AIBrain
from voice_output import VoiceOutput


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NeuralMirror — Real-time Wellness AI")
    p.add_argument("--no-voice", action="store_true", help="Disable Murf TTS output")
    p.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between automatic AI insights (default: 30)",
    )
    p.add_argument(
        "--futurecast",
        action="store_true",
        help="Start in FutureCast mode (forward-looking trend insights)",
    )
    p.add_argument(
        "--save-report",
        type=str,
        default="",
        help="Optional path to save a JSON session report at exit",
    )
    return p.parse_args()


def _trend_label(delta: float, threshold: float) -> str:
    if delta > threshold:
        return "rising"
    if delta < -threshold:
        return "falling"
    return "steady"


def _cycle_style(current: str) -> str:
    styles = ["oracle", "tactical", "poetic"]
    try:
        idx = styles.index(current)
    except ValueError:
        return styles[0]
    return styles[(idx + 1) % len(styles)]


def _save_session_report(report_path: str, session_started: float, events: list[dict]) -> None:
    if not events:
        return

    readings = [e for e in events if e.get("type") == "insight"]
    bpms = [float(e["bpm"]) for e in readings if "bpm" in e]
    stresses = [float(e["stress_index"]) for e in readings if "stress_index" in e]

    summary = {
        "session_started_utc": datetime.fromtimestamp(session_started, tz=timezone.utc).isoformat(),
        "session_ended_utc": datetime.now(tz=timezone.utc).isoformat(),
        "total_events": len(events),
        "insight_events": len(readings),
        "chat_events": len([e for e in events if e.get("type") == "chat"]),
        "avg_bpm": round(sum(bpms) / len(bpms), 2) if bpms else None,
        "max_bpm": round(max(bpms), 2) if bpms else None,
        "avg_stress_index": round(sum(stresses) / len(stresses), 3) if stresses else None,
        "max_stress_index": round(max(stresses), 3) if stresses else None,
        "futurecast_usage_count": len([e for e in readings if e.get("mode") == "FutureCast"]),
    }

    report = {
        "project": "NeuralMirror",
        "report_version": 1,
        "summary": summary,
        "events": events,
    }

    out = Path(report_path)
    if out.parent and str(out.parent) != ".":
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[NeuralMirror] Session report saved: {out}")


def main() -> None:
    args = parse_args()

    detector = PulseDetector()
    brain = AIBrain()
    voice = None if args.no_voice else VoiceOutput()
    futurecast_enabled = args.futurecast

    detector.start()
    print(
        "\n🪞  NeuralMirror is live.\n"
        "   Press  SPACE  for an instant insight.\n"
        "   Press  C      for live chat in terminal.\n"
        "   Press  R      to reset the AI memory.\n"
        "   Press  F      to toggle FutureCast mode.\n"
        "   Press  V      to cycle AI style.\n"
        "   Press  Q      to quit.\n"
    )
    print(f"[NeuralMirror] Initial mode: {'FutureCast' if futurecast_enabled else 'Classic'}")
    print(f"[NeuralMirror] Response style: {brain.style}")

    last_auto_insight = time.time()
    recent_readings: deque = deque(maxlen=24)
    session_started = time.time()
    session_events: list[dict] = []

    try:
        while True:
            frame = detector.get_frame()
            if frame is not None:
                cv2.imshow("NeuralMirror — Live Feed", frame)

            key = cv2.waitKey(1) & 0xFF

            # ── Quit ─────────────────────────────────────────────────────────
            if key == ord("q"):
                break

            # ── Reset AI memory ───────────────────────────────────────────────
            if key == ord("r"):
                brain.reset()
                print("[NeuralMirror] Conversation history cleared.")

            # ── Toggle FutureCast mode ───────────────────────────────────────
            if key == ord("f"):
                futurecast_enabled = not futurecast_enabled
                state = "ON" if futurecast_enabled else "OFF"
                print(f"[NeuralMirror] FutureCast mode: {state}")

            # ── Cycle creative response style ────────────────────────────────
            if key == ord("v"):
                next_style = _cycle_style(brain.style)
                brain.set_style(next_style)
                print(f"[NeuralMirror] Response style: {brain.style}")

            # ── Live chat prompt ─────────────────────────────────────────────
            if key == ord("c"):
                reading = detector.get_latest()
                if reading is None:
                    print("[NeuralMirror] Live chat unavailable while calibrating.")
                    continue

                recent_readings.append(reading)
                print("\n[NeuralMirror] Live chat mode. Type your message and press Enter.")
                user_msg = input("You > ").strip()
                if not user_msg:
                    print("[NeuralMirror] Empty message, returning to monitor.")
                    continue

                reply = brain.chat(
                    user_message=user_msg,
                    reading=reading,
                    recent_readings=list(recent_readings),
                )
                print(f"\n🧠 NeuralMirror chat:\n   {reply}\n")
                session_events.append(
                    {
                        "type": "chat",
                        "timestamp": time.time(),
                        "user_message": user_msg,
                        "assistant_reply": reply,
                        "mode": "FutureCast" if futurecast_enabled else "Classic",
                        "style": brain.style,
                        "bpm": round(reading.bpm, 2),
                        "stress_index": round(reading.stress_index, 3),
                    }
                )
                if voice:
                    voice.speak(reply)

            # ── Manual or auto insight trigger ────────────────────────────────
            now = time.time()
            manual = key == ord(" ")
            auto = (now - last_auto_insight) >= args.interval

            if manual or auto:
                reading = detector.get_latest()
                if reading is None:
                    print("[NeuralMirror] Still calibrating — no reading yet.")
                    continue

                # Flag physiological outliers
                if reading.bpm > STRESS_BPM_HIGH:
                    print(f"⚠️  Elevated BPM detected: {reading.bpm:.0f}")
                elif reading.bpm < STRESS_BPM_LOW:
                    print(f"⚠️  Low BPM detected: {reading.bpm:.0f}")

                print(
                    f"\n📊 BPM={reading.bpm:.1f}  "
                    f"SDNN={reading.sdnn:.1f}ms  "
                    f"RMSSD={reading.rmssd:.1f}ms  "
                    f"Stress={reading.stress_index:.2f}"
                )

                recent_readings.append(reading)
                window = list(recent_readings)[-8:]
                if len(window) >= 2:
                    bpm_delta = window[-1].bpm - window[0].bpm
                    stress_delta = window[-1].stress_index - window[0].stress_index
                else:
                    bpm_delta = 0.0
                    stress_delta = 0.0

                print(
                    "🛰️ Trend "
                    f"BPM={_trend_label(bpm_delta, 2.5)} ({bpm_delta:+.1f})  "
                    f"Stress={_trend_label(stress_delta, 0.06)} ({stress_delta:+.2f})  "
                    f"Mode={'FutureCast' if futurecast_enabled else 'Classic'}"
                )

                if futurecast_enabled:
                    insight = brain.analyse_futurecast(reading, list(recent_readings))
                else:
                    insight = brain.analyse(reading)
                print(f"\n🧠 NeuralMirror says:\n   {insight}\n")

                session_events.append(
                    {
                        "type": "insight",
                        "timestamp": now,
                        "mode": "FutureCast" if futurecast_enabled else "Classic",
                        "style": brain.style,
                        "bpm": round(reading.bpm, 2),
                        "sdnn": round(reading.sdnn, 2),
                        "rmssd": round(reading.rmssd, 2),
                        "stress_index": round(reading.stress_index, 3),
                        "confidence": round(reading.confidence, 3),
                        "insight": insight,
                    }
                )

                if voice:
                    voice.speak(insight)

                last_auto_insight = now

    finally:
        detector.stop()
        if voice:
            voice.close()
        cv2.destroyAllWindows()
        if args.save_report:
            _save_session_report(args.save_report, session_started, session_events)
        print("\n[NeuralMirror] Session ended. Stay well. 💚")


if __name__ == "__main__":
    main()
