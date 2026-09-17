import json
import re
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

    rules = {
        'multiple_choice': 'In question put exactly four distinct choices on separate lines labeled A. through D. Start answer with the correct letter and a period, followed by explanation.',
        'true_false': 'Start answer with True: or False: followed by an explanation.',
        'matching': 'Each question is one matching set. In question use separate lines L1: item, L2: item (up to L10) and R1: option, R2: option (up to R10). Include equal left/right counts. Start answer with one L1=R2 mapping per line, covering each label exactly once; put explanation after mappings.',
        'Fill in the Blanks': 'Include ___ in each question for the student to fill in.'
    }
    canonical = 'matching' if question_type == 'Matching' else question_type
    question_instruction += ' ' + rules.get(canonical, '')

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
            validate_type(row, canonical)
        questions = ('\n' + delimiter + '\n').join(f"{r['id']}. {r['question'].strip()}" for r in rows)
        answers = ('\n' + delimiter + '\n').join(f"{r['id']}. {r['answer'].strip()}" for r in rows)
        return questions + '\n\nAnswers:\n' + answers
    except (ValueError, TypeError, KeyError):
        raise WorksheetFormatError('The worksheet did not contain the requested questions and matching answers. Your inputs are saved; please retry.') from None


def validate_type(row, kind):
    question, answer = row['question'], row['answer']
    if kind == 'multiple_choice':
        choices = re.findall(r'^([A-Z])\.\s+([^\n]+)', question, re.MULTILINE)
        if [key for key, _ in choices] != list('ABCD') or len({value.strip().casefold() for _, value in choices}) != 4:
            raise ValueError('Four distinct choices required')
        if not re.match(r'^[A-D]\.\s+\S', answer.strip()):
            raise ValueError('Answer must reference a choice and explain it')
    elif kind == 'true_false':
        if not re.match(r'^(True|False):\s+\S', answer.strip()):
            raise ValueError('Truth value and explanation required')
    elif kind == 'matching':
        labels = re.findall(r'^([LR]\d+):\s+([^\n]+)', question, re.MULTILINE)
        left = [key for key, _ in labels if key.startswith('L')]
        right = [key for key, _ in labels if key.startswith('R')]
        count = len(left)
        if not 2 <= count <= 10 or left != [f'L{i}' for i in range(1,count+1)] or right != [f'R{i}' for i in range(1,count+1)]:
            raise ValueError('Complete matching columns required')
        pairs = re.findall(r'^(L\d+)=(R\d+)\s*$', answer, re.MULTILINE)
        if len(pairs) != count or {a for a,b in pairs} != set(left) or {b for a,b in pairs} != set(right):
            raise ValueError('Complete one-to-one answer mappings required')
    elif kind == 'Fill in the Blanks' and '___' not in question:
        raise ValueError('Blank required')
