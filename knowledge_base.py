
import difflib
import json
from pathlib import Path

KB_FILE = Path("knowledge_base_store.json")

DEFAULT_KB = {
    "companies": ["Google", "Microsoft", "Amazon", "Nvidia", "Infosys", "Wipro", "Accenture"],
    "universities": ["IIT Bombay", "IIT Delhi", "JNTU Hyderabad", "Osmania University", "SRM University"],
}


def _load_kb() -> dict:
    if KB_FILE.exists():
        return json.loads(KB_FILE.read_text(encoding="utf-8"))
    KB_FILE.write_text(json.dumps(DEFAULT_KB, indent=2), encoding="utf-8")
    return json.loads(json.dumps(DEFAULT_KB))


def _save_kb(kb: dict):
    KB_FILE.write_text(json.dumps(kb, indent=2), encoding="utf-8")


def verify_entity(name: str, kind: str) -> dict:
    kb = _load_kb()
    pool = kb["companies"] if kind == "company" else kb["universities"]
    matches = difflib.get_close_matches(name, pool, n=1, cutoff=0.75)
    if matches:
        return {"verified": True, "matched_to": matches[0]}
    return {"verified": False, "matched_to": None}


def teach_entity(name: str, kind: str):
    kb = _load_kb()
    key = "companies" if kind == "company" else "universities"
    if name and name not in kb[key]:
        kb[key].append(name)
        _save_kb(kb)
