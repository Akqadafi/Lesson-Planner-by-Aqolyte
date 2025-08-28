import os
from dotenv import load_dotenv
import openai
from worksheet_generator import generate_worksheet
# Load environment variables from the .env file
load_dotenv()

# Fetch API key from the environment variables
API_KEY = os.environ.get('OPENAI_API_KEY')

if API_KEY is None:
    print("API Key not found. Make sure you set the OPENAI_API_KEY environment variable in the .env file.")
else:
    print("API Key: ", API_KEY)

# Set the API key for OpenAI
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
            title = section.replace("Section: ", "")
            content = ""
            lesson_plan_dict[title] = content

    return lesson_plan_dict

def get_samr_definition():
    return ("The SAMR model offers a method of seeing how computer technology might impact teaching and learning. "
            "It shows a progression that adopters of educational technology often follow as they progress through teaching and learning with technology. "
            "SAMR stands for Substitution, Augmentation, Modification, and Redefinition.")

def generate_lesson_plan(input_data):
    print("Received prompt in generate_lesson_plan:", input_data['prompt'])  # Debug print
    samr_definition = get_samr_definition()
    
    if input_data['prompt'] == 'prompt0':
        prompt = (f"You are an education specialist. Create a detailed webquest about {input_data['topic']} using the SAMR model and adheres to ISTE standards.This lesson plan should include at least a title, lesson objectives, materials, assessment and a worksheet. The SAMR model is defined as follows:\n\n{samr_definition}\n\n")        
    elif input_data['prompt'] == 'prompt1':
        prompt = (f"You are an education specialist tasked with creating a {input_data['lesson_type']} lesson plan for teachers to teach: {input_data['topic']}.")
    elif input_data['prompt'] == 'prompt2':
        prompt = (f"You are an education specialist crafting a concept-based lesson plan for teachers to teach: {input_data['topic']}. The lesson's blueprint is as follows: "
                  f"I. Learning Purpose Statement: Pupils will delve deep into {input_data['topic']}."
                  f"II. Input/Instruction: This will encapsulate the essence of {input_data['topic']}, from its definition to its attributes, both positive and negative.Guided practice and informal assessments will further reinforce their grasp on the concept."
                  f"III. Activity/Independent Practice: Activities that allow students to apply and extend their understanding of {input_data['topic']}. "
                  f"Ensure these activities are interactive and relate the topic to real-world applications.")

    elif input_data['prompt'] == 'prompt3':
        prompt = (f"You are an education specialist tasked with creating a skills-based lesson plan for teachers to teach: {input_data['topic']}. The lesson plan should include the following sections: "
            f"1. Objective: A clear statement of what the students will be able to do by the end of the lesson. "
            f"2. Materials: A list of materials needed for the lesson. "
            f"3. Procedure: A step-by-step guide for the teacher to follow. "
            f"4. Assessment: A description of how the students' learning will be assessed. "
            f"5. Differentiation: Strategies for differentiating the lesson to meet the needs of all students. "
            f"6. Reflection: Questions for the teacher to reflect on the lesson and its effectiveness.")


    elif input_data['prompt'] == 'prompt4':
        prompt = (f"You are an education specialist tasked with creating a reading lesson plan for teachers in the scaffolded reading experience (SRE) program to teach: {input_data['topic']}.The lesson plan should focus on promoting reading enjoyment and comprehension."  f"The lesson's blueprint is as follows:"
                 f"I. Purpose Statement: The purpose statement should clearly define the objectives of the lesson for both narrative and expository texts. For narrative texts, the objective is to have students read and enjoy a specific story or chapter. For expository texts, the objective is to have students read and understand a particular book or chapter."
                 f"II. Pre-Reading Activity: The pre-reading activity should be brief, lasting between 1 to 4 minutes, and designed to prepare students for their reading session."
                 f"III. During-Reading: Students will engage in independent reading or follow a substitute-friendly reading method during SRE."
                 f"IV. Post-Reading Activity: Create an activity that encourages students to interact with ideas from the story they read. For narrative texts, consider including aesthetic response activities that allow students to express their emotional or creative responses to the story.")


