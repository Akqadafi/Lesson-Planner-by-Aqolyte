from lesson_planner import generate_lesson_plan

# Default sample data for most prompts
default_sample_data = {
    'topic': 'Photosynthesis',
    'number_of_words': 500,
    'grade_level': '5',
    'number_of_students': 30,
    'culture_group': ['American', 'Mexican'],
    'socioeconomic_level': 'Middle Class',
    'experiential_type': 'Kinesthetic Learners',
    'disabled': True,
    'ell': False,
    'gifted': False,
    'state': 'California',
    'prompt': ''
}

# Specific sample data for prompt1
prompt1_sample_data = {
    'prompt': '',
    'topic': 'The Solar System',
    'number_of_words': '1000',
    'grade_level': '5',
    'number_of_students': '30',
    'culture_group': ['African American', 'Hispanic'],
    'socioeconomic_level': 'Middle Class',
    'experiential_type': 'Urban',
    'disabled': False,
    'ell': False,
    'gifted': True,
    'state': 'California',
    'lesson_type': 'Science'
}

def select_prompt():
    available_prompts = ['prompt0', 'prompt1', 'prompt2', 'prompt3', 'prompt4', 'prompt5']
    print("Available prompts:", ", ".join(available_prompts))
    prompt = input("Select a prompt: ")

    while prompt not in available_prompts:
        print(f"Invalid prompt. Choose from {', '.join(available_prompts)}")
        prompt = input("Select a prompt: ")

    return prompt

if __name__ == "__main__":
    while True:
        prompt = select_prompt()
        
        # Use prompt1_sample_data for prompt1, otherwise use default_sample_data
        sample_data = prompt1_sample_data if prompt == 'prompt1' else default_sample_data.copy()
        sample_data['prompt'] = prompt

        lesson_plan = generate_lesson_plan(sample_data)
        
        print("\nGenerated Lesson Plan:")
        for section, content in lesson_plan.items():
            print(f"Section: {section}")
            print(f"Content: {content}\n")
        
        cont = input("Do you want to test another prompt? (Yes/No): ").lower()
        if cont != 'yes':
            break

