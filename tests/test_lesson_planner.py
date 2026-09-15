import unittest
from unittest.mock import patch

import lesson_planner


SAMPLE_INPUT = {
    "prompt": "prompt3",
    "topic": "Photosynthesis",
    "number_of_words": "500",
    "grade_level": "5",
    "number_of_students": "30",
    "culture_group": ["Black", "Latino"],
    "socioeconomic_level": "Middle",
    "experiential_type": "Mixed",
    "disabled": True,
    "ell": False,
    "gifted": True,
    "state": "Arizona",
}


class LessonPlannerTests(unittest.TestCase):
    def test_parse_lesson_plan(self):
        result = lesson_planner.parse_lesson_plan(
            "Section: Title\nContent: Plant Power\n\n"
            "Section: Assessment\nContent: Exit ticket"
        )
        self.assertEqual(result["Title"], "Plant Power")
        self.assertEqual(result["Assessment"], "Exit ticket")

    def test_unstructured_response_is_rejected(self):
        with self.assertRaises(lesson_planner.LessonFormatError):
            lesson_planner.parse_lesson_plan("A complete plan")

    @patch("lesson_planner.generate_text")
    def test_generate_lesson_plan_uses_safe_api_boundary(self, mock_generate):
        mock_generate.return_value = "\n\n".join(
            f"Section: {name}\nContent: Learn photosynthesis."
            for name in lesson_planner.SECTION_ORDER['prompt3']
        )
        plan, order = lesson_planner.generate_lesson_plan(SAMPLE_INPUT)

        self.assertEqual(plan["Lesson Plan Purpose Statement"], "Learn photosynthesis.")
        self.assertEqual(order, lesson_planner.SECTION_ORDER["prompt3"])
        sent_messages = mock_generate.call_args.args[0]
        self.assertIn("Black, Latino", sent_messages[1]["content"])

    @patch("lesson_planner.generate_text")
    def test_single_culture_string_is_not_split_into_characters(self, mock_generate):
        mock_generate.return_value = "\n\n".join(
            f"Section: {name}\nContent: Ready"
            for name in lesson_planner.SECTION_ORDER['prompt3']
        )
        data = dict(SAMPLE_INPUT, culture_group="Latino")
        lesson_planner.generate_lesson_plan(data)
        sent_messages = mock_generate.call_args.args[0]
        self.assertIn("Cultural groups: Latino", sent_messages[1]["content"])

    def test_invalid_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            lesson_planner.generate_lesson_plan(dict(SAMPLE_INPUT, prompt="unknown"))


if __name__ == "__main__":
    unittest.main()
