import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ACTIONS_FILE = BASE_DIR / "data" / "actions.json"

app = Flask(__name__)


def load_actions() -> List[Dict[str, Any]]:
    with ACTIONS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def estimate_annual_kg_co2(profile: Dict[str, Any]) -> float:
    commute_km_week = float(profile.get("commute_km_week", 0))
    meat_meals_week = float(profile.get("meat_meals_week", 0))
    home_kwh_month = float(profile.get("home_kwh_month", 0))
    flights_year = float(profile.get("flights_year", 0))

    # Rough model for hackathon impact storytelling.
    commute_kg_year = commute_km_week * 52 * 0.192
    meat_kg_year = meat_meals_week * 52 * 2.4
    home_kg_year = home_kwh_month * 12 * 0.4
    flights_kg_year = flights_year * 250

    if profile.get("recycling", False):
        recycling_savings = 120
    else:
        recycling_savings = 0

    total = commute_kg_year + meat_kg_year + home_kg_year + flights_kg_year - recycling_savings
    return round(max(total, 0), 2)


def personalize_actions(profile: Dict[str, Any], actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    commute_km_week = float(profile.get("commute_km_week", 0))
    meat_meals_week = float(profile.get("meat_meals_week", 0))
    home_kwh_month = float(profile.get("home_kwh_month", 0))
    flights_year = float(profile.get("flights_year", 0))

    filtered: List[Dict[str, Any]] = []

    for action in actions:
        trigger = action.get("trigger", "all")
        keep = False

        if trigger == "all":
            keep = True
        elif trigger == "commute" and commute_km_week >= 15:
            keep = True
        elif trigger == "food" and meat_meals_week >= 4:
            keep = True
        elif trigger == "home" and home_kwh_month >= 200:
            keep = True
        elif trigger == "travel" and flights_year >= 2:
            keep = True

        if keep:
            filtered.append(action)

    return sorted(filtered, key=lambda x: x["annual_kg_saved"], reverse=True)[:6]


def build_local_summary(city: str, baseline: float, potential: float, actions: List[Dict[str, Any]]) -> str:
    top_actions = ", ".join(action["title"] for action in actions[:3])
    return (
        f"Your estimated annual footprint is {baseline:.0f} kg CO2e. "
        f"In {city}, a practical path is to start with {top_actions}. "
        f"If you stay consistent, you can realistically avoid around {potential:.0f} kg CO2e this year."
    )


def generate_gemini_coach_text(city: str, profile: Dict[str, Any], baseline: float, actions: List[Dict[str, Any]]) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        potential = sum(a["annual_kg_saved"] for a in actions)
        return build_local_summary(city, baseline, potential, actions)

    prompt = {
        "city": city,
        "profile": profile,
        "baseline_kg_co2e": baseline,
        "recommended_actions": actions,
        "task": (
            "Write a concise motivating climate action plan in plain English. "
            "Use max 120 words, include 3 actions, and estimate annual impact."
        ),
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": json.dumps(prompt)}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        candidate = data.get("candidates", [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        if parts and "text" in parts[0]:
            return parts[0]["text"].strip()
    except Exception:
        pass

    potential = sum(a["annual_kg_saved"] for a in actions)
    return build_local_summary(city, baseline, potential, actions)


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.post("/api/plan")
def create_plan():
    payload = request.get_json(silent=True) or {}

    city = str(payload.get("city", "your city")).strip() or "your city"
    profile = {
        "commute_km_week": payload.get("commute_km_week", 0),
        "meat_meals_week": payload.get("meat_meals_week", 0),
        "home_kwh_month": payload.get("home_kwh_month", 0),
        "flights_year": payload.get("flights_year", 0),
        "recycling": bool(payload.get("recycling", False)),
    }

    baseline = estimate_annual_kg_co2(profile)
    actions = personalize_actions(profile, load_actions())
    potential = round(sum(a["annual_kg_saved"] for a in actions), 2)
    after = round(max(baseline - potential, 0), 2)
    coach_text = generate_gemini_coach_text(city, profile, baseline, actions)

    return jsonify(
        {
            "city": city,
            "baseline_kg_co2": baseline,
            "potential_kg_saved": potential,
            "after_kg_co2": after,
            "coach_text": coach_text,
            "actions": actions,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
