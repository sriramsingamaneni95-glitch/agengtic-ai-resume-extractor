"""Tool: normalize skill name variants to a canonical form (Point 2)."""

SKILL_MAP = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python3": "Python",
    "reactjs": "React",
    "react.js": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
}


def normalize_skill(skill: str) -> str:
    key = skill.strip().lower()
    return SKILL_MAP.get(key, skill.strip())


def normalize_skills(skills: list[str]) -> list[str]:
    seen = []
    for s in skills:
        norm = normalize_skill(s)
        if norm not in seen:
            seen.append(norm)
    return seen
