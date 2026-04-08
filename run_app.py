"""
Launcher for Company Name Normalizer (PyInstaller entry point)
"""
import os
import sys
import threading
import time


def get_meipass():
    """Return the PyInstaller temp extraction path, or the script directory."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_exe_dir():
    """Return the folder containing the .exe (or the script folder in dev mode)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_browser_when_ready(url: str, tries: int = 60, interval: float = 1.0):
    """Poll Streamlit health endpoint, then open browser reliably on Windows."""
    import urllib.request
    health = url.rstrip("/") + "/_stcore/health"
    for _ in range(tries):
        try:
            urllib.request.urlopen(health, timeout=2)
            # os.startfile is the most reliable way to open a URL on Windows
            if sys.platform == "win32":
                os.startfile(url)
            else:
                import webbrowser
                webbrowser.open(url)
            return
        except Exception:
            time.sleep(interval)


if __name__ == "__main__":
    base_path = get_meipass()
    exe_dir = get_exe_dir()

    # Ensure company_normalizer (and app.py) are importable
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    # Load .env from the folder containing the .exe (user-editable)
    env_file = os.path.join(exe_dir, ".env")
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)

    # Streamlit environment tweaks
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")

    # Open browser once Streamlit is ready
    threading.Thread(
        target=open_browser_when_ready,
        args=("http://localhost:8501",),
        daemon=True,
    ).start()

    # Launch Streamlit
    import streamlit.web.cli as stcli

    app_path = os.path.join(base_path, "app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.headless=true",
    ]
    sys.exit(stcli.main())
