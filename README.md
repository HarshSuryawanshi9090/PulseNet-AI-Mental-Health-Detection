# 🧠 PulseNet — AI Mental Health Early Warning System

> **Consent-based AI that detects emotional distress in social media posts before it becomes a crisis.**

---

## 🚀 Quick Start

```bash
# 1. Clone / navigate to project
cd PulseNet-AI-Mental-Health-Detection

# 2. One-click launch (installs deps + starts API + opens dashboard)
python run.py
```

That's it! The dashboard opens automatically at `frontend/dashboard.html`.

---

## 📦 Project Structure

```
PulseNet-AI-Mental-Health-Detection/
├── backend/
│   ├── app.py          # Flask REST API
│   ├── model.py        # NLP distress scorer (0-100)
│   ├── database.py     # SQLite ORM
│   ├── guardian.py     # Alert notification system
│   ├── requirements.txt
│   └── pulsenet.db     # Auto-created SQLite DB
├── frontend/
│   ├── index.html      # Landing page
│   ├── dashboard.html  # Wellness dashboard
│   ├── style.css       # Dark-mode design system
│   └── dashboard.js    # Charts + API integration
├── extension/
│   ├── manifest.json   # Chrome Extension Manifest V3
│   ├── content.js      # Social media post scraper
│   ├── popup.html      # Extension popup UI
│   ├── popup.js        # Popup logic
│   └── background.js   # Service worker
└── run.py              # One-click launcher
```

---

## 🔌 Chrome Extension Setup

1. Open Chrome → `chrome://extensions`
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder
4. Extension is active! Visit Twitter/X or Instagram to see it in action.

> **Note**: The backend must be running (`python run.py`) for the extension to send scores.

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/health` | API health check |
| POST   | `/api/analyze` | Analyze text (no save) |
| POST   | `/api/posts` | Analyze + save post |
| GET    | `/api/dashboard` | 7-day dashboard data |
| GET    | `/api/guardians` | List guardians |
| POST   | `/api/guardians` | Add guardian |
| DELETE | `/api/guardians/<id>` | Remove guardian |
| GET    | `/api/alerts` | Alert history |
| POST   | `/api/test-alert` | Send test alert |
| POST   | `/api/seed` | Load demo data |

---

## 🧠 Distress Score Scale

| Score | Category | Meaning |
|-------|----------|---------|
| 0–20 | 😊 Healthy | No significant distress detected |
| 21–40 | 😕 Mild Distress | Minor emotional difficulty |
| 41–60 | 😟 Moderate | Noticeable distress, monitor closely |
| 61–80 | 😰 High Risk | Significant distress — check in |
| 81–100 | 🆘 Crisis | Immediate intervention needed |

---

## 📧 Real Guardian Alerts (Optional)

Set environment variables to enable real email alerts:

```bash
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your@gmail.com
set SMTP_PASS=your-app-password
```

> Without SMTP config, alerts are still logged in the dashboard (simulated mode).

---

## 🌱 Load Demo Data

Click **"🌱 Load Demo Data"** in the dashboard to populate 14 sample posts spanning 7 days — great for showcasing the trend chart.

---

## ☎️ Crisis Helplines (India)

- **iCall**: 9152987821
- **AASRA**: 9820466627
- **Vandrevala Foundation**: 1860-2662-345
- **NIMHANS**: 080-46110007

---

## 🔮 Upgrade to Real BERT

To swap the rule-based NLP with a real BERT model:
1. Replace `backend/model.py`'s `score_text()` function
2. Keep the same return dict format
3. Everything else (API, dashboard, extension) works unchanged

---

*Built with ❤️ for India — because early intervention saves lives.*
