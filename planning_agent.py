"""
Planning Agent (Point 1): decides the extraction strategy before acting,
instead of jumping straight into a single prompt.
"""
from llm_client import get_client
from utils.logging_config import logger, log_call

PLANNING_PROMPT = """You are a planning agent for a resume-processing pipeline.
Given the raw resume text below, output a short JSON plan with these fields:
- "is_scanned_or_messy": true/false (does text look OCR-garbled or poorly formatted?)
- "has_multiple_pages": true/false
- "language": detected language of the resume
- "notes": any special handling needed (e.g. "dates in DD/MM/YYYY", "non-English section")

Return ONLY valid JSON, nothing else.

Resume text:
{resume_text}
"""


@log_call
def plan_extraction(resume_text: str) -> dict:
    client = get_client()
    response = client.responses.create(
        model="gpt-4.1",
        input=PLANNING_PROMPT.format(resume_text=resume_text[:3000]),
        text={"format": {"type": "json_object"}},
    )
    import json
    try:
        return json.loads(response.output_text.strip())
    except json.JSONDecodeError:
        logger.warning("Planning agent returned invalid JSON, using default plan.")
        return {"is_scanned_or_messy": False, "has_multiple_pages": False,
                "language": "unknown", "notes": ""}
