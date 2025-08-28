import os
import openai
from dotenv import load_dotenv

load_dotenv()

# Your API Key should be stored in the OPENAI_API_KEY environment variable
API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize the OpenAI API client
openai.api_key = API_KEY

# Define the prompt for generating questions about German Geography
prompt = "Generate 5 short answer questions about German Geography and provide their answers."

# Make the API call
try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
except openai.error.APIError as e:
    print(f"OpenAI API error: {e}")

# Print the API response to diagnose if it's returning as expected
worksheet_with_answers = response['choices'][0]['message']['content'].strip()
print("API Response:", worksheet_with_answers)
