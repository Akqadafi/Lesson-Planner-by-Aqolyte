import json
from openai_service import generate_text


class WorksheetFormatError(ValueError):
    pass


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
    if not topic or len(topic) > 300:
        raise ValueError("Enter a worksheet topic of 1-300 characters.")

    num_questions = int(num_questions)
    if not 1 <= num_questions <= 50:
        raise ValueError("Number of questions must be between 1 and 50.")

    if not 0 <= int(grade_level) <= 12:
        raise ValueError("Grade must be between 0 and 12.")
    delimiter = formatting_delimiter or "----"
    if not isinstance(delimiter, str) or len(delimiter) > 20 or "\n" in delimiter or "\r" in delimiter:
        raise ValueError("Use a single-line delimiter of at most 20 characters.")
    if question_type == "Mix":
        question_instruction = (
            "Use a balanced mix of short-answer, fill-in-the-blank, and matching questions."
        )
    elif question_type in QUESTION_PROMPTS:
        question_instruction = f"Use {QUESTION_PROMPTS[question_type]}."
    else:
        raise ValueError(f"Invalid question type: {question_type}")

    prompt = f"""
Create a worksheet draft about {topic} with exactly {num_questions} questions for grade {grade_level} (0 means kindergarten).
This is an unverified teacher draft. Do not invent citations. Flag uncertain facts for review.
{question_instruction}
Return only JSON with a questions array. Each item must have exactly these fields:
id (consecutive integer starting at 1), question (nonempty student-facing text),
answer (nonempty teacher answer or scoring guidance). Include exactly {num_questions} items.
Include all choices or matching columns inside question where needed. Never put teacher answers in question.
""".strip()

    raw = generate_text(
        [
            {"role": "system", "content": "You create accurate, age-appropriate classroom worksheets."},
            {"role": "user", "content": prompt},
        ]
    )

    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict) or set(payload) != {'questions'}:
            raise ValueError()
        rows = payload['questions']
        if not isinstance(rows, list) or len(rows) != num_questions:
            raise ValueError()
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict) or set(row) != {'id', 'question', 'answer'}:
                raise ValueError()
            if type(row['id']) is not int or row['id'] != index:
                raise ValueError()
            if any(not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 4000 for key in ('question', 'answer')):
                raise ValueError()
        questions = ('\n' + delimiter + '\n').join(f"{r['id']}. {r['question'].strip()}" for r in rows)
        answers = ('\n' + delimiter + '\n').join(f"{r['id']}. {r['answer'].strip()}" for r in rows)
        return questions + '\n\nAnswers:\n' + answers
    except (ValueError, TypeError, KeyError):
        raise WorksheetFormatError('The worksheet did not contain the requested questions and matching answers. Your inputs are saved; please retry.') from None
