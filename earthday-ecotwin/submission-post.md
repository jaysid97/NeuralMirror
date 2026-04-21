# EcoTwin: Your Personal Climate Twin for Earth Day

## Title Options
- EcoTwin: Your Personal Climate Twin for Earth Day
- EcoTwin: An AI Climate Coach for Real-World Emissions Cuts
- EcoTwin: Turning Everyday Habits Into Measurable Climate Action

## Cover Image Prompt
Create a bold editorial-style Earth Day cover image for a hackathon project called EcoTwin. Show a modern climate dashboard, lush green terrain, subtle planet visuals, and clean UI panels with before-and-after impact bars. Use rich greens, soft sunlight, and a polished futuristic look. Composition should fit a 1000:420 banner ratio.

*This is a submission for [Weekend Challenge: Earth Day Edition](https://dev.to/challenges/weekend-2026-04-16)*

## What I Built
Most climate tools diagnose. EcoTwin prescribes.

EcoTwin is a personalized climate action coach that turns a few everyday inputs, like commute habits, food choices, home energy use, and travel frequency, into a practical path with estimated annual CO2e savings.

The core idea is a climate mirror with a plan. Instead of stopping at a guilt score, EcoTwin estimates your baseline footprint, shows a before-and-after projection, and recommends the highest-impact changes first. The goal is low friction and clear momentum so users can see that small actions compound into meaningful annual reductions.

## Demo
Use this section to show the project in the simplest possible way:

- If deployed, paste the live URL first.
- If not deployed, paste a short screen recording link.
- If you have neither yet, describe the local flow in 3 to 5 steps and add screenshots.

Recommended demo format:

1. Open the app.
2. Enter a city and a few lifestyle inputs.
3. Click Generate My Climate Plan.
4. Show the before/after footprint and top actions.
5. Point out the Gemini-powered coach summary if enabled.

Run the app locally and try it live:

- Start the Flask app from the [project folder](./)
- Open the homepage
- Enter your city and a few lifestyle values
- Click Generate My Climate Plan
- Review the before/after footprint, recommended actions, and AI coach summary

If you want to include a deployed demo or video, add it here:

- Live demo: _add your URL_
- Video walkthrough: _add your URL_

## Code
Project files live in the [earthday-ecotwin folder](./earthday-ecotwin).

Key parts:

- [Backend app](./earthday-ecotwin/app.py) handles scoring, recommendations, and AI summary generation.
- [Action library](./earthday-ecotwin/data/actions.json) stores the curated reduction ideas and savings estimates.
- [Frontend](./earthday-ecotwin/templates/index.html), [styles](./earthday-ecotwin/static/styles.css), and [client logic](./earthday-ecotwin/static/app.js) power the UI.

## How I Built It
I built EcoTwin as a small full-stack Flask app so the submission would be easy to run and easy to judge.

The architecture is intentionally simple:

1. The frontend collects a few user inputs.
2. The backend estimates an annual baseline footprint with a transparent scoring model.
3. A curated action dataset is filtered by relevance to the user’s habits.
4. The app calculates projected savings and renders a before/after comparison.
5. If a Gemini API key is present, the app produces a concise personalized coaching summary. If not, it falls back to a deterministic local summary so the app still works fully offline.

I made the visual design bold on purpose. Earth Day projects can easily look generic, so I used a bright, editorial-style layout with layered gradients, strong typography, and a dashboard-like result section that makes the impact feel tangible.

The biggest product decision was to focus on practical behavior change instead of abstract environmental scoring. The app answers a simple question: "What should I do this week that actually matters?"

## Prize Categories
I am positioning this project for:

- Best use of Google Gemini: the app uses Gemini as a personalized climate coach when configured.
- Best use of GitHub Copilot: the project was scaffolded and iterated quickly with a Copilot-first workflow.

I am not claiming the other prize categories for this submission.

## What Makes This a Good Earth Day Project
EcoTwin connects directly to the theme by helping people reduce emissions through concrete, everyday decisions. It is creative enough to stand out, but still practical enough to demo clearly in a few seconds.

The project is also easy to explain in a submission post, which matters. Judges should be able to understand the purpose, the technical approach, and the user value without reading a long architecture essay.

## Next Steps
If I keep extending it, the next improvements would be:

- save user plans over time,
- add city-specific transit and energy data,
- build a community challenge mode,
- and track progress streaks so people can see the cumulative impact of their choices.

## Team
Solo submission.
