from src.question_generator import generate_question
from src.difficulty_manager import get_next_difficulty

print("=== Testing Question Generator ===")
question = generate_question("Python", "easy")
print(question)

print("\n=== Testing Difficulty Manager ===")
print(get_next_difficulty(90))
print(get_next_difficulty(70))
print(get_next_difficulty(40))
