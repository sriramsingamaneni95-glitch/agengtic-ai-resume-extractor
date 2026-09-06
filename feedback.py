"""
Human feedback loop: when a human corrects a low-confidence field, persist
the correction AND teach the knowledge base immediately, so future runs on
similar resumes/entities benefit from it (agent memory actually updates).
"""
import json
from pathlib import Path
from knowledge_base import teach_entity

FEEDBACK_FILE = Path("human_feedback.json")


def record_correction(resume_name: str, field: str, old_value, corrected_value):
    feedback = []
    if FEEDBACK_FILE.exists():
        feedback = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    feedback.append({
        "resume_name": resume_name,
        "field": field,
        "old_value": old_value,
        "corrected_value": corrected_value,
    })
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2, ensure_ascii=False), encoding="utf-8")

    # Immediately teach the knowledge base for company/institution corrections
    if field == "company":
        teach_entity(corrected_value, "company")
    if field == "institution":
        teach_entity(corrected_value, "university")
