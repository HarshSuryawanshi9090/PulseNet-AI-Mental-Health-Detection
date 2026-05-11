// PulseNet Background Service Worker
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "NEW_SCORE") {
    const score = msg.data.score;
    // Update badge color based on severity
    let color = "#34C759";
    if (score >= 81) color = "#FF3B30";
    else if (score >= 61) color = "#FF6B35";
    else if (score >= 41) color = "#FF9500";
    else if (score >= 21) color = "#FFCC00";

    chrome.action.setBadgeText({ text: String(score) });
    chrome.action.setBadgeBackgroundColor({ color });

    // Store latest score for popup
    chrome.storage.session.set({ latest_score: msg.data });
  }
});

// On extension install, enable monitoring by default
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({ pulsenet_enabled: true });
  chrome.action.setBadgeText({ text: "ON" });
  chrome.action.setBadgeBackgroundColor({ color: "#34C759" });
});
