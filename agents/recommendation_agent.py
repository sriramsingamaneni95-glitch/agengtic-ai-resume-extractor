
import json
from llm_client import get_client
from schema import ResumeData, MatchResult
from utils.retry import clean_json_text, retry_on_failure
from utils.logging_config import log_call, log_token_usage

MATCH_PROMPT = """Compare this candidate's resume data to the job description.
Return ONLY JSON: {{"fit_score": 0-100, "reasoning": str,
"matching_skills": [str], "missing_skills": [str]}}

Resume data:
{resume_json}

Job description:
{jd_text}
"""


@log_call
@retry_on_failure(max_attempts=3)
def match_resume_to_jd(resume: ResumeData, jd_text: str) -> MatchResult:
    client = get_client()
    prompt = MATCH_PROMPT.format(resume_json=resume.model_dump_json(), jd_text=jd_text)
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    log_token_usage(response, label="matching")
    data = json.loads(clean_json_text(response.output_text))
    return MatchResult(**data)
