"""
NeuralMirror — Configuration
Centralises all API keys, tunable parameters, and hardware settings.
Load secrets from a .env file so nothing sensitive is committed to Git.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in project root

# ─── Murf TTS ────────────────────────────────────────────────────────────────
MURF_API_KEY: str = os.getenv("MURF_API_KEY", "")
MURF_VOICE_ID: str = os.getenv("MURF_VOICE_ID", "en-US-natalie")   # calm, empathic voice
MURF_MODEL: str = os.getenv("MURF_MODEL", "FALCON")
MURF_REGION: str = os.getenv("MURF_REGION", "GLOBAL")
MURF_LOCALE: str = os.getenv("MURF_LOCALE", "en-US")

# ─── OpenAI / LLM Brain ──────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
LLM_MODEL: str = "gpt-4o"
LLM_RESPONSE_STYLE: str = os.getenv("LLM_RESPONSE_STYLE", "oracle")
LLM_SYSTEM_PROMPT: str = (
    "You are NeuralMirror — an empathic AI wellness companion. "
    "You receive the user's real-time heart rate and stress signals "
    "captured by their webcam. Respond with calm, supportive insights "
    "grounded in evidence-based wellness science. Keep responses under 3 sentences."
)

# ─── Webcam / Pulse Detection ────────────────────────────────────────────────
CAMERA_INDEX: int = 0            # 0 = default webcam
FRAME_BUFFER_SECONDS: int = 30   # seconds of video to buffer for rPPG analysis
TARGET_FPS: int = 30
ROI_SCALE: float = 0.25          # fraction of face ROI used for colour sampling

# ─── HeartPy DSP ─────────────────────────────────────────────────────────────
HP_SAMPLE_RATE: float = float(TARGET_FPS)
HP_BAND_LOW: float = 0.75        # Hz  — ~45 BPM minimum
HP_BAND_HIGH: float = 3.5        # Hz  — ~210 BPM maximum

# ─── Stress Thresholds ───────────────────────────────────────────────────────
STRESS_BPM_HIGH: int = 100       # BPM above this = elevated stress flag
STRESS_BPM_LOW: int = 50         # BPM below this = bradycardia flag

# ─── Audio Output ────────────────────────────────────────────────────────────
AUDIO_SAMPLE_RATE: int = 44100
AUDIO_CHANNELS: int = 1
