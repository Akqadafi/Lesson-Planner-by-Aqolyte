from flask import Flask, render_template, request
import lesson_planner

app = Flask(__name__)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        input_data = {
            'topic': request.form.get('topic'),
            'lesson_type': request.form.get('lesson_type'),
            'model_type': request.form.get('model_type'),
            'number_of_words': int(request.form.get('number_of_words')),
            'grade_level': int(request.form.get('grade_level')),
            'number_of_students': int(request.form.get('number_of_students')),
            'culture_group': request.form.getlist('culture_group'),
            'socioeconomic_level': request.form.get('socioeconomic_level'),
            'experiential_type': request.form.get('experiential_type'),
            'disabled': request.form.get('disabled') == 'True',
            'ell': request.form.get('ell') == 'True',
            'gifted': request.form.get('gifted') == 'True',
            'state': request.form.get('state'),
        }
        lesson_plan = lesson_planner.generate_lesson_plan(input_data)
        return render_template('unit_plan.html', unit_plan=lesson_plan)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)


