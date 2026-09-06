"""
Scoring Agent (Points 12, 13): ATS score + resume intelligence
(experience years, seniority, leadership signals, career progression).

Both functions here are DETERMINISTIC (regex/date math, keyword overlap) -
no OpenAI call is made. This is a deliberate design choice: cheaper, faster,
and fully reproducible/testable without hitting the API. See README ->
"Design decisions" for the trade-off this implies.
"""
import re
from datetime import datetime

from schema import ResumeData, ResumeIntelligence, ATSResult
from utils.logging_config import log_call

LEADERSHIP_KEYWORDS = ["led", "managed", "mentored", "supervised", "directed", "founded", "head of"]


def _years_between(start: str, end: str) -> float:
    def to_dt(s):
        if not s or s == "present":
            return datetime.now()
        try:
            return datetime.strptime(s, "%Y-%m")
        except ValueError:
            return None
    d1, d2 = to_dt(start), to_dt(end)
    if not d1 or not d2:
        return 0.0
    return max(0.0, (d2 - d1).days / 365.25)


@log_call
def compute_resume_intelligence(data: ResumeData) -> ResumeIntelligence:
    total_years = sum(_years_between(e.start_date, e.end_date) for e in data.experience)

    leadership_hits = []
    for exp in data.experience:
        desc = (exp.description or "").lower()
        for kw in LEADERSHIP_KEYWORDS:
            if kw in desc and kw not in leadership_hits:
                leadership_hits.append(kw)

    if total_years < 2:
        seniority = "Junior"
    elif total_years < 5:
        seniority = "Mid-level"
    elif total_years < 9:
        seniority = "Senior"
    else:
        seniority = "Lead/Principal"

    titles = [e.title for e in data.experience]
    progression = " -> ".join(titles) if titles else "No experience listed"

    return ResumeIntelligence(
        total_experience_years=round(total_years, 1),
        seniority_level=seniority,
        leadership_indicators=leadership_hits,
        career_progression_summary=progression,
    )


@log_call
def compute_ats_score(resume_text: str, jd_text: str) -> ATSResult:
    """Simple deterministic keyword-overlap ATS score - no LLM call needed."""
    def keywords(text):
        words = re.findall(r"[A-Za-z][A-Za-z\+\#\.]{1,}", text.lower())
        stop = {"the", "and", "with", "for", "a", "an", "to", "of", "in", "on"}
        return set(w for w in words if w not in stop and len(w) > 2)

    jd_kw = keywords(jd_text)
    resume_kw = keywords(resume_text)
    matched = jd_kw & resume_kw
    missing = jd_kw - resume_kw

    score = round(100 * len(matched) / max(1, len(jd_kw)), 1)
    return ATSResult(ats_score=score, missing_keywords=sorted(missing)[:20])
