import unittest
import openai
from worksheet_generator import generate_worksheet_and_fact_sheet

openai.api_key = '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'

class TestWorksheetGenerator(unittest.TestCase):

    def test_generate_worksheet_and_fact_sheet(self):
        topic = "Germany"
        num_questions = 9
        question_type = "Short Answer Questions"
        formatting_delimiter = "----"
        
        worksheet, fact_sheet = generate_worksheet_and_fact_sheet(topic, num_questions, question_type)

        # Check if both worksheet and fact sheet are generated
        self.assertIsNotNone(worksheet)
        self.assertIsNotNone(fact_sheet)

        # Basic tests to check the content of the worksheet and fact sheet
        # Adjust these tests based on the expected content
        print("\nGenerated Worksheet:", worksheet)

        self.assertTrue(topic in worksheet)
        self.assertTrue("short answer questions" in worksheet)
        self.assertTrue("fill in the blank questions" in worksheet)
        self.assertTrue("matching definition questions" in worksheet)
	
        # Check if the topic is in the worksheet
        
        self.assertTrue(topic in worksheet)

        self.assertTrue(topic in fact_sheet)

    def test_generate_worksheet_and_fact_sheet_invalid_question_type(self):
        topic = "Photosynthesis"
        num_questions = 9
        question_type = "InvalidType"
        
        with self.assertRaises(ValueError):
            generate_worksheet_and_fact_sheet(topic, num_questions, question_type)


if __name__ == '__main__':
    unittest.main()
