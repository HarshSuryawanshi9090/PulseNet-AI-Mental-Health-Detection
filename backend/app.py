"""PulseNet Flask API — with session-based authentication"""
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sys, os, json

BACKEND_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BACKEND_DIR, "..", "frontend"))

sys.path.insert(0, BACKEND_DIR)
import model, database, guardian as guardian_module

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/app")
app.secret_key = os.getenv("PULSENET_SECRET", "pulsenet-dev-secret-change-in-prod")
CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000"])
database.init_db()


# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required", "redirect": "/login"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Serve frontend files ──────────────────────────────────────────────────────
@app.route("/")
def root():
    if "user_id" not in session:
        return send_from_directory(FRONTEND_DIR, "login.html")
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/login")
def serve_login():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/dashboard")
def serve_dashboard():
    if "user_id" not in session:
        return send_from_directory(FRONTEND_DIR, "login.html")
    return send_from_directory(FRONTEND_DIR, "dashboard.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    pw_hash = generate_password_hash(password)
    uid, err = database.create_user(username, email, pw_hash)
    if err:
        return jsonify({"error": err}), 409

    session["user_id"] = uid
    session["username"] = username
    return jsonify({"success": True, "user": {"id": uid, "username": username, "email": email}}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = database.get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({
        "success": True,
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]}
    })


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/me")
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401
    user = database.get_user_by_id(uid)
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 401
    return jsonify(user)


# ── Health (public) ───────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "PulseNet API", "version": "1.0.0"})


# ── Protected API routes ──────────────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
@login_required
def analyze():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(model.score_text(text))


@app.route("/api/posts", methods=["POST"])
@login_required
def save_post():
    data = request.get_json(force=True)
    text   = data.get("text", "").strip()
    source = data.get("source", "manual")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    result  = model.score_text(text)
    post_id = database.save_post(text, result["score"], result["category"],
                                 result["sentiment"], result["keywords_found"], source)
    alerts  = guardian_module.check_and_alert(post_id, result["score"], result["category"], text)
    return jsonify({"post_id": post_id, "analysis": result, "alerts_triggered": len(alerts), "alerts": alerts})


@app.route("/api/dashboard")
@login_required
def dashboard():
    return jsonify(database.get_dashboard_data())


@app.route("/api/guardians", methods=["GET"])
@login_required
def get_guardians():
    return jsonify(database.get_guardians())


@app.route("/api/guardians", methods=["POST"])
@login_required
def add_guardian():
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    gid = database.save_guardian(name, data.get("email",""), data.get("phone",""),
                                 int(data.get("threshold", 70)))
    return jsonify({"success": True, "guardian_id": gid}), 201


@app.route("/api/guardians/<int:gid>", methods=["DELETE"])
@login_required
def remove_guardian(gid):
    database.delete_guardian(gid)
    return jsonify({"success": True})


@app.route("/api/alerts")
@login_required
def get_alerts():
    return jsonify(database.get_alerts())


@app.route("/api/test-alert", methods=["POST"])
@login_required
def test_alert():
    data = request.get_json(force=True)
    gid  = data.get("guardian_id")
    if not gid:
        return jsonify({"error": "guardian_id required"}), 400
    return jsonify(guardian_module.send_test_alert(int(gid), data.get("score", 75)))


@app.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify(database.get_profile())


@app.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json(force=True)
    database.update_profile(data.get("name", "User"), data.get("email", ""))
    return jsonify({"success": True})


@app.route("/api/seed", methods=["POST"])
@login_required
def seed():
    database.seed_demo_data()
    return jsonify({"success": True, "message": "Demo data seeded"})


if __name__ == "__main__":
    print("PulseNet API starting on http://localhost:5000")
    app.run(debug=True, port=5000)
