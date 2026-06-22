/**
 * PulseNet Dashboard — JavaScript
 * Handles all API calls, Chart.js rendering, score ring, and UI updates.
 */

const API = (window.location.protocol === "file:") ? "http://localhost:5000/api" : "/api";

const CAT_COLOR = {
  "Healthy": "#34C759", "Mild Distress": "#FFCC00",
  "Moderate": "#FF9500", "High Risk": "#FF6B35", "Crisis": "#FF3B30",
};
const CAT_EMOJI = {
  "Healthy":"😊","Mild Distress":"😕","Moderate":"😟","High Risk":"😰","Crisis":"🆘"
};
const TIPS = {
  Healthy:      ["🧘 Keep up your mindfulness routine","🌿 You're doing great — maintain healthy habits","💬 Continue sharing your feelings openly","🎯 Set small, positive goals for the week"],
  "Mild Distress":["🚶 Take a short walk outside today","📓 Journal what's on your mind","☕ Schedule a coffee chat with a friend","🎵 Listen to music that uplifts you"],
  Moderate:     ["📞 Reach out to someone you trust","🧘 Try a 10-min guided meditation","🛌 Prioritize getting enough sleep","🆘 Consider talking to a counsellor"],
  "High Risk":  ["📞 Call a trusted friend or family now","🤝 Contact your guardian","🏥 Seek professional support soon","☎️ iCall: 9152987821"],
  Crisis:       ["🆘 You're not alone — please reach out","☎️ AASRA: 9820466627","☎️ iCall: 9152987821","🏥 Go to your nearest hospital if unsafe"],
};

let trendChart = null;
let lastAnalysis = null;

// ── API Helpers ───────────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  try {
    const res = await fetch(API + path, {
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      ...opts,
    });
    if (res.status === 401) {
      window.location.href = "/login";
      return null;
    }
    return await res.json();
  } catch {
    return null;
  }
}

// ── Check API status ──────────────────────────────────────────────────────────
async function checkAPI() {
  const data = await apiFetch("/health");
  const dot = document.getElementById("apiDot");
  const txt = document.getElementById("apiStatusText");
  if (data?.status === "ok") {
    dot.className = "api-dot";
    txt.textContent = "API Connected";
  } else {
    dot.className = "api-dot offline";
    txt.textContent = "API Offline";
  }
  return !!data;
}

// ── Load dashboard data ───────────────────────────────────────────────────────
async function loadDashboard() {
  const data = await apiFetch("/dashboard");
  if (!data) return;

  // Stats
  setText("statCurrent", data.current_score);
  setText("statCurrentCat", data.current_category);
  setText("statAvg", data.rolling_avg);
  setText("statPeak", data.peak_score);
  setText("statTotal", data.total_posts);

  document.getElementById("statCurrent").style.color = CAT_COLOR[data.current_category] || "#34C759";

  // Score ring
  animateRing(data.current_score, data.current_category);

  // Trend chart
  renderChart(data.seven_day);

  // Recent posts
  renderPosts(data.recent_posts, "recentPostsList", 5);
  renderPosts(data.recent_posts, "historyList");
  setText("historyCount", `${data.total_posts} posts analyzed`);

  // Tips
  renderTips(data.current_category);
}

// ── Score Ring ────────────────────────────────────────────────────────────────
function animateRing(score, category) {
  const circumference = 477.5;
  const fill = document.getElementById("ringFill");
  const offset = circumference - (score / 100) * circumference;
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = CAT_COLOR[category] || "#34C759";

  // Animate number
  const numEl = document.getElementById("ringNumber");
  let current = parseInt(numEl.textContent) || 0;
  const step = () => {
    if (current < score) { current = Math.min(current + 2, score); numEl.textContent = current; requestAnimationFrame(step); }
    else if (current > score) { current = Math.max(current - 2, score); numEl.textContent = current; requestAnimationFrame(step); }
  };
  requestAnimationFrame(step);
  numEl.style.color = CAT_COLOR[category] || "#34C759";

  setText("ringCat", category);
  setText("ringEmoji", CAT_EMOJI[category] || "😊");
  document.getElementById("ringCat").style.color = CAT_COLOR[category] || "#34C759";
}

