const form = document.getElementById("profile-form");
const results = document.getElementById("results");

const baselineEl = document.getElementById("baseline");
const savedEl = document.getElementById("saved");
const afterEl = document.getElementById("after");
const coachTextEl = document.getElementById("coach-text");
const actionsList = document.getElementById("actions-list");

const barBefore = document.getElementById("bar-before");
const barAfter = document.getElementById("bar-after");

function toNumber(id) {
  const value = document.getElementById(id).value;
  return Number.parseFloat(value || "0");
}

function formatKg(value) {
  return `${Math.round(value).toLocaleString()} kg CO2e`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    city: document.getElementById("city").value,
    commute_km_week: toNumber("commute_km_week"),
    meat_meals_week: toNumber("meat_meals_week"),
    home_kwh_month: toNumber("home_kwh_month"),
    flights_year: toNumber("flights_year"),
    recycling: document.getElementById("recycling").checked,
  };

  const response = await fetch("/api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    alert("Unable to generate your plan right now. Try again.");
    return;
  }

  const data = await response.json();

  baselineEl.textContent = formatKg(data.baseline_kg_co2);
  savedEl.textContent = formatKg(data.potential_kg_saved);
  afterEl.textContent = formatKg(data.after_kg_co2);
  coachTextEl.textContent = data.coach_text;

  actionsList.innerHTML = "";
  data.actions.forEach((action) => {
    const li = document.createElement("li");
    li.textContent = `${action.title} - save ~${Math.round(action.annual_kg_saved)} kg/year (${action.effort} effort). ${action.why_it_works}`;
    actionsList.appendChild(li);
  });

  const max = Math.max(data.baseline_kg_co2, 1);
  barBefore.style.width = `${Math.min((data.baseline_kg_co2 / max) * 100, 100)}%`;
  barAfter.style.width = `${Math.min((data.after_kg_co2 / max) * 100, 100)}%`;

  results.classList.remove("hidden");
  results.scrollIntoView({ behavior: "smooth", block: "start" });
});
