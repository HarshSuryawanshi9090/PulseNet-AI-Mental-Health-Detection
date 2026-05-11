/**
 * PulseNet Content Script
 * Scrapes social media post text and sends to backend for distress analysis.
 * Only runs if user has given consent (stored in chrome.storage).
 */

const API_BASE = "http://localhost:5000/api";
const ANALYZED_ATTR = "data-pulsenet-analyzed";
const INTERVAL_MS = 8000;

// ── Selectors per platform ───────────────────────────────────────────────────
const SELECTORS = {
  "twitter.com":    '[data-testid="tweetText"]',
  "x.com":          '[data-testid="tweetText"]',
  "instagram.com":  "._a9zs span, .C4VMK span, article div[class*='Post'] span",
  "linkedin.com":   ".feed-shared-update-v2__description span[dir]",
};

function getSiteSelector() {
  const host = location.hostname.replace("www.", "");
  return SELECTORS[host] || null;
}

function extractText(el) {
  return el.innerText?.trim() || "";
}

async function analyzePost(text, el) {
  if (!text || text.length < 10) return;
  el.setAttribute(ANALYZED_ATTR, "true");

  try {
    const res = await fetch(`${API_BASE}/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, source: location.hostname }),
    });
    const data = await res.json();
    if (data.analysis) {
      injectScoreBadge(el, data.analysis);
      chrome.runtime.sendMessage({ type: "NEW_SCORE", data: data.analysis });
    }
  } catch (e) {
    // API not running — silent fail
  }
}

function injectScoreBadge(el, analysis) {
  const colors = {
    "Healthy": "#34C759", "Mild Distress": "#FFCC00",
    "Moderate": "#FF9500", "High Risk": "#FF6B35", "Crisis": "#FF3B30",
  };
  const color = colors[analysis.category] || "#888";
  const badge = document.createElement("span");
  badge.style.cssText = `
    display:inline-block; margin-left:8px; padding:2px 8px; border-radius:100px;
    font-size:11px; font-weight:700; color:${color};
    border:1px solid ${color}40; background:${color}18;
    vertical-align:middle; cursor:default; font-family:sans-serif;
  `;
  badge.title = `PulseNet: ${analysis.category} (${analysis.score}/100)`;
  badge.textContent = `🧠 ${analysis.score}`;
  el.closest("article")?.querySelector('[lang]')?.appendChild(badge) ||
    el.parentElement?.appendChild(badge);
}

function scanPage(selector) {
  document.querySelectorAll(selector).forEach((el) => {
    if (!el.getAttribute(ANALYZED_ATTR)) {
      analyzePost(extractText(el), el);
    }
  });
}

// ── Main ─────────────────────────────────────────────────────────────────────
chrome.storage.sync.get(["pulsenet_enabled"], ({ pulsenet_enabled }) => {
  if (pulsenet_enabled === false) return;

  const selector = getSiteSelector();
  if (!selector) return;

  // Initial scan
  setTimeout(() => scanPage(selector), 2000);

  // Periodic scan (SPA navigation)
  setInterval(() => scanPage(selector), INTERVAL_MS);

  // MutationObserver for infinite scroll
  const observer = new MutationObserver(() => scanPage(selector));
  observer.observe(document.body, { childList: true, subtree: true });
});