// ── Chart ─────────────────────────────────────────────────────────────────────
function renderChart(days) {
  const ctx = document.getElementById("trendChart");
  if (!ctx) return;

  const labels = days.map(d => d.label);
  const scores = days.map(d => d.avg_score);
  const colors = scores.map(s => {
    if (s >= 81) return "#FF3B30";
    if (s >= 61) return "#FF6B35";
    if (s >= 41) return "#FF9500";
    if (s >= 21) return "#FFCC00";
    return "#34C759";
  });

  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Distress Score",
        data: scores,
        borderColor: "#00D4FF",
        backgroundColor: "rgba(0,212,255,0.08)",
        borderWidth: 2.5,
        pointBackgroundColor: colors,
        pointBorderColor: colors,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.4,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0d1220",
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1,
          callbacks: {
            label: (ctx) => ` Score: ${ctx.parsed.y}/100`,
          },
        },
      },
      scales: {
        x: { grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#8B9AB3", font: { size: 11 } } },
        y: {
          min: 0, max: 100,
          grid: { color: "rgba(255,255,255,0.04)" },
          ticks: { color: "#8B9AB3", font: { size: 11 }, callback: v => v },
        },
      },
    },
  });
}

// ── Posts ─────────────────────────────────────────────────────────────────────
function renderPosts(posts, containerId, limit = 100) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!posts.length) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">📭</div><p>No posts yet. Load demo data or analyze text.</p></div>`;
    return;
  }
  el.innerHTML = posts.slice(0, limit).map(p => {
    const cat = p.category || "Healthy";
    const cls = catClass(cat);
    const time = new Date(p.created_at + "Z").toLocaleString();
    return `
      <div class="post-item">
        <div class="post-header">
          <div class="post-meta">
            <span class="badge badge-${cls}">${CAT_EMOJI[cat] || ""} ${cat}</span>
            <span class="post-source">${p.source || "manual"}</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            ${p.crisis_detected ? '<span class="badge badge-crisis">🆘 Crisis</span>' : ""}
            <span style="font-family:\'Space Grotesk\',sans-serif;font-size:18px;font-weight:800;color:${CAT_COLOR[cat]}">${p.score}</span>
          </div>
        </div>
        <div class="post-text">${escHtml(p.text)}</div>
        <div class="post-time" style="margin-top:6px;">${time}</div>
      </div>`;
  }).join("");
}

// ── Guardians ─────────────────────────────────────────────────────────────────
async function loadGuardians() {
  const data = await apiFetch("/guardians");
  const el = document.getElementById("guardiansList");
  if (!data || !data.length) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">🤝</div><p>No guardians added yet.</p></div>`;
    return;
  }
  el.innerHTML = data.map(g => `
    <div class="card guardian-card">
      <div class="guardian-info">
        <h4>${escHtml(g.name)}</h4>
        <p>${g.email || "No email"} ${g.phone ? "· " + g.phone : ""}</p>
      </div>
      <div class="guardian-actions">
        <span class="threshold-badge">Alert ≥ ${g.threshold}</span>
        <button class="btn btn-ghost btn-sm" onclick="testAlert(${g.id})">🔔 Test</button>
        <button class="btn btn-danger btn-sm" onclick="removeGuardian(${g.id})">✕</button>
      </div>
    </div>`).join("");
}

async function removeGuardian(id) {
  await apiFetch(`/guardians/${id}`, { method: "DELETE" });
  loadGuardians();
}

async function testAlert(id) {
  const data = await apiFetch("/test-alert", { method: "POST", body: JSON.stringify({ guardian_id: id, score: 75 }) });
  alert(data?.success ? `✅ Test alert logged for ${data.guardian}${data.simulated ? " (simulated — add SMTP config for real email)" : " (email sent!)"}` : "Failed to send test alert");
  loadAlerts();
}

