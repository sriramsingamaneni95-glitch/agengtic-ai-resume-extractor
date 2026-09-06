"""Point 17: unit tests. These run offline - no OpenAI API calls."""
from schema import ResumeData, ConfidenceScores


def test_valid_resume_data():
    data = ResumeData(
        name="Sriram",
        email="sriram@example.com",
        skills=["Python", "SQL"],
    )
    assert data.name == "Sriram"
    assert "Python" in data.skills


def test_confidence_low_field_detection():
    scores = ConfidenceScores(name=0.9, email=0.4, phone=0.95, skills=0.8,
                               experience=0.9, education=0.9)
    low = scores.low_confidence_fields(threshold=0.7)
    assert "email" in low
    assert "name" not in low
