"""
NeuralMirror — Voice Output (Murf TTS)
Converts the AI's text insight to a natural-sounding voice using the Murf API,
then plays the audio directly through the system speakers via PyAudio.
"""

from __future__ import annotations

import io
import threading
from typing import Optional

import requests
import pyaudio
import wave

from config import MURF_API_KEY, MURF_VOICE_ID, AUDIO_SAMPLE_RATE, AUDIO_CHANNELS

_MURF_TTS_URL = "https://api.murf.ai/v1/speech/generate"


class VoiceOutput:
    """
    Asynchronous TTS engine backed by Murf.
    Calls are non-blocking — audio plays in a daemon thread so the
    main loop can continue capturing pulse data.
    """

    def __init__(self) -> None:
        self._pa = pyaudio.PyAudio()
        self._lock = threading.Lock()        # prevent overlapping playback
        self._current_thread: Optional[threading.Thread] = None

    def speak(self, text: str, blocking: bool = False) -> None:
        """
        Synthesise *text* via Murf and play it.

        Parameters
        ----------
        text:      The AI-generated insight string.
        blocking:  If True, wait for playback to finish before returning.
        """
        t = threading.Thread(target=self._tts_and_play, args=(text,), daemon=True)
        with self._lock:
            self._current_thread = t
        t.start()
        if blocking:
            t.join()

    def close(self) -> None:
        """Release PyAudio resources."""
        self._pa.terminate()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _tts_and_play(self, text: str) -> None:
        try:
            audio_bytes = self._call_murf(text)
            self._play_wav(audio_bytes)
        except Exception as exc:
            print(f"[VoiceOutput] Error: {exc}")

    def _call_murf(self, text: str) -> bytes:
        """POST to Murf REST API and return WAV bytes."""
        if not MURF_API_KEY or MURF_API_KEY == "YOUR_MURF_API_KEY":
            raise ValueError(
                "Missing MURF_API_KEY. Add your key to .env (see .env.example)."
            )

        headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "voiceId": MURF_VOICE_ID,
            "text": text,
            "audioFormat": "WAV",
            "sampleRate": AUDIO_SAMPLE_RATE,
            "channelType": "MONO" if AUDIO_CHANNELS == 1 else "STEREO",
        }
        resp = requests.post(_MURF_TTS_URL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()

        # Murf returns a JSON body with an audioFile URL
        data = resp.json()
        audio_url: str = data["audioFile"]
        wav_resp = requests.get(audio_url, timeout=15)
        wav_resp.raise_for_status()
        return wav_resp.content

    def _play_wav(self, wav_bytes: bytes) -> None:
        """Decode WAV bytes and stream through PyAudio."""
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            stream = self._pa.open(
                format=self._pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )
            chunk = 1024
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            stream.stop_stream()
            stream.close()