// ── Alerts ────────────────────────────────────────────────────────────────────
async function loadAlerts() {
  const data = await apiFetch("/alerts");
  const el = document.getElementById("alertsList");
  const dot = document.getElementById("alertDot");
  if (!data || !data.length) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">🔔</div><p>No alerts yet.</p></div>`;
    dot.style.display = "none"; return;
  }
  dot.style.display = "inline-block";
  el.innerHTML = data.map(a => `
    <div class="card alert-item">
      <div class="alert-header">
        <div class="alert-guardian">🤝 ${escHtml(a.guardian_name || "Unknown")}</div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="alert-score">Score: ${a.triggered_score}/100</span>
          <span class="alert-status status-${a.status}">${a.status}</span>
        </div>
      </div>
      <div class="alert-msg">${escHtml(a.message?.slice(0, 160) || "")}…</div>
      <div class="alert-time">${new Date(a.created_at + "Z").toLocaleString()}</div>
    </div>`).join("");
}

// ── Tips ──────────────────────────────────────────────────────────────────────
function renderTips(category) {
  const tips = TIPS[category] || TIPS.Healthy;
  document.getElementById("tipsList").innerHTML = tips.map(t =>
    `<div class="tip-item"><span class="tip-icon">${t.slice(0,2)}</span>${t.slice(2)}</div>`
  ).join("");
}

// ── Analyze ───────────────────────────────────────────────────────────────────
async function analyzeText() {
  const text = document.getElementById("analyzeText").value.trim();
  if (!text) { alert("Please enter some text to analyze."); return; }

  const btn = document.getElementById("analyzeBtn");
  btn.innerHTML = '<span class="spinner"></span> Analyzing…'; btn.disabled = true;

  const data = await apiFetch("/analyze", { method: "POST", body: JSON.stringify({ text }) });
  btn.innerHTML = "🧠 Analyze Now"; btn.disabled = false;
  if (!data) { alert("API not reachable. Start the backend first."); return; }

  lastAnalysis = { text, ...data };

  const res = document.getElementById("analyzeResult");
  res.classList.add("show");

  const score = data.score;
  const color = CAT_COLOR[data.category] || "#34C759";
  const scoreEl = document.getElementById("resultScore");
  scoreEl.textContent = score; scoreEl.style.color = color;
  setText("resultCat", `${data.category_emoji} ${data.category}`);
  document.getElementById("resultCat").style.color = color;
  setText("resultEmoji", data.category_emoji);
  setText("resultBar", "");
  document.getElementById("resultBar").style.width = score + "%";
  document.getElementById("resultBar").style.background = color;
  setText("resultSentiment", capitalize(data.sentiment));
  setText("resultWords", data.text_length + " words");
  setText("resultCrisis", data.crisis_detected ? "⚠️ Yes" : "✅ No");
  setText("resultTime", new Date(data.analyzed_at + "Z").toLocaleTimeString());

  // Keywords
  const kwEl = document.getElementById("resultKeywords");
  kwEl.innerHTML = (data.keywords_found || []).map(k =>
    `<span class="keyword-tag kw-${k.severity}">${k.word}</span>`
  ).join("") || '<span style="color:var(--text-muted);font-size:12px;">No significant keywords detected</span>';

  document.getElementById("savePostBtn").style.display = "inline-flex";
}

async function savePost() {
  if (!lastAnalysis) return;
  await apiFetch("/posts", { method: "POST", body: JSON.stringify({ text: lastAnalysis.text, source: "manual" }) });
  document.getElementById("savePostBtn").style.display = "none";
  loadDashboard(); loadAlerts();
  alert("✅ Post saved to history!");
}

// ── Nav / Tabs ────────────────────────────────────────────────────────────────
const PANEL_META = {
  overview:  { title: "Wellness Overview",  sub: "Your 7-day emotional trend" },
  analyze:   { title: "Analyze Text",       sub: "Instant distress detection" },
  history:   { title: "Post History",       sub: "All analyzed posts" },
  guardians: { title: "Guardian Network",   sub: "Trusted contacts for crisis alerts" },
  alerts:    { title: "Alert History",      sub: "Guardian notifications" },
};

