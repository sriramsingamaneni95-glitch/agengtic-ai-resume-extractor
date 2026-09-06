"""
Memory module (Point 9): stores each run's output and diffs it against
the previous version for the same resume file.
"""
import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("resume_history.json")


def _load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_version(resume_name: str, data: dict) -> dict | None:
    """Saves a new version and returns a diff against the previous one (or None)."""
    history = _load_history()
    previous = next(
        (h for h in reversed(history) if h["resume_name"] == resume_name), None
    )

    entry = {
        "resume_name": resume_name,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

    if previous is None:
        return None
    return _diff(previous["data"], data)


def _diff(old: dict, new: dict) -> dict:
    changes = {}
    keys = set(old.keys()) | set(new.keys())
    for k in keys:
        if old.get(k) != new.get(k):
            changes[k] = {"old": old.get(k), "new": new.get(k)}
    return changes
