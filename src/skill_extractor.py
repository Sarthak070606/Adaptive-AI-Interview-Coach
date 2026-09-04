"""Simple skill extractor from resume text – only common skills."""

# Keep only practical / commonly known skills
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "C++", "C#", "SQL",
    "Machine Learning", "Deep Learning", "Data Analysis",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
    "HTML", "CSS", "React", "Node.js", "Django", "Flask", "FastAPI",
    "Git", "Docker", "Linux", "AWS", "Azure",
    "MongoDB", "PostgreSQL", "MySQL",
    "Data Structures", "Algorithms", "System Design",
    "NLP", "Computer Vision", "Excel"
]

def extract_skills(text: str) -> list:
    """Return list of skills found in the text (case-insensitive)."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        # Simple whole-word style match
        if skill.lower() in text_lower:
            found.append(skill)
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for s in found:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique
