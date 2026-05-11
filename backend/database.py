"""PulseNet Database Layer — SQLite"""
import sqlite3, os, json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "pulsenet.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'User',
    email TEXT DEFAULT '',
    avatar_color TEXT DEFAULT '#00D4FF',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    score INTEGER NOT NULL,
    category TEXT NOT NULL,
    sentiment TEXT,
    keywords_json TEXT,
    crisis_detected INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS guardians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    threshold INTEGER DEFAULT 70,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guardian_id INTEGER,
    post_id INTEGER,
    message TEXT,
    channel TEXT DEFAULT 'email',
    status TEXT DEFAULT 'simulated',
    triggered_score INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(guardian_id) REFERENCES guardians(id),
    FOREIGN KEY(post_id) REFERENCES posts(id)
);
"""

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM user_profile")
    if cur.fetchone()["cnt"] == 0:
        cur.execute("INSERT INTO user_profile (name, email) VALUES ('User', '')")
    conn.commit()
    conn.close()

# ── Auth helpers ──────────────────────────────────────────────────────────────────
def create_user(username, email, password_hash):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        uid = cur.lastrowid
        conn.commit()
        return uid, None
    except Exception as e:
        if "UNIQUE" in str(e):
            if "email" in str(e):
                return None, "Email already registered"
            return None, "Username already taken"
        return None, str(e)
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(uid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (uid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_post(text, score, category, sentiment, keywords_json, source="manual"):
    crisis = 1 if score >= 81 else 0
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (text,source,score,category,sentiment,keywords_json,crisis_detected) VALUES (?,?,?,?,?,?,?)",
        (text, source, score, category, sentiment, json.dumps(keywords_json), crisis)
    )
    post_id = cur.lastrowid
    conn.commit(); conn.close()
    return post_id

def get_dashboard_data():
    conn = get_connection()
    cur = conn.cursor()
    days = []
    for i in range(6, -1, -1):
        d = datetime.utcnow() - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        label = d.strftime("%a")
        cur.execute("SELECT AVG(score) as avg_score, COUNT(*) as cnt FROM posts WHERE DATE(created_at)=?", (date_str,))
        row = cur.fetchone()
        days.append({"date": date_str, "label": label, "avg_score": round(row["avg_score"] or 0, 1), "post_count": row["cnt"]})

    cur.execute("SELECT AVG(score) as avg, MAX(score) as peak, COUNT(*) as total FROM posts")
    stats = cur.fetchone()
    cur.execute("SELECT score, category FROM posts ORDER BY created_at DESC LIMIT 1")
    latest = cur.fetchone()
    cur.execute("SELECT id,text,score,category,sentiment,crisis_detected,created_at FROM posts ORDER BY created_at DESC LIMIT 10")
    recent = [dict(r) for r in cur.fetchall()]
    conn.close()

    rolling_avg = round(sum(d["avg_score"] for d in days) / 7, 1)
    return {
        "seven_day": days,
        "rolling_avg": rolling_avg,
        "peak_score": stats["peak"] or 0,
        "total_posts": stats["total"] or 0,
        "current_score": latest["score"] if latest else 0,
        "current_category": latest["category"] if latest else "Healthy",
        "recent_posts": recent,
    }

def get_guardians():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM guardians WHERE active=1")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def save_guardian(name, email, phone, threshold):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO guardians (name,email,phone,threshold) VALUES (?,?,?,?)", (name,email,phone,threshold))
    gid = cur.lastrowid; conn.commit(); conn.close(); return gid

def delete_guardian(gid):
    conn = get_connection()
    conn.execute("UPDATE guardians SET active=0 WHERE id=?", (gid,))
    conn.commit(); conn.close()

def save_alert(guardian_id, post_id, message, channel, triggered_score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (guardian_id,post_id,message,channel,triggered_score,status) VALUES (?,?,?,?,?,?)",
        (guardian_id, post_id, message, channel, triggered_score, "simulated")
    )
    aid = cur.lastrowid; conn.commit(); conn.close(); return aid

def get_alerts(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id,a.message,a.channel,a.status,a.triggered_score,a.created_at,
               g.name as guardian_name, g.email as guardian_email
        FROM alerts a LEFT JOIN guardians g ON a.guardian_id=g.id
        ORDER BY a.created_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def get_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profile LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {"name": "User", "email": ""}

def update_profile(name, email):
    conn = get_connection()
    conn.execute("UPDATE user_profile SET name=?,email=? WHERE id=1", (name, email))
    conn.commit(); conn.close()

def seed_demo_data():
    """Insert demo posts spread over 7 days."""
    import model as m
    demo = [
        ("Feeling really down today, everything seems hopeless", 6),
        ("Had an amazing day with friends! Feeling so blessed 🙏", 5),
        ("Can't stop crying, nobody understands me anymore", 5),
        ("Just finished my project, so proud of myself!", 4),
        ("I feel so alone, like nobody cares about me", 4),
        ("Grateful for all the support from my family today", 3),
        ("Everything is falling apart, I don't know what to do", 3),
        ("Watched a beautiful sunset, feeling at peace", 2),
        ("Been struggling with anxiety a lot lately, overwhelming", 2),
        ("Had a great workout, feeling energized and happy!", 1),
        ("I hate myself, I'm such a burden to everyone", 1),
        ("Starting therapy next week, feeling hopeful 💙", 0),
        ("Can't sleep again, dark thoughts won't stop", 0),
    ]
    conn = get_connection()
    for text, days_ago in demo:
        result = m.score_text(text)
        ts = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO posts (text,source,score,category,sentiment,keywords_json,crisis_detected,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (text,"demo",result["score"],result["category"],result["sentiment"],
             json.dumps(result["keywords_found"]),1 if result["crisis_detected"] else 0, ts)
        )
    conn.commit(); conn.close()
