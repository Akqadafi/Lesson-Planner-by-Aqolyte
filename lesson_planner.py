import json
import re
from legacy_choices import CHOICES

from openai_service import generate_text
from response_schemas import legacy_lesson_schema


SECTION_ORDER = {
    "prompt0": ["Title", "Lesson Overview", "Learning Objectives and Outcomes", "Materials", "Lesson Procedures", "Assessment", "Concluding Remarks", "Worksheet"],
    "prompt1": ["Title", "Lesson Objectives", "Materials", "Activities", "Assessment"],
    "prompt2": ["Learning Purpose Statement", "Input/Instruction", "Activity/Independent Practice", "Assessment"],
    "prompt3": ["Lesson Plan Purpose Statement", "Input", "Procedural Components", "Direct Instruction and Modeling", "Activities", "Assessment"],
    "prompt4": ["Purpose Statement", "Pre-Reading Activity", "During-Reading", "Post-Reading Activity", "Assessment"],
    "prompt5": ["Purpose Statement", "Discovery Activity", "Input", "Activity", "Assessment"],
}

# Backward-compatible alias for code that imported the old lowercase name.
section_order = SECTION_ORDER


def gpt4_request(messages):
    """Backward-compatible wrapper around the current Responses API client."""
    return generate_text(messages)


class LessonFormatError(ValueError):
    """The model response is not a complete lesson draft."""


def parse_lesson_plan(lesson_plan_text: str, expected_sections=None) -> dict[str, str]:
    message = 'The generated lesson was incomplete or incorrectly formatted. Please retry; your inputs have been kept.'
    if not isinstance(lesson_plan_text, str) or not lesson_plan_text.strip():
        raise LessonFormatError(message)
    blocks = re.split(r'(?=^[ \t]*Section:)', lesson_plan_text.strip(), flags=re.MULTILINE)
    sections = {}
    for block in blocks:
        if not block.strip():
            continue
        match = re.fullmatch(r'[ \t]*Section:[ \t]*([^\r\n]+)\r?\n[ \t]*Content:[ \t]*(.*)', block.strip(), re.DOTALL)
        if not match:
            raise LessonFormatError(message)
        title, content = (part.strip() for part in match.groups())
        if not title or not content or title in sections or content == '<detailed content>':
            raise LessonFormatError(message)
        sections[title] = content
    if expected_sections is not None:
        if set(sections) != set(expected_sections):
            raise LessonFormatError(message)
        return {name: sections[name] for name in expected_sections}
    return sections


def parse_structured_lesson(lesson_plan_text: str, expected_sections) -> dict[str, str]:
    message = 'The generated lesson was incomplete or incorrectly formatted. Please retry; your inputs have been kept.'
    try:
        payload = json.loads(lesson_plan_text)
        if not isinstance(payload, dict) or set(payload) != {'sections'}:
            raise ValueError()
        rows = payload['sections']
        if not isinstance(rows, list) or len(rows) != len(expected_sections):
            raise ValueError()
        sections = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'title', 'content'}:
                raise ValueError()
            title, content = row['title'], row['content']
            if (title not in expected_sections or title in sections or not isinstance(content, str)
                    or not content.strip() or len(content) > 30000):
                raise ValueError()
            sections[title] = content.strip()
        if set(sections) != set(expected_sections):
            raise ValueError()
        return {name: sections[name] for name in expected_sections}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise LessonFormatError(message) from None


def get_samr_definition() -> str:
    return (
        "The SAMR model describes how technology may affect teaching and learning through "
        "Substitution, Augmentation, Modification, and Redefinition."
    )


def _required(input_data: dict, name: str):
    value = input_data.get(name)
    if value is None or value == "":
        raise ValueError(f"Missing required lesson-plan field: {name}")
    return value


