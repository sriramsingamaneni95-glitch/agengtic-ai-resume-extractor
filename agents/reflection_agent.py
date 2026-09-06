
import json
from llm_client import get_client
from schema import ResumeData
from utils.retry import clean_json_text, retry_on_failure
from utils.logging_config import log_call, log_token_usage

REFLECTION_PROMPT = """You extracted this JSON from a resume. Re-check it against
the original resume text. Fix any missing, incorrect, or misformatted fields.
Return ONLY the corrected JSON, in the same shape.

Extracted JSON:
{extracted_json}

Original resume:
{resume_text}
"""


@log_call
@retry_on_failure(max_attempts=2)
def self_reflect(data: ResumeData, resume_text: str) -> ResumeData:
    client = get_client()
    prompt = REFLECTION_PROMPT.format(
        extracted_json=data.model_dump_json(), resume_text=resume_text
    )
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    log_token_usage(response, label="reflection")
    corrected = json.loads(clean_json_text(response.output_text))
    return ResumeData(**corrected)
