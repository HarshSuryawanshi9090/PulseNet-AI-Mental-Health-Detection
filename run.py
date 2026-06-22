"""
PulseNet — One-Click Launcher
Run: python run.py
"""
import subprocess, sys, os, time, webbrowser

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

def install_deps():
    req = os.path.join(BACKEND_DIR, "requirements.txt")
    print("[info] Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req, "-q"], check=True)
    print("[ok] Dependencies ready")

def start_server():
    print("[info] Starting PulseNet API on http://localhost:5000 ...")
    return subprocess.Popen(
        [sys.executable, os.path.join(BACKEND_DIR, "app.py")],
        cwd=BACKEND_DIR,
    )

if __name__ == "__main__":
    print("=" * 50)
    print("  [PulseNet] Mental Health Monitor")
    print("=" * 50)
    install_deps()
    proc = start_server()
    print("[info] Waiting for server to start...")
    time.sleep(2)
    dashboard = os.path.abspath(os.path.join(FRONTEND_DIR, "dashboard.html"))
    print(f"[info] Opening dashboard: {dashboard}")
    webbrowser.open(f"file:///{dashboard}")
    print("\n[ok] PulseNet is running!")
    print("   API:       http://localhost:5000")
    print("   Dashboard: Open frontend/dashboard.html in browser")
    print("   Press Ctrl+C to stop\n")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n👋 Shutting down PulseNet...")
        proc.terminate()
