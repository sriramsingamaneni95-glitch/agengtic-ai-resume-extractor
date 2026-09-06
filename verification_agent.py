"""
Targeted Verification Agent — dynamically invoked ONLY for fields that came
back low-confidence, instead of re-running the whole pipeline. This is the
'targeted verification agent' from the review feedback.
"""
import json
from llm_client import get_client
from schema import ResumeData
from utils.retry import clean_json_text, retry_on_failure
from utils.logging_config import log_call, log_token_usage

VERIFY_PROMPT = """Focus ONLY on re-extracting these specific fields as carefully
as possible by re-reading the original resume text: {fields}
Return ONLY a JSON object containing just these field names as keys.

Original resume:
{resume_text}
"""


@log_call
@retry_on_failure(max_attempts=2)
def verify_low_confidence_fields(data: ResumeData, resume_text: str, fields: list[str]) -> ResumeData:
    if not fields:
        return data

    client = get_client()
    prompt = VERIFY_PROMPT.format(fields=fields, resume_text=resume_text)
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    log_token_usage(response, label="targeted_verification")
    corrected = json.loads(clean_json_text(response.output_text))

    updated = data.model_copy(deep=True)
    for field_name, value in corrected.items():
        if hasattr(updated, field_name):
            setattr(updated, field_name, value)
            if field_name in updated.confidence_scores.model_fields:
                setattr(updated.confidence_scores, field_name, 0.9)  # boosted post-verification
    return updated
