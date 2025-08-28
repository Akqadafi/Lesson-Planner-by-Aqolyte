from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import lesson_planner
from worksheet_generator import generate_worksheet
import logging
import pypandoc
from docx import Document
from bs4 import BeautifulSoup
from dotenv import load_dotenv


logging.basicConfig(filename='app.log', level=logging.DEBUG)


# Configure logging
logging.basicConfig(filename='html_to_docx.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # reads .env in your project folder

app = Flask(__name__)
secret = os.getenv("FLASK_SECRET_KEY")
if not secret:
    raise RuntimeError("Missing FLASK_SECRET_KEY. Put it in .env (not committed).")
app.config["SECRET_KEY"] = secret
app.config["SESSION_TYPE"] = "filesystem"  # only used if you're using Flask-Session


def html_to_docx(html_content, output_filename):
    try:
        # Define output path
        output_path = os.path.join(os.getcwd(), output_filename)
        
        # Use pypandoc to convert HTML to DOCX
        pypandoc.convert_text(html_content, 'docx', format='html', outputfile=output_path)
        
        logging.info("Document saved successfully at %s", output_path)
        return output_path
    except Exception as e:
        logging.error("An error occurred: %s", e)
        return None

# Example usage
html_content = "<html><body><p>This is a test paragraph.</p><p>This is another paragraph.</p></body></html>"
output_filename = "output.docx"
html_to_docx(html_content, output_filename)


@app.route('/')
def landing ():
    return render_template('home.html')

@app.route('/second_landing')
def second_landing():
    return render_template('second_landing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/choose')
def choose():
    return render_template('choose.html')

@app.route('/clear_cache')
def clear_cache():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/redirect_choice', methods=['POST'])
def redirect_choice():
    choice = request.form.get('choice')
    if choice == "lesson":
        session.pop('worksheet_data', None)  # Remove worksheet_data if it exists
        return redirect(url_for('prompt_selection'))
    elif choice == "worksheet":
        session.pop('input_data', None)  # Remove input_data if it exists
        return redirect(url_for('worksheet'))
    else:
        return redirect(url_for('landing'))

@app.route('/prompt_selection', methods=['GET', 'POST'])
def prompt_selection():
    if request.method == 'POST':
        session['prompt'] = request.form['prompt']
        return redirect(url_for('home'))
    return render_template('prompt_selection.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        input_data = request.form.to_dict()
        input_data['prompt'] = session.get('prompt')
        session['input_data'] = input_data
        return redirect(url_for('output'))
    else:
        prompt = session.get('prompt')
        if prompt:
            form_template = f"prompt{prompt[-1]}_form.html"
            return render_template(form_template)
        else:
            return redirect(url_for('prompt_selection'))

@app.route('/worksheet', methods=['GET', 'POST'])
def worksheet():
    if request.method == 'POST':
        try:
            topic = request.form['topic']
            question_types = request.form['question_types']
            num_questions = int(request.form['num_questions'])
            delimiter = request.form['delimiter']
            session['worksheet_data'] = {
                'topic': topic,
                'question_types': question_types,
                'num_questions': num_questions,
                'formatting_delimiter': delimiter
            }
            return redirect(url_for('output'))
        except Exception as e:
            logging.error(f"Error in worksheet generation form submission: {e}", exc_info=True)
            return "An error occurred. Please try again."
    return render_template('worksheet_input_form.html')

@app.route('/output', methods=['GET', 'POST'])
def output():
    try:
        input_data = session.get('input_data', {})
        worksheet_data = session.get('worksheet_data', {})

        if request.method == 'POST' and request.form.get('download_word'):
            content = None  # Initialize content
            if session.get('content_type') == 'Lesson Plan':
                content = render_template(
                    'unit_plan.html',
                    unit_plan=session.get('content', {}),
                    grade_level=input_data.get('grade_level', ''),
                    num_students=input_data.get('number_of_students', ''),
                    state=input_data.get('state', '')
                )
            elif session.get('content_type') == 'Worksheet':
                content = render_template(
                    'worksheet_display.html',
                    content=session['content']
                )
            if content:
                output_path = html_to_docx(content, f"{session.get('content_type')}.docx")
                return send_file(output_path, as_attachment=True, download_name=f"{session.get('content_type')}.docx")

        if input_data:
            lesson_plan_dict, ordered_sections = lesson_planner.generate_lesson_plan(input_data)
            session['content_type'] = 'Lesson Plan'
            session['content'] = lesson_plan_dict
            return render_template(
                'unit_plan.html',
                unit_plan=lesson_plan_dict,
                grade_level=input_data.get('grade_level', ''),
                num_students=input_data.get('number_of_students', ''),
                state=input_data.get('state', '')
            )

        elif worksheet_data:
            worksheet_with_answers = generate_worksheet(
                worksheet_data['topic'],
                worksheet_data['num_questions'],
                worksheet_data['question_types'],
                worksheet_data['formatting_delimiter']
            )
            if worksheet_with_answers is None:
                return "Could not generate the worksheet. Please try again."
            session['content_type'] = 'Worksheet'
            session['content'] = worksheet_with_answers
            return render_template('worksheet_display.html', content=worksheet_with_answers)

        else:
            return "No data found for rendering. Please go back and try again."
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return "An error occurred. Please try again."

if __name__ == "__main__":
    app.run(debug=True)
