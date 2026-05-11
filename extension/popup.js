// PulseNet Popup Logic
const DASHBOARD_URL = "http://localhost:5000/../frontend/dashboard.html";
const CAT_COLORS = {
  "Healthy": "#34C759", "Mild Distress": "#FFCC00",
  "Moderate": "#FF9500", "High Risk": "#FF6B35", "Crisis": "#FF3B30",
};

const toggle   = document.getElementById("toggle");
const scoreVal = document.getElementById("scoreVal");
const scoreCat = document.getElementById("scoreCat");
const statusDot  = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const dashBtn  = document.getElementById("dashBtn");
const clearBtn = document.getElementById("clearBtn");

// ── Load state ───────────────────────────────────────────────────────────────
chrome.storage.sync.get(["pulsenet_enabled"], ({ pulsenet_enabled }) => {
  toggle.checked = pulsenet_enabled !== false;
  updateStatus(toggle.checked);
});

chrome.storage.session.get(["latest_score"], ({ latest_score }) => {
  if (latest_score) renderScore(latest_score);
});

// ── Toggle monitoring ────────────────────────────────────────────────────────
toggle.addEventListener("change", () => {
  chrome.storage.sync.set({ pulsenet_enabled: toggle.checked });
  updateStatus(toggle.checked);
  if (!toggle.checked) {
    chrome.action.setBadgeText({ text: "OFF" });
    chrome.action.setBadgeBackgroundColor({ color: "#4A5568" });
  } else {
    chrome.action.setBadgeText({ text: "ON" });
    chrome.action.setBadgeBackgroundColor({ color: "#34C759" });
  }
});

clearBtn.addEventListener("click", () => {
  chrome.action.setBadgeText({ text: "" });
  chrome.storage.session.remove("latest_score");
  scoreVal.textContent = "--";
  scoreCat.textContent = "No data yet";
  scoreCat.style.color = "#8B9AB3";
  scoreCat.style.borderColor = "rgba(255,255,255,0.08)";
});

dashBtn.addEventListener("click", (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: "http://127.0.0.1:5500/frontend/dashboard.html" });
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function renderScore(data) {
  scoreVal.textContent = data.score;
  scoreCat.textContent = `${data.category_emoji || ""} ${data.category}`;
  const color = CAT_COLORS[data.category] || "#8B9AB3";
  scoreCat.style.color = color;
  scoreCat.style.borderColor = color + "50";
  scoreCat.style.background = color + "18";
  statusText.textContent = `Last analyzed: ${new Date(data.analyzed_at).toLocaleTimeString()}`;
}

function updateStatus(enabled) {
  statusDot.className = "dot" + (enabled ? "" : " off");
  if (!enabled) statusText.textContent = "Monitoring paused";
}

// ── Listen for live updates ──────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "NEW_SCORE") renderScore(msg.data);
});
