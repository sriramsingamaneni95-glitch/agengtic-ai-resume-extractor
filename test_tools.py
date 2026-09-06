from tools.email_validator import validate_email
from tools.date_parser import parse_date
from tools.skill_normalizer import normalize_skill, normalize_skills


def test_email_validator():
    ok, cleaned = validate_email("test@example.com")
    assert ok is True
    bad, _ = validate_email("not-an-email")
    assert bad is False


def test_date_parser():
    assert parse_date("Present") == "present"
    assert parse_date("Jan 2020") == "2020-01"


def test_skill_normalizer():
    assert normalize_skill("js") == "JavaScript"
    result = normalize_skills(["js", "JavaScript", "Python"])
    assert result.count("JavaScript") == 1
