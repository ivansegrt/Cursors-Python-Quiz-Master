import random
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass(frozen=True)
class Question:
	question_text: str
	options: List[str]
	correct_option_key: str  # one of: "a", "b", "c", "d"
	explanation: str


LETTER_KEYS: Tuple[str, ...] = ("a", "b", "c", "d")


def build_questions() -> List[Question]:
	return [
		Question(
			question_text="What is the correct file extension for Python files?",
			options=[".pyt", ".pt", ".py", ".python"],
			correct_option_key="c",
			explanation=".py is the standard extension for Python source files.",
		),
		Question(
			question_text="Which keyword is used to define a function in Python?",
			options=["func", "def", "function", "define"],
			correct_option_key="b",
			explanation="Functions in Python are defined using the 'def' keyword.",
		),
		Question(
			question_text="How do you write a comment in Python?",
			options=["// comment", "<!-- comment -->", "/* comment */", "# comment"],
			correct_option_key="d",
			explanation="Python uses the hash symbol (#) for single-line comments.",
		),
		Question(
			question_text="What is the output type of input() in Python 3?",
			options=["int", "str", "float", "bool"],
			correct_option_key="b",
			explanation="input() returns a string. Convert it if you need another type.",
		),
		Question(
			question_text="Which of the following is a valid list in Python?",
			options=["{1, 2, 3}", "(1, 2, 3)", "[1, 2, 3]", "<1, 2, 3>"],
			correct_option_key="c",
			explanation="Lists use square brackets, e.g., [1, 2, 3].",
		),
	]


def print_greeting() -> None:
	print("Welcome to the Python Quiz Chatbot!")
	print("Answer by typing a, b, c, or d. Type 'q' at any time to quit.")
	print("Type 's' to skip a question. Good luck!\n")


def format_question(q: Question) -> str:
	lines: List[str] = [q.question_text]
	for idx, option in enumerate(q.options):
		lines.append(f"  {LETTER_KEYS[idx]}) {option}")
	return "\n".join(lines)


def ask_for_choice(prompt_text: str) -> str:
	while True:
		raw = input(prompt_text).strip().lower()
		if raw in ("q", "s") or raw in LETTER_KEYS:
			return raw
		print("Please enter a valid choice: a, b, c, d, 's' to skip, or 'q' to quit.")


def run_quiz_loop() -> None:
	questions = build_questions()
	score: int = 0
	total_answered: int = 0
	print_greeting()

	# Cycle through questions indefinitely; reshuffle each round
	while True:
		shuffled = questions[:]
		random.shuffle(shuffled)

		for q in shuffled:
			print(format_question(q))
			choice = ask_for_choice("Your choice (a/b/c/d, 's' skip, 'q' quit): ")

			if choice == "q":
				print(f"\nExiting quiz. You answered {total_answered} question(s) with {score} correct.")
				return

			if choice == "s":
				print("Skipped.\n")
				continue

			total_answered += 1
			if choice == q.correct_option_key:
				score += 1
				print("Correct! 🎉")
			else:
				correct_idx = LETTER_KEYS.index(q.correct_option_key)
				correct_text = q.options[correct_idx]
				print(f"Incorrect. The correct answer is '{q.correct_option_key}) {correct_text}'.")
			print(f"Explanation: {q.explanation}")
			print(f"Score: {score}/{total_answered}\n")


if __name__ == "__main__":
	run_quiz_loop()

