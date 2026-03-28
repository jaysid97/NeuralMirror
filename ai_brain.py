"""
NeuralMirror — AI Brain
Sends pulse + stress data to an LLM and returns an empathic wellness insight.
Keeps a rolling conversation history so the AI can track trends over time.
Gracefully falls back to templated responses if OpenAI API is unavailable.
"""

from __future__ import annotations

from statistics import mean
from typing import Optional
from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    LLM_MODEL,
    LLM_SYSTEM_PROMPT,
    LLM_RESPONSE_STYLE,
)
from pulse_detector import PulseReading

_MAX_HISTORY = 10  # keep last N user/assistant turns in context


class AIBrain:
    """Wrapper around the OpenAI chat completion API."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self._history: list[dict[str, str]] = []
        self._style = "oracle"
        self.set_style(LLM_RESPONSE_STYLE)

    @property
    def style(self) -> str:
        return self._style

    def set_style(self, style: str) -> None:
        allowed = {"oracle", "tactical", "poetic"}
        normalized = style.strip().lower()
        self._style = normalized if normalized in allowed else "oracle"

    def analyse(self, reading: PulseReading, user_note: Optional[str] = None) -> str:
        """
        Build a biometric prompt from *reading* and return the AI's insight.

        Parameters
        ----------
        reading:    Latest PulseReading from the detector.
        user_note:  Optional free-text from the user ("I feel anxious right now").

        Returns
        -------
        The AI's plain-text response string. Falls back to templated response if API unavailable.
        """
        prompt = self._build_prompt(reading, user_note)
        self._history.append({"role": "user", "content": prompt})

        # Trim history to avoid token overflow
        if len(self._history) > _MAX_HISTORY * 2:
            self._history = self._history[-(_MAX_HISTORY * 2):]

        messages = [{"role": "system", "content": self._system_prompt()}] + self._history

        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
            )
            content = response.choices[0].message.content or ""
            reply = content.strip()
            if not reply:
                reply = self._generate_fallback(reading, user_note)
            self._history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            # Fallback: generate response from template when API fails
            print(f"⚠ AI API unavailable ({str(e)[:50]}), using templated response.")
            fallback = self._generate_fallback(reading, user_note)
            self._history.append({"role": "assistant", "content": fallback})
            return fallback

    def chat(
        self,
        user_message: str,
        reading: Optional[PulseReading] = None,
        recent_readings: Optional[list[PulseReading]] = None,
    ) -> str:
        """
        Conversational entrypoint for a live chat interaction.

        If biometric data is available, include a compact context block so the
        assistant can adapt advice to the user's current physiological state.
        """
        prompt = self._build_chat_prompt(user_message, reading, recent_readings or [])
        self._history.append({"role": "user", "content": prompt})

        if len(self._history) > _MAX_HISTORY * 2:
            self._history = self._history[-(_MAX_HISTORY * 2):]

        messages = [{"role": "system", "content": self._system_prompt()}] + self._history
        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=220,
            )
            content = response.choices[0].message.content or ""
            reply = content.strip()
            if not reply:
                reply = self._generate_fallback_chat(user_message, reading)
            self._history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"⚠ AI API unavailable ({str(e)[:50]}), using templated response.")
            fallback = self._generate_fallback_chat(user_message, reading)
            self._history.append({"role": "assistant", "content": fallback})
            return fallback

    def reset(self) -> None:
        """Clear conversation history (start a fresh session)."""
        self._history.clear()

    def analyse_futurecast(
        self,
        reading: PulseReading,
        recent_readings: list[PulseReading],
        user_note: Optional[str] = None,
    ) -> str:
        """
        Build a forward-looking prompt from recent biometric trajectory.

        The model receives current state + recent averages/slopes and replies with
        a concise 10-minute forecast and one practical action protocol.
        """
        prompt = self._build_future_prompt(reading, recent_readings, user_note)
        self._history.append({"role": "user", "content": prompt})

        if len(self._history) > _MAX_HISTORY * 2:
            self._history = self._history[-(_MAX_HISTORY * 2):]

        messages = [{"role": "system", "content": self._system_prompt()}] + self._history
        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=220,
            )
            content = response.choices[0].message.content or ""
            reply = content.strip()
            if not reply:
                reply = self._generate_fallback_forecast(reading, recent_readings)
            self._history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"⚠ AI API unavailable ({str(e)[:50]}), using templated forecast.")
            fallback = self._generate_fallback_forecast(reading, recent_readings)
            self._history.append({"role": "assistant", "content": fallback})
            return fallback

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(reading: PulseReading, note: Optional[str]) -> str:
        lines = [
            f"Current heart rate: {reading.bpm:.1f} BPM",
            f"HRV SDNN: {reading.sdnn:.1f} ms  |  RMSSD: {reading.rmssd:.1f} ms",
            f"Composite stress index: {reading.stress_index:.2f} / 1.00",
            f"Signal confidence: {reading.confidence * 100:.0f}%",
        ]
        if note:
            lines.append(f'User note: "{note}"')
        lines.append(
            "Based on these biometrics, give me a short, empathic wellness insight."
        )
        return "\n".join(lines)

    @staticmethod
    def _build_future_prompt(
        reading: PulseReading,
        recent_readings: list[PulseReading],
        note: Optional[str],
    ) -> str:
        window = recent_readings[-8:] if recent_readings else [reading]

        avg_bpm = mean(r.bpm for r in window)
        avg_rmssd = mean(r.rmssd for r in window)
        avg_stress = mean(r.stress_index for r in window)

        if len(window) >= 2:
            bpm_delta = window[-1].bpm - window[0].bpm
            stress_delta = window[-1].stress_index - window[0].stress_index
        else:
            bpm_delta = 0.0
            stress_delta = 0.0

        lines = [
            "NeuralMirror FutureCast request:",
            f"Current BPM: {reading.bpm:.1f}",
            f"Current RMSSD: {reading.rmssd:.1f} ms",
            f"Current stress index: {reading.stress_index:.2f}",
            f"Recent avg BPM (last {len(window)} readings): {avg_bpm:.1f}",
            f"Recent avg RMSSD: {avg_rmssd:.1f} ms",
            f"Recent avg stress index: {avg_stress:.2f}",
            f"BPM trend delta over window: {bpm_delta:+.1f}",
            f"Stress trend delta over window: {stress_delta:+.2f}",
            "Predict likely state over the next 10 minutes (calmer/stable/escalating),",
            "then provide a compact 3-step protocol the user can do right now.",
            "Keep tone supportive and practical. Keep response under 5 short sentences.",
        ]
        if note:
            lines.append(f'User note: "{note}"')
        return "\n".join(lines)

    @staticmethod
    def _build_chat_prompt(
        user_message: str,
        reading: Optional[PulseReading],
        recent_readings: list[PulseReading],
    ) -> str:
        lines = ["NeuralMirror Live Chat message:"]

        if reading is not None:
            lines.extend(
                [
                    f"Current BPM: {reading.bpm:.1f}",
                    f"Current RMSSD: {reading.rmssd:.1f} ms",
                    f"Current stress index: {reading.stress_index:.2f}",
                    f"Signal confidence: {reading.confidence * 100:.0f}%",
                ]
            )

            window = recent_readings[-8:] if recent_readings else [reading]
            if len(window) >= 2:
                bpm_delta = window[-1].bpm - window[0].bpm
                stress_delta = window[-1].stress_index - window[0].stress_index
                lines.extend(
                    [
                        f"BPM trend delta over recent window: {bpm_delta:+.1f}",
                        f"Stress trend delta over recent window: {stress_delta:+.2f}",
                    ]
                )

        lines.append(f'User says: "{user_message}"')
        lines.append(
            "Reply conversationally as a supportive wellness coach. Keep it concise and actionable."
        )
        return "\n".join(lines)

    def _system_prompt(self) -> str:
        style_line = {
            "oracle": (
                "Response style: Oracle Mode. Be clear and visionary with concise "
                "future-facing guidance, still grounded in practical wellness steps."
            ),
            "tactical": (
                "Response style: Tactical Mode. Give precise, stepwise, measurable "
                "guidance with direct language."
            ),
            "poetic": (
                "Response style: Poetic Mode. Use warm, vivid language with a gentle "
                "motivational tone, while keeping advice practical."
            ),
        }[self._style]
        return f"{LLM_SYSTEM_PROMPT}\n{style_line}"

    # ── Fallback Templates (when OpenAI API is unavailable) ────────────────────

    def _generate_fallback(self, reading: PulseReading, user_note: Optional[str] = None) -> str:
        """Generate a templated response based on stress level when API fails."""
        stress = reading.stress_index
        bpm = reading.bpm

        if stress > 0.65:
            return f"Your heart rate is elevated at {bpm:.0f} BPM with higher stress signals. Try slow breathing: 4 seconds in, 6 out. Ground yourself in the present moment."
        elif stress > 0.4:
            return f"Heart rate at {bpm:.0f} BPM with moderate activation. A short walk or mindful pause could help. You're doing well staying aware."
        else:
            return f"Your biometrics show a calm state ({bpm:.0f} BPM). Great opportunity to reflect or gently challenge yourself if you have a goal in mind."

    def _generate_fallback_chat(self, user_message: str, reading: Optional[PulseReading] = None) -> str:
        """Generate a templated chat response when API fails."""
        context = ""
        if reading:
            if reading.stress_index > 0.65:
                context = " I notice your stress is elevated right now."
            elif reading.stress_index < 0.3:
                context = " I see your heart rate and stress are very calm."
        return f"I hear you.{context} I'm here to support you through this. What's one small thing that might help right now?"

    def _generate_fallback_forecast(self, reading: PulseReading, recent_readings: list[PulseReading]) -> str:
        """Generate a templated forecast when API fails."""
        if recent_readings:
            trend = "rising" if recent_readings[-1].bpm > recent_readings[0].bpm else "stable"
        else:
            trend = "stable"
        return f"Your stress trend looks {trend}. In the next 10 minutes, try to maintain this awareness. One action: take 3 conscious breaths every 2 minutes."