document.querySelectorAll(".nav-item[data-panel]").forEach(btn => {
  btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
});
document.getElementById("viewAllBtn")?.addEventListener("click", () => switchPanel("history"));

function switchPanel(name) {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.panel === name));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === "panel-" + name));
  const meta = PANEL_META[name] || {};
  setText("panelTitle", meta.title || name);
  setText("panelSub",   meta.sub   || "");
  if (name === "guardians") loadGuardians();
  if (name === "alerts")    loadAlerts();
}

// ── Buttons ───────────────────────────────────────────────────────────────────
document.getElementById("refreshBtn").addEventListener("click", () => { loadDashboard(); checkAPI(); });

// Logout
document.getElementById("logoutBtn").addEventListener("click", async () => {
  await apiFetch("/auth/logout", { method: "POST" });
  window.location.href = "/login";
});

document.getElementById("analyzeBtn").addEventListener("click", analyzeText);
document.getElementById("savePostBtn").addEventListener("click", savePost);
document.getElementById("clearAnalyzeBtn").addEventListener("click", () => {
  document.getElementById("analyzeText").value = "";
  document.getElementById("analyzeResult").classList.remove("show");
  document.getElementById("savePostBtn").style.display = "none";
  lastAnalysis = null;
});

document.getElementById("seedBtn").addEventListener("click", async () => {
  document.getElementById("seedBtn").textContent = "⏳ Seeding…";
  await apiFetch("/seed", { method: "POST" });
  await loadDashboard();
  document.getElementById("seedBtn").textContent = "🌱 Load Demo Data";
});

document.querySelectorAll(".demo-text").forEach(btn => {
  btn.addEventListener("click", () => {
    document.getElementById("analyzeText").value = btn.dataset.text;
    switchPanel("analyze");
    analyzeText();
  });
});

document.getElementById("addGuardianBtn").addEventListener("click", async () => {
  const name = document.getElementById("gName").value.trim();
  if (!name) { alert("Name is required"); return; }
  const res = await apiFetch("/guardians", {
    method: "POST",
    body: JSON.stringify({
      name, email: document.getElementById("gEmail").value,
      phone: document.getElementById("gPhone").value,
      threshold: parseInt(document.getElementById("gThreshold").value) || 70,
    }),
  });
  if (res?.success) {
    ["gName","gEmail","gPhone"].forEach(id => document.getElementById(id).value = "");
    document.getElementById("gThreshold").value = "70";
    loadGuardians();
  }
});

// Profile modal
document.getElementById("profileBtn").addEventListener("click", async () => {
  const p = await apiFetch("/profile");
  if (p) { document.getElementById("profileName").value = p.name; document.getElementById("profileEmail").value = p.email; }
  document.getElementById("profileModal").classList.add("show");
});
document.getElementById("closeProfileModal").addEventListener("click", () => document.getElementById("profileModal").classList.remove("show"));
document.getElementById("saveProfileBtn").addEventListener("click", async () => {
  await apiFetch("/profile", { method: "PUT", body: JSON.stringify({ name: document.getElementById("profileName").value, email: document.getElementById("profileEmail").value }) });
  document.getElementById("profileModal").classList.remove("show");
});
document.getElementById("profileModal").addEventListener("click", (e) => { if (e.target === e.currentTarget) e.currentTarget.classList.remove("show"); });

// ── Utils ─────────────────────────────────────────────────────────────────────
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val ?? ""; }
function escHtml(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }
function catClass(cat) {
  const map = { "Healthy":"healthy","Mild Distress":"mild","Moderate":"moderate","High Risk":"high","Crisis":"crisis" };
  return map[cat] || "healthy";
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  // Auth guard — redirect to login if not authenticated
  const user = await apiFetch("/auth/me");
  if (!user || user.error) {
    window.location.href = "/login";
    return;
  }
  // Show username in topbar
  const titleEl = document.getElementById("panelTitle");
  document.getElementById("panelSub").textContent = `Signed in as ${user.username}`;

  await checkAPI();
  await loadDashboard();
})();
