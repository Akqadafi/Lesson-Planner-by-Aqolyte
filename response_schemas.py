"""Strict JSON Schemas for all generated lesson materials.

The provider enforces these shapes. Application validators still enforce semantic
rules such as exact ordering, field lengths, timing, and worksheet conventions.
"""


def _object(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _fixed_array(items, count):
    return {"type": "array", "items": items, "minItems": count, "maxItems": count}


def _text(description):
    return {"type": "string", "description": description}


def _activity():
    return _object({
        "session": {"type": "integer", "description": "One-based lesson session number."},
        "minutes": {"type": "integer", "description": "Instruction minutes, excluding transition."},
        "transition_minutes": {"type": "integer", "description": "Minutes needed to transition."},
        "objective": _text("Observable learning objective for this activity."),
        "grouping": _text("Individual, pair, group, or whole-class organization."),
        "materials": {"type": "array", "items": _text("One material teachers or students need.")},
        "teacher_steps": {"type": "array", "items": _text("One ordered teacher action.")},
        "student_directions": {"type": "array", "items": _text("One ordered student direction.")},
        "assessment": _text("Check for understanding and observable evidence."),
        "supports_extensions": _text("Teacher-described supports plus an optional extension."),
    })


def lesson_sections_schema(section_ids, activity_ids=()):
    activity_ids = set(activity_ids)
    variants = []
    for section_id in section_ids:
        properties = {"id": {"type": "string", "enum": [section_id]}}
        if section_id in activity_ids:
            properties["activity"] = _activity()
        else:
            properties["content"] = _text("Complete plain-text content for this lesson section.")
        variants.append(_object(properties))
    item_schema = variants[0] if len(variants) == 1 else {"anyOf": variants}
    return _object({"sections": _fixed_array(item_schema, len(section_ids))})


def legacy_lesson_schema(section_titles):
    item = _object({
        "title": {"type": "string", "enum": list(section_titles)},
        "content": _text("Complete plain-text content for this lesson section."),
    })
    return _object({"sections": _fixed_array(item, len(section_titles))})


def handout_schema(question_count):
    question = _object({
        "id": {"type": "integer", "description": "Consecutive one-based item number."},
        "prompt": _text("Student-facing question, prompt, reference content, or task."),
        "answer": _text("Teacher-only answer, scoring guidance, or verification note."),
    })
    return _object({
        "title": _text("Short title for the student handout."),
        "instructions": _text("Clear student-facing directions."),
        "questions": _fixed_array(question, question_count),
    })


def worksheet_schema(question_count, mixed=False):
    properties = {
        "id": {"type": "integer", "description": "Consecutive one-based question number."},
        "question": _text("Student-facing question including choices or matching columns when needed."),
        "answer": _text("Teacher-only answer plus explanation or scoring guidance."),
    }
    if mixed:
        properties["type"] = {
            "type": "string",
            "enum": ["short_answer", "Fill in the Blanks", "matching"],
        }
    return _object({"questions": _fixed_array(_object(properties), question_count)})
