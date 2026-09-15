from openai_service import generate_text


QUESTION_PROMPTS = {
    "short_answer": "short-answer questions",
    "essay": "essay questions with scoring guidance",
    "true_false": "true-or-false questions with explanations",
    "matching": "matching questions",
    "Short Answer Questions": "short-answer questions",
    "Fill in the Blanks": "fill-in-the-blank questions",
    "Matching": "matching questions",
    "multiple_choice": "multiple-choice questions with four options each",
}


def generate_worksheet(topic, num_questions, question_type, formatting_delimiter="----", *, grade_level=5):
    topic = str(topic).strip()
    if not topic:
        raise ValueError("A worksheet topic is required.")

    num_questions = int(num_questions)
    if not 1 <= num_questions <= 50:
        raise ValueError("Number of questions must be between 1 and 50.")

    if not 0 <= int(grade_level) <= 12:
        raise ValueError("Grade must be between 0 and 12.")
    delimiter = formatting_delimiter or "----"
    if question_type == "Mix":
        question_instruction = (
            "Use a balanced mix of short-answer, fill-in-the-blank, and matching questions."
        )
    elif question_type in QUESTION_PROMPTS:
        question_instruction = f"Use {QUESTION_PROMPTS[question_type]}."
    else:
        raise ValueError(f"Invalid question type: {question_type}")

    prompt = f"""
Create a classroom-ready worksheet about {topic} with exactly {num_questions} questions for grade {grade_level} (0 means kindergarten).
This is an unverified teacher draft. Do not invent citations. Flag uncertain facts for review.
{question_instruction}
List all questions first, followed by a section titled exactly "Answers:" containing the answer key.
Place this delimiter between items: {delimiter}
Do not include commentary before or after the worksheet.
""".strip()

    return generate_text(
        [
            {"role": "system", "content": "You create accurate, age-appropriate classroom worksheets."},
            {"role": "user", "content": prompt},
        ]
    )
