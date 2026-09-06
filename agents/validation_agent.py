
from schema import ResumeData
from tools.email_validator import validate_email
from knowledge_base import verify_entity
from utils.logging_config import logger, log_call


@log_call
def validate_resume(data: ResumeData) -> ResumeData:
    is_valid, cleaned_email = validate_email(data.email)
    if not is_valid:
        logger.warning(f"Email failed validation: {data.email}")
        data.confidence_scores.email = min(data.confidence_scores.email, 0.3)
    data.email = cleaned_email or data.email

    verified = {}
    for exp in data.experience:
        verified[exp.company] = verify_entity(exp.company, "company")
    for edu in data.education:
        verified[edu.institution] = verify_entity(edu.institution, "university")
    data.verified_entities = verified

    return data


def needs_human_review(data: ResumeData, threshold: float = 0.7) -> list[str]:
    """Point 7: human-in-the-loop trigger."""
    return data.confidence_scores.low_confidence_fields(threshold)
