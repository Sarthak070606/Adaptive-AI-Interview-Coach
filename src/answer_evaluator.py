"""Answer evaluator using Groq LLM."""
import json
import re
from src.llm_client import chat


def evaluate_answer(question: str, answer: str, skill: str) -> dict:
    """
    Evaluate a candidate's answer and return structured scores.
    Returns dict with technical, relevance, completeness, communication, overall, feedback.
    """
    system = (
        "You are a strict but fair technical interviewer. "
        "Evaluate the candidate's answer honestly. "
        "Return ONLY valid JSON, no markdown, no extra text."
    )

    prompt = f"""
Evaluate this interview answer.

Skill: {skill}
Question: {question}
Candidate Answer: {answer}

Score each category from 0 to 100:
- technical: technical correctness and depth
- relevance: how well it answers the question
- completeness: covers important points
- communication: clarity and structure

Also give:
- overall: weighted average (technical 40%, relevance 25%, completeness 20%, communication 15%)
- feedback: 2-3 short sentences of constructive feedback
- strengths: list of 1-3 short strengths
- improvements: list of 1-3 short improvement points

Return JSON in this exact format:
{{
  "technical": 75,
  "relevance": 80,
  "completeness": 70,
  "communication": 85,
  "overall": 76,
  "feedback": "...",
  "strengths": ["...", "..."],
  "improvements": ["...", "..."]
}}
"""

    try:
        raw = chat(prompt, system=system)
        # Extract JSON even if model wraps it
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(raw)

        # Ensure all keys exist with safe defaults
        result = {
            "technical": int(data.get("technical", 50)),
            "relevance": int(data.get("relevance", 50)),
            "completeness": int(data.get("completeness", 50)),
            "communication": int(data.get("communication", 50)),
            "overall": int(data.get("overall", 50)),
            "feedback": data.get("feedback", "No detailed feedback available."),
            "strengths": data.get("strengths", []),
            "improvements": data.get("improvements", []),
        }
        # Recompute overall if missing/wrong
        result["overall"] = int(
            result["technical"] * 0.40
            + result["relevance"] * 0.25
            + result["completeness"] * 0.20
            + result["communication"] * 0.15
        )
        return result
    except Exception as e:
        print(f"Evaluation failed: {e}")
        # Fallback simple score
        word_count = len(answer.split())
        rough = min(90, max(25, word_count * 4))
        return {
            "technical": rough,
            "relevance": rough,
            "completeness": max(20, rough - 10),
            "communication": rough,
            "overall": rough,
            "feedback": "Could not get detailed AI evaluation. Score is approximate based on answer length.",
            "strengths": [],
            "improvements": ["Provide more technical detail next time."],
        }
