"""
History Manager
===============
Handles saving, loading, and purging of processing history records.

Storage layout (inside project root):
  history/
    index.json              ← metadata for all records (newest first)
    2026-04-10_11-30-05_Procure360.xlsx
    …

Each index entry:
  {
    "filename":      "2026-04-10_11-30-05_Procure360.xlsx",
    "original_name": "Procure360.xlsx",
    "row_count":     1234,
    "timestamp":     "2026-04-10T11:30:05"   (ISO-8601, local time)
  }

Records older than HISTORY_DAYS are deleted automatically when
purge_old_records() is called (once per app startup).
"""

import json
import os
from datetime import datetime, timedelta

# ── Configuration ─────────────────────────────────────────────────────────────
HISTORY_DAYS = 30          # records older than this are purged
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORY_DIR   = os.path.join(_PROJECT_ROOT, "history")
INDEX_FILE    = os.path.join(HISTORY_DIR, "index.json")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _ensure_dir():
    """Create history/ directory if it doesn't exist."""
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_index() -> list:
    """Load the index file. Returns empty list if missing or corrupt."""
    if not os.path.exists(INDEX_FILE):
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_index(records: list):
    """Persist the index list to disk."""
    _ensure_dir()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


# ── Public API ────────────────────────────────────────────────────────────────

def save_to_history(excel_bytes: bytes, original_filename: str, row_count: int) -> str:
    """
    Save *excel_bytes* to the history folder and update the index.

    Parameters
    ----------
    excel_bytes       : raw bytes of the .xlsx file
    original_filename : the user-uploaded filename (e.g. "Procure360.xlsx")
    row_count         : number of data rows processed

    Returns
    -------
    The saved filename (e.g. "2026-04-10_11-30-05_Procure360.xlsx")
    """
    _ensure_dir()

    now       = datetime.now()
    ts_str    = now.strftime("%Y-%m-%d_%H-%M-%S")
    iso_ts    = now.isoformat(timespec="seconds")

    # Sanitise the stem so it's safe as a filesystem name
    stem      = os.path.splitext(original_filename)[0]
    safe_stem = "".join(c if c.isalnum() or c in "-_ " else "_" for c in stem).strip()
    safe_stem = safe_stem[:60]   # cap length

    saved_name = f"{ts_str}_{safe_stem}.xlsx"
    saved_path = os.path.join(HISTORY_DIR, saved_name)

    with open(saved_path, "wb") as f:
        f.write(excel_bytes)

    records = _load_index()
    records.insert(0, {
        "filename":      saved_name,
        "original_name": original_filename,
        "row_count":     row_count,
        "timestamp":     iso_ts,
    })
    _save_index(records)

    return saved_name


def load_history_index() -> list:
    """
    Return the full history index, newest-first.
    Each item is a dict with keys: filename, original_name, row_count, timestamp.
    """
    return _load_index()


def get_history_file_path(filename: str) -> str:
    """Absolute path to a history file by its saved filename."""
    return os.path.join(HISTORY_DIR, filename)


def purge_old_records(days: int = HISTORY_DAYS):
    """
    Delete any history records (file + index entry) older than *days* days.
    Safe to call even if history/ doesn't exist yet.
    """
    if not os.path.exists(INDEX_FILE):
        return

    cutoff  = datetime.now() - timedelta(days=days)
    records = _load_index()
    kept    = []

    for rec in records:
        try:
            ts = datetime.fromisoformat(rec["timestamp"])
        except Exception:
            kept.append(rec)   # keep malformed entries (don't silently delete)
            continue

        if ts < cutoff:
            # Delete the xlsx file
            fpath = get_history_file_path(rec["filename"])
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
            except Exception:
                pass   # best-effort deletion
        else:
            kept.append(rec)

    _save_index(kept)
