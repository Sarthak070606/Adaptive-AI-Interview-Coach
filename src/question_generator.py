"""Question generator – real-time via Groq LLM + static bank fallback."""
import json
import random
from pathlib import Path
from src.llm_client import chat


def load_questions():
    project_root = Path(__file__).resolve().parent.parent
    question_file = project_root / "data" / "question_bank.json"
    with open(question_file, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_question_llm(skill: str, difficulty: str, role: str = "Software Engineer", level: str = "Intermediate") -> dict:
    """Generate a fresh interview question using Groq."""
    system = (
        "You are an expert technical interviewer. "
        "Generate clear, practical interview questions. "
        "Return ONLY the question text. No numbering, no extra explanation."
    )
    prompt = (
        f"Generate one {difficulty} level interview question "
        f"for the skill '{skill}' for a {level} {role} candidate. "
        f"The question should test real understanding, not just definition."
    )
    try:
        question_text = chat(prompt, system=system)
        # Clean up if model adds quotes or prefixes
        question_text = question_text.strip().strip('"').strip("'")
        if question_text.lower().startswith("question:"):
            question_text = question_text[9:].strip()
        return {
            "question": question_text,
            "skill": skill,
            "difficulty": difficulty,
            "source": "llm"
        }
    except Exception as e:
        print(f"LLM question generation failed: {e}")
        return None


def generate_question_bank(skill: str, difficulty: str, exclude_questions=None) -> dict:
    """Fallback: pick from static question bank."""
    if exclude_questions is None:
        exclude_questions = []

    questions = load_questions()
    filtered = [
        q for q in questions
        if q["skill"].lower() == skill.lower()
        and q["difficulty"].lower() == difficulty.lower()
        and q["question"] not in exclude_questions
    ]
    if not filtered:
        filtered = [
            q for q in questions
            if q["skill"].lower() == skill.lower()
            and q["question"] not in exclude_questions
        ]
    if not filtered:
        return None
    q = random.choice(filtered)
    q["source"] = "bank"
    return q


def generate_question(skill: str, difficulty: str, role: str = "Software Engineer",
                      level: str = "Intermediate", exclude_questions=None, use_llm: bool = True) -> dict:
    """Main entry point. Prefer LLM, fall back to bank."""
    if use_llm:
        q = generate_question_llm(skill, difficulty, role, level)
        if q and q["question"]:
            return q
    return generate_question_bank(skill, difficulty, exclude_questions)
