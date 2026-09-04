def get_next_difficulty(score):
    if score >= 80:
        return "hard"
    elif score >= 60:
        return "medium"
    else:
        return "easy"