# ...

    elif input_data['prompt'] == 'prompt5':
        prompt = (
        f"You are an education specialist tasked with creating a discovery-based lesson plan for teachers to teach: {input_data['topic']}."
        f"The goal of this lesson plan is to implement discovery learning in a planned and directed manner to teach specific concepts, lessons, or information."
        f"The lesson's blueprint is as follows:"
        f"I. Purpose Statement: Clearly define the specific concepts, lessons, or information you want students to learn through discovery. This statement should guide the entire lesson plan."
        f"II. Discovery Activity: Identify the elements or key concepts you want students to discover during the lesson. Design an engaging activity that allows students to explore and uncover these elements on their own. After the activity, encourage students to identify or describe the salient elements they discovered."
        f"III. Input: Provide students with specific information that directly relates to the lesson's purpose. Use this input to complement their discoveries or to extend their initial findings."
        f"IV. Activity: Design an activity that allows students to manipulate, reinforce, or extend their learning based on the elements they discovered."
        f"This activity should build upon their explorations and encourage a deeper understanding of the concepts."
    )
    else:
        raise ValueError(f'Invalid prompt selected: {input_data["prompt"]}')

# ...


    # Add common details to the prompt
    prompt += (f"The lesson plan should include detailed instructions for the teacher to follow. The lesson plan should be "
               f"complete and comprehensive, meaning the teacher would need no additional resources in order to use the lesson." 
               f"Provide detailed instructions for the teacher, including introductory activities to engage students and           concluding remarks or activities to wrap up the lesson."
               f"The lesson structure should encompass a title, lesson overview, learning objectives and outcomes, necessary materials, diverse activities for students and assessment questions. The activities should range from discussions to hands-on exercises."
               f"Furthermore, a meticulously detailed worksheet should be integral to the plan. This worksheet should offer specific questions, diagrams, and content tailored for student engagement."
               f"It should be about {input_data['number_of_words']} words, detailed and appropriate for grade {input_data['grade_level']} and a class of {input_data['number_of_students']} students. "
               f"The cultural makeup of the students includes {', '.join(input_data['culture_group'])},"
               f"the Socioeconomic level of the students is {input_data.get('socioeconomic_level')} with the Experiential Type of {input_data.get('experiential_type')}. The students include {'Disabled' if input_data.get('disabled') else 'Not Disabled'}, {'ELL' if input_data.get('ell') else 'Not ELL'}, "

               f"and {'Gifted' if input_data.get('gifted') else 'Not Gifted'}. The lesson should fit the state of {input_data.get('state')} standards.")


    # Create the messages for the GPT model
    messages = [
        {
            "role": "system",
            "content": prompt
        },
    ]
    
    # Call the GPT model and get the generated lesson plan
    lesson_plan_str = gpt4_request(messages)

    # Parse the lesson plan string into a dictionary
    lesson_plan_dict = parse_lesson_plan(lesson_plan_str)

    # Get the predefined order of section titles for this prompt type
    ordered_sections = section_order.get(input_data['prompt'], [])

    return lesson_plan_dict, ordered_sections

# Define a mapping from prompt types to the predefined order of section titles
section_order = {
    'prompt0': ["Title", "Lesson Overview", "Learning Objectives and Outcomes", "Materials", "Lesson Procedures", "Assessment", "Concluding Remarks", "Worksheet"],
    'prompt1': ["Title", "Lesson Objectives", "Materials", "Activities", "Assessment"],
    'prompt2': ["Learning Purpose Statement", "Input/Instruction", "Activity/Independent Practice", "Assessment"],
    'prompt3': ["Lesson Plan Purpose Statement", "Input", "Procedural Components", "Direct Instruction and Modeling", "Activities", "Assessment"],
    'prompt4': ["Purpose Statement", "Pre-Reading Activity", "During-Reading", "Post-Reading Activity", "Assessment"],
    'prompt5': ["Purpose Statement", "Discovery Activity", "Input", "Activity", "Assessment"]
}


