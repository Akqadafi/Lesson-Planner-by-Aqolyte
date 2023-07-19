import os
import openai

# Fetch API key from the environment variables
API_KEY = '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'
print("API Key: ", API_KEY)

openai.api_key = API_KEY

def gpt4_request(messages):
    model_name = "gpt-4"
    
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=messages
    )

    if response['choices'][0]['finish_reason'] == 'stop':
        return response['choices'][0]['message']['content']
    else:
        return "Error: The GPT-4 request was not successful"

def parse_lesson_plan(lesson_plan_str):
    sections = lesson_plan_str.split("\n\n")  # Split by blank lines
    lesson_plan_dict = {}
    
    for section in sections:
        if "\nContent: " in section:
            title, content = section.split("\nContent: ")
            title = title.replace("Section: ", "")
            lesson_plan_dict[title] = content
        else:
            # Handle the case where "\nContent: " is not in the section
            # For example, you could use the whole section as the title and use an empty string as the content
            title = section.replace("Section: ", "")
            content = ""
            lesson_plan_dict[title] = content

    return lesson_plan_dict


def generate_lesson_plan(input_data):
    # Create the messages for the GPT model
    messages = [
        {
            "role": "system",
            "content": "You are an education specialist tasked with creating a {} lesson plan for teachers based on the {}. The lesson plan should include detailed instructions for the teacher to follow. The lesson plan should be complete and comprehensive, meaning the teacher would need no additional resources in order to use the lesson in their class. The instructions should be divided into title, instructions for the teacher, materials, activities for students and assessment questions. Each lesson plan should include a worksheet with facts and details for the students to use. The lesson is about {}. It should be about {} words, detailed and appropriate for the {} grade and a class of {} students. The cultural makeup of the students include {}, the Socioeconomic level of the students is {} with the Experiential Type of {}. The students include {}, {}, and {}. The lesson should fit the state of {} standards.".format(
                input_data['lesson_type'],
                input_data['model_type'],
                input_data['topic'],
                input_data['number_of_words'],
                input_data['grade_level'],
                input_data['number_of_students'],
                ', '.join(input_data['culture_group']),
                input_data['socioeconomic_level'],
                input_data['experiential_type'],
                'Disabled' if input_data['disabled'] else 'Not Disabled',
                'ELL' if input_data['ell'] else 'Not ELL',
                'Gifted' if input_data['gifted'] else 'Not Gifted',
                input_data['state'],
            )
        },
 
    ]
    
    # Call the GPT model and get the generated lesson plan
    lesson_plan_str = gpt4_request(messages)

    # Parse the lesson plan string into a dictionary
    lesson_plan_dict = parse_lesson_plan(lesson_plan_str)

    return lesson_plan_dict

