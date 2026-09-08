import re

from openai_service import generate_text


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


def parse_lesson_plan(lesson_plan_text: str) -> dict[str, str]:
    pattern = re.compile(
        r"^\s*Section:\s*(.+?)\s*\r?\nContent:\s*(.*?)(?=^\s*Section:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    sections = {
        title.strip(): content.strip()
        for title, content in pattern.findall(lesson_plan_text.strip())
    }
    return sections or {"Lesson Plan": lesson_plan_text.strip()}


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


def generate_lesson_plan(input_data: dict) -> tuple[dict[str, str], list[str]]:
    prompt_type = _required(input_data, "prompt")
    if prompt_type not in SECTION_ORDER:
        raise ValueError(f"Invalid prompt selected: {prompt_type}")

    cultures = input_data.get("culture_group") or []
    if isinstance(cultures, str):
        cultures = [cultures]
    culture_description = ", ".join(cultures) if cultures else "not specified"
    ordered_sections = SECTION_ORDER[prompt_type]
    output_format = "\n\n".join(
        f"Section: {section}\nContent: <detailed content>" for section in ordered_sections
    )

    prompt = f"""
You are an education specialist. {_lesson_blueprint(input_data)}

Make the plan comprehensive enough for a teacher to use without additional planning. Include engaging
introductory and concluding activities, discussions, hands-on work, assessment questions, differentiation,
and a detailed student worksheet where appropriate.

Class context:
- Target length: {_required(input_data, 'number_of_words')} words
- Grade: {_required(input_data, 'grade_level')}
- Students: {_required(input_data, 'number_of_students')}
- Cultural groups: {culture_description}
- Socioeconomic context: {input_data.get('socioeconomic_level') or 'not specified'}
- Experiential context: {input_data.get('experiential_type') or 'not specified'}
- Students with disabilities: {'yes' if input_data.get('disabled') else 'no'}
- English-language learners: {'yes' if input_data.get('ell') else 'no'}
- Gifted students: {'yes' if input_data.get('gifted') else 'no'}
- State standards: {input_data.get('state') or 'not specified'}

Return only the following section format. Preserve each section title exactly:
{output_format}
""".strip()

    generated = generate_text(
        [
            {"role": "system", "content": "You create practical, inclusive K-12 instructional materials."},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = parse_lesson_plan(generated)
    ordered_plan = {name: parsed[name] for name in ordered_sections if name in parsed}
    ordered_plan.update({name: content for name, content in parsed.items() if name not in ordered_plan})
    return ordered_plan, ordered_sections