def _lesson_blueprint(input_data: dict) -> str:
    prompt_type = _required(input_data, "prompt")
    topic = _required(input_data, "topic")

    if prompt_type == "prompt0":
        return (
            f"Create a detailed WebQuest about {topic} using the SAMR model and relevant ISTE standards. "
            f"Use this SAMR definition: {get_samr_definition()}"
        )
    if prompt_type == "prompt1":
        return f"Create a {_required(input_data, 'lesson_type')} lesson plan about {topic}."
    if prompt_type == "prompt2":
        return (
            f"Create a concept-based lesson plan about {topic}, including a learning-purpose statement, "
            "input and guided practice, independent real-world application, and assessment."
        )
    if prompt_type == "prompt3":
        return (
            f"Create a skills-based lesson plan about {topic}, including objectives, materials, procedure, "
            "assessment, differentiation, and teacher reflection."
        )
    if prompt_type == "prompt4":
        return (
            f"Create a scaffolded reading experience about {topic} that promotes reading enjoyment and "
            "comprehension through pre-reading, during-reading, and post-reading activities."
        )
    if prompt_type == "prompt5":
        return (
            f"Create a directed discovery-learning lesson about {topic}, including the learning purpose, "
            "discovery activity, teacher input, application, and assessment."
        )
    raise ValueError(f"Invalid prompt selected: {prompt_type}")


def validate_input(data):
    if data.get('prompt') not in SECTION_ORDER:
        raise ValueError('Choose a supported lesson type.')
    for field in ('topic', 'state', 'lesson_type'):
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > 300:
            raise ValueError(f'{field} must be text of at most 300 characters.')
    for field in ('prior_knowledge', 'learner_supports'):
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > 4000:
            raise ValueError(f'{field} must be text of at most 4,000 characters.')
    if data['prompt'] == 'prompt1' and not data.get('lesson_type', '').strip():
        raise ValueError('Choose a lesson approach.')

    for field in ('state', 'lesson_type'):
        if data.get(field) and data[field] not in CHOICES[field]:
            raise ValueError(f'Choose a supported {field.replace("_", " ")}.')
    for name, low, high in [('grade_level', 0, 12), ('number_of_students', 1, 100), ('number_of_words', 50, 5000)]:
        try:
            value = int(data.get(name, ''))
        except (TypeError, ValueError):
            raise ValueError(f'{name} must be a whole number.')
        if not low <= value <= high:
            raise ValueError(f'{name} must be between {low} and {high}.')
    topic = str(data.get('topic', '')).strip()
    if not topic or len(topic) > 300:
        raise ValueError('Enter a topic of 1–300 characters.')


def generate_lesson_plan(input_data: dict) -> tuple[dict[str, str], list[str]]:
    validate_input(input_data)
    prompt_type = _required(input_data, "prompt")
    if prompt_type not in SECTION_ORDER:
        raise ValueError(f"Invalid prompt selected: {prompt_type}")

    ordered_sections = SECTION_ORDER[prompt_type]
    output_format = ", ".join(ordered_sections)

    prompt = f"""
You are an education specialist. {_lesson_blueprint(input_data)}

Create a draft for teacher review; do not claim factual accuracy or verified standards alignment. Do not invent standard identifiers, citations or source URLs. Mark unsupported alignment as needing verification. Include engaging
introductory and concluding activities, discussions, hands-on work, assessment questions, differentiation,
and a detailed student worksheet where appropriate. Use only the learner needs the teacher describes. Do not
infer abilities, interests or support needs from identity or demographic characteristics.

Class context:
- Target length: {_required(input_data, 'number_of_words')} words
- Grade: {_required(input_data, 'grade_level')}
- Students: {_required(input_data, 'number_of_students')}
- Prior knowledge and skills: {input_data.get('prior_knowledge') or 'not specified'}
- Teacher-described learner support: {input_data.get('learner_supports') or 'not specified'}
- Requested state (standards are not retrieved or verified): {input_data.get('state') or 'not specified'}

Return one complete JSON section for each of these titles, preserving every title exactly:
{output_format}
""".strip()

    generated = generate_text(
        [
            {"role": "system", "content": "You create practical, inclusive K-12 instructional materials."},
            {"role": "user", "content": prompt},
        ],
        response_schema=legacy_lesson_schema(ordered_sections),
        schema_name='legacy_lesson_plan',
    )
    ordered_plan = parse_structured_lesson(generated, ordered_sections)
    return ordered_plan, ordered_sections
