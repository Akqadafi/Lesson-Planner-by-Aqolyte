import json
import unittest
from unittest.mock import patch

import worksheet_generator


class WorksheetGeneratorTests(unittest.TestCase):
    @patch("worksheet_generator.generate_text")
    def test_generates_without_a_live_api_call(self, mock_generate):
        mock_generate.return_value = json.dumps({"questions":[{"id":i,"question":f"Question {i}","answer":f"Answer {i}"} for i in range(1,6)]})
        result = worksheet_generator.generate_worksheet(
            "German geography", 5, "Short Answer Questions", "----"
        )
        self.assertIn("5. Question 5", result)
        self.assertIn("5. Answer 5", result)
        sent_messages = mock_generate.call_args.args[0]
        self.assertIn("exactly 5 questions", sent_messages[1]["content"])
        self.assertIn("German geography", sent_messages[1]["content"])

    def test_invalid_question_type_is_rejected(self):
        with self.assertRaises(ValueError):
            worksheet_generator.generate_worksheet("Math", 5, "Unknown")

    def test_question_count_is_bounded(self):
        with self.assertRaises(ValueError):
            worksheet_generator.generate_worksheet("Math", 0, "Matching")


if __name__ == "__main__":
    unittest.main()
