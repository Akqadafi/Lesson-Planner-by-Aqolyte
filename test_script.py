import openai
from worksheet_generator import generate_worksheet_and_fact_sheet

# Initialize the OpenAI API (if required and not done within the imported module)
openai.api_key = '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'  # Replace with your key

def test_generate_worksheet_and_fact_sheet():
    # Dummy data
    topic = "Germany"
    num_questions = 5
    question_type = "Short Answer Questions"
    formatting_delimiter = "----"
    
    # Call the function
    worksheet, answer_bank = generate_worksheet(topic, num_questions, question_type, formatting_delimiter)
    
    # Print the results
    print("Generated Worksheet Content:")
    print(worksheet)

# Execute the test function
test_generate_worksheet()



if __name__ == '__main__':
    unittest.main()
