# EcoTwin - Earth Day Hackathon MVP

EcoTwin is a personalized climate action coach. Users enter a few lifestyle signals, and the app returns:

- estimated annual CO2e footprint,
- practical reduction opportunities,
- an AI-generated short action plan (Gemini when configured, local fallback otherwise).

## Why This Can Win

- Clear Earth Day relevance: direct emissions reduction for everyday life.
- Creative angle: "AI twin" framing with habit-to-impact translation.
- Technical execution: full stack app with API, dynamic UI, scoring model, and AI summary flow.
- Category-ready path: meaningful Gemini integration and strong GitHub Copilot-assisted build workflow.

## Stack

- Python + Flask backend
- HTML/CSS/JS frontend
- Optional Gemini API integration via REST

## Quick Start

1. Create and activate your virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Optionally add Gemini key:

```powershell
copy .env.example .env
# then set GEMINI_API_KEY in .env
```

4. Run:

```powershell
python app.py
```

5. Open http://127.0.0.1:5000

## Permanent Deployment (Render)

This project includes `render.yaml` for one-click Blueprint deployment.

1. Push your repo to GitHub.
2. In Render, click `New +` -> `Blueprint`.
3. Select your GitHub repo.
4. Confirm the service settings from `earthday-ecotwin/render.yaml`.
5. Set environment variable `GEMINI_API_KEY` in Render dashboard.
6. Deploy and use the generated `.onrender.com` URL as your permanent demo link.

If you prefer manual setup on Render, create a Python Web Service with:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Root directory: `earthday-ecotwin`

## Alternative Deployment (Railway)

Railway can deploy this app using the included `Procfile`.

1. Create a new Railway project from your GitHub repo.
2. Set root directory to `earthday-ecotwin`.
3. Add `GEMINI_API_KEY` environment variable.
4. Deploy and use the provided Railway domain as a stable demo URL.

## Demo Script For Submission

1. Enter a city and baseline lifestyle values.
2. Click "Generate My Climate Plan."
3. Show before/after bars and top actions.
4. Highlight AI coach text and explain projected annual savings.

## Prize Category Mapping

- Best use of GitHub Copilot: document assisted architecture, code generation, refactors, and testing workflow in your submission write-up.
- Best use of Google Gemini: enable GEMINI_API_KEY and show personalized summary generation from profile + action data.

## Suggested Next Upgrades

- Add account system and saved progress streaks.
- Pull city-specific public transit and energy grid data.
- Add team mode so communities compete on emissions reduction.
