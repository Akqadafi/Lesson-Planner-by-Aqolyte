from form_client import client as form_client
import os
import unittest
from unittest.mock import patch


os.environ.setdefault("FLASK_SECRET_KEY", "unit-test-secret-not-for-production")
os.environ.setdefault("OPENAI_API_KEY", "unit-test-placeholder")

import app as app_module
from openai_service import GenerationUnavailableError


class AppRouteTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = form_client(app_module.app)

    def test_landing_and_products_templates_resolve(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/products").status_code, 200)

    def test_invalid_prompt_is_rejected(self):
        response = self.client.post("/prompt_selection", data={"prompt": "prompt99"})
        self.assertEqual(response.status_code, 400)

    def test_teacher_described_context_is_preserved(self):
        with self.client.session_transaction() as browser_session:
            browser_session["prompt"] = "prompt3"

        response = self.client.post(
            "/home",
            data={
                "topic": "Photosynthesis",
                "number_of_words": "500",
                "grade_level": "5",
                "number_of_students": "25",
                "prior_knowledge": "Students can label a plant cell.",
                "learner_supports": "Use diagrams and read directions aloud.",
                "state": "Arizona",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as browser_session:
            saved = browser_session["input_data"]
            self.assertEqual(saved["prior_knowledge"], "Students can label a plant cell.")
            self.assertEqual(saved["learner_supports"], "Use diagrams and read directions aloud.")
            self.assertNotIn("culture_group", saved)

    @patch("app.lesson_planner.generate_lesson_plan")
    def test_output_reuses_generated_lesson(self, mock_generate):
        mock_generate.return_value = ({"Title": "Plants", "Assessment": "Exit ticket"}, [])
        with self.client.session_transaction() as browser_session:
            browser_session["input_data"] = {"grade_level": "5"}

        first = self.client.post("/output", data={"generate":"1"}, follow_redirects=True)
        second = self.client.get("/output")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        mock_generate.assert_called_once()

    def test_word_export_is_in_memory(self):
        with self.client.session_transaction() as browser_session:
            browser_session["content_type"] = "Worksheet"
            browser_session["content"] = "Question 1\nAnswers:\nAnswer 1"
        response = self.client.post("/output", data={"download_word": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[:2], b"PK")

    @patch("app.lesson_planner.generate_lesson_plan", side_effect=GenerationUnavailableError("The AI service took too long to respond. Please retry; your saved draft is unchanged."))
    def test_legacy_lesson_provider_failure_preserves_inputs(self, mock_generate):
        saved = {"grade_level": "5", "topic": "Fractions"}
        with self.client.session_transaction() as browser_session:
            browser_session["input_data"] = saved
        response = self.client.post("/output", data={"generate": "1"})
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"too long to respond", response.data)
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["input_data"], saved)
            self.assertNotIn("content", browser_session)

    @patch("app.generate_worksheet", side_effect=GenerationUnavailableError("The app could not connect to OpenAI. Check the server's internet access and retry. Your saved draft is unchanged."))
    def test_legacy_worksheet_provider_failure_preserves_inputs(self, mock_generate):
        saved = {"topic": "Fractions", "num_questions": 5, "question_types": "essay", "formatting_delimiter": "----", "grade_level": 5}
        with self.client.session_transaction() as browser_session:
            browser_session["worksheet_data"] = saved
        response = self.client.post("/output", data={"generate": "1"})
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"connect to OpenAI", response.data)
        with self.client.session_transaction() as browser_session:
            self.assertEqual(browser_session["worksheet_data"], saved)
            self.assertNotIn("content", browser_session)


if __name__ == "__main__":
    unittest.main()
