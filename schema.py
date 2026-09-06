"""
Pydantic schema for guaranteed structured output (Point 5: JSON Schema validation).
Also carries confidence scores (Point 6) and resume intelligence fields (Point 13).
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class Experience(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    institution: str
    degree: str
    year: Optional[str] = None


class ConfidenceScores(BaseModel):
    name: float = 1.0
    email: float = 1.0
    phone: float = 1.0
    skills: float = 1.0
    experience: float = 1.0
    education: float = 1.0

    def low_confidence_fields(self, threshold: float = 0.7) -> List[str]:
        return [f for f, v in self.model_dump().items() if v < threshold]


class ResumeIntelligence(BaseModel):
    total_experience_years: Optional[float] = None
    seniority_level: Optional[str] = None          # Junior / Mid / Senior / Lead
    leadership_indicators: List[str] = Field(default_factory=list)
    career_progression_summary: Optional[str] = None
    skill_categories: dict = Field(default_factory=dict)  # e.g. {"languages": [...], "tools": [...]}


class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores)
    intelligence: Optional[ResumeIntelligence] = None
    verified_entities: dict = Field(default_factory=dict)   # filled by RAG/knowledge base agent


class MatchResult(BaseModel):
    fit_score: float
    reasoning: str
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)


class ATSResult(BaseModel):
    ats_score: float
    missing_keywords: List[str] = Field(default_factory=list)
