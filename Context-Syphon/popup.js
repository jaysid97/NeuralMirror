const syphonBtn = document.getElementById("syphonBtn");
const copyBtn = document.getElementById("copyBtn");
const modeSelect = document.getElementById("modeSelect");
const previewEl = document.getElementById("preview");
const statusEl = document.getElementById("status");

let latestPayload = "";

function getStatusDirective(mode) {
  if (mode === "creative") {
    return "Generate an imaginative angle, metaphors, and 3 novel idea branches.";
  }
  if (mode === "strategic") {
    return "Deliver structured insight with risks, opportunities, and next actions.";
  }
  return "Summarize the context quickly with key facts and one suggested next step.";
}

function buildPayload(tab, mode) {
  const pageUrl = new URL(tab.url);
  const missionId = Math.random().toString(36).slice(2, 8).toUpperCase();

  return [
    "[SYSTEM: CONTEXT_SYPHON_V2]",
    `Mission ID: ${missionId}`,
    `Capture Mode: ${mode.toUpperCase()}`,
    `Target Title: ${tab.title || "Untitled"}`,
    `Target Source: ${tab.url}`,
    `Target Domain: ${pageUrl.hostname}`,
    `Captured At: ${new Date().toISOString()}`,
    "",
    "[ANALYSIS DIRECTIVE]",
    getStatusDirective(mode),
  ].join("\n");
}

function setStatus(message, color) {
  statusEl.innerText = message;
  statusEl.style.color = color;
}

syphonBtn.addEventListener("click", async () => {
  setStatus("Scanning active signal...", "#98b2be");

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tab = tabs && tabs[0];
    if (!tab || !tab.url) {
      setStatus("No active tab context found.", "#ff9a8a");
      return;
    }

    try {
      const mode = modeSelect.value;
      latestPayload = buildPayload(tab, mode);
      previewEl.value = latestPayload;
      await navigator.clipboard.writeText(latestPayload);

      setStatus("Payload captured and copied.", "#53f4c8");
      syphonBtn.innerText = "Syphon Complete";
    } catch (err) {
      setStatus("Capture failed.", "#ff9a8a");
      console.error(err);
    }
  });
});

copyBtn.addEventListener("click", async () => {
  if (!latestPayload) {
    setStatus("Nothing to copy yet. Run syphon first.", "#ffb347");
    return;
  }

  try {
    await navigator.clipboard.writeText(latestPayload);
    setStatus("Preview copied to clipboard.", "#53f4c8");
  } catch (err) {
    setStatus("Clipboard copy failed.", "#ff9a8a");
    console.error(err);
  }
});
