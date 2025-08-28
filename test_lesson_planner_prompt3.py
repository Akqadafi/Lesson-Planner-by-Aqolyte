import unittest
from lesson_planner import generate_lesson_plan  # Adjust the import based on your actual function

class TestLessonPlanner(unittest.TestCase):
    def test_generate_lesson_plan(self):
        input_data = {
            'prompt': 'prompt3',
            'topic': 'Photosynthesis',
            'number_of_words': 500,  # Add this line
            'grade_level': 10,       # Add this line
            'number_of_students': 30, # Add this line
            'culture_group': ['black']  # Add this line
        }
        expected_output = (
            "You are an education specialist tasked with creating a skills-based lesson plan for teachers to teach: Photosynthesis. "
            "The lesson plan should focus on teaching students a specific skill, and it should be designed to provide detailed instructions for the teacher to follow. "
            "The lesson plan should include the following sections: "
            "1. Objective: A clear statement of what the students will be able to do by the end of the lesson. "
            "2. Materials: A list of materials needed for the lesson. "
            "3. Procedure: A step-by-step guide for the teacher to follow. "
            "4. Assessment: A description of how the students' learning will be assessed. "
            "5. Differentiation: Strategies for differentiating the lesson to meet the needs of all students. "
            "6. Reflection: Questions for the teacher to reflect on the lesson and its effectiveness."
        )
        result = generate_lesson_plan(input_data)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()