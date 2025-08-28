import os
import openai
import logging
from dotenv import load_dotenv

logging.basicConfig(filename='worksheet_generator.log', level=logging.DEBUG)

load_dotenv()

# Fetch API key from the environment variables
API_KEY = os.environ.get('OPENAI_API_KEY')

if API_KEY is None:
    print("API Key not found. Make sure you set the OPENAI_API_KEY environment variable in the .env file.")
else:
    openai.api_key = API_KEY

def generate_worksheet(topic, num_questions, question_type, formatting_delimiter):
    logging.debug(f"Generating worksheet with topic: {topic}, num_questions: {num_questions}, question_type: {question_type}, delimiter: {formatting_delimiter}")
    initial_prompt = f"I am a teacher and I need to create a worksheet for my students on the topic of {topic}."
    
    if question_type == "Short Answer Questions":
        worksheet_prompt = f"Please generate {num_questions} short answer questions related to {topic} and group all the questions first. Then, group all the answers separately."
    elif question_type == "Fill in the Blanks":
        worksheet_prompt = f"Generate {num_questions} fill in the blank questions about {topic} and group all the questions first. Then, group all the answers separately."
    elif question_type == "Matching":
        worksheet_prompt = f"Generate {num_questions} matching questions about {topic} and group all the questions first. Then, group all the answers separately."
    elif question_type == "Mix":
        num_each = num_questions // 3
        worksheet_prompt = (f"Generate a worksheet about {topic}. Provide:\n"
                            f"- {num_each} short answer questions\n"
                            f"- {num_each} fill in the blank questions\n"
                            f"- {num_each} matching questions.")
    elif question_type == "multiple_choice":
        worksheet_prompt = f"Generate {num_questions} multiple-choice questions about {topic}. For each question, provide 4 options and clearly indicate the correct answer."
    else:
        raise ValueError(f"Invalid question type: {question_type}")

    worksheet_prompt += " Please include the word 'Answers:' to separate the questions from the answers."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": initial_prompt},
                {"role": "user", "content": worksheet_prompt}
            ]
        )
        
        logging.debug("Full API Response: %s", response)

        worksheet_with_answers = response['choices'][0]['message']['content'].strip()
        logging.debug(f"API Response Content: {worksheet_with_answers}")

        return worksheet_with_answers

    except openai.error.APIError as e:
        logging.error(f"OpenAI API error: {e}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"Exception occurred while generating worksheet: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    try:
        topic = input("Enter the topic for the worksheet: ")
        question_type = input("Enter the type of question: ")
        num_questions = int(input("Enter the number of questions: "))
        formatting_delimiter = input("Enter the delimiter to separate questions (e.g., '----' or '*****'): ")
        
        worksheet_with_answers = generate_worksheet(topic, num_questions, question_type, formatting_delimiter)
        print("\nGenerated Worksheet Content:")
        print(worksheet_with_answers)
        
    except Exception as e:
        logging.error(f"Exception occurred while generating worksheet: {e}", exc_info=True)
        print(str(e))
