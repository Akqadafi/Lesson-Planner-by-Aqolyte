import logging
import secrets
import os
from io import BytesIO
from pdf_export import convert_docx, PDFExportError
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from flask_session import Session
from request_guard import SessionRequestGuard

from openai_service import GenerationUnavailableError
from handouts import bp as handouts_blueprint
from builder import bp as builder_blueprint, csrf

import lesson_planner
from worksheet_generator import generate_worksheet, WorksheetFormatError


BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = (BASE_DIR / "VERSION").read_text(encoding="utf-8").strip()
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = Flask(__name__)
secret = os.getenv("FLASK_SECRET_KEY")
if not secret:
    raise RuntimeError("Missing FLASK_SECRET_KEY. Add it to .env (never commit .env).")

app.config.update(
    SECRET_KEY=secret,
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=str(BASE_DIR / "instance" / "sessions"),
    SESSION_PERMANENT=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    SESSION_USE_SIGNER=True,
    MAX_CONTENT_LENGTH=1024 * 1024,
)
Session(app)
app.wsgi_app = SessionRequestGuard(app.wsgi_app, app.config["SESSION_COOKIE_NAME"])
app.register_blueprint(builder_blueprint)
app.register_blueprint(handouts_blueprint)


@app.context_processor
def csrf_context():
    return {"csrf_token": csrf}


@app.before_request
def protect_legacy_forms():
    if request.method == "POST" and request.blueprint not in {"builder", "handouts"}:
        expected = session.get("builder_csrf", "")
        supplied = request.form.get("csrf", "")
        if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
            return "This form expired. Reload the form and try again. Your saved work is unchanged.", 400


def legacy_form(template, values=None, error=None):
    html = render_template(template)
    if values is None:
        return html
    soup = BeautifulSoup(html, 'html.parser')
    for field in soup.select('input[name], select[name], textarea[name]'):
        name = field['name']
        if field.get('type') in {'hidden', 'submit'}:
            continue
        submitted = values.getlist(name)
        if field.get('type') in {'checkbox', 'radio'}:
            field.attrs.pop('checked', None)
            if field.get('value', 'on') in submitted:
                field['checked'] = ''
        elif field.name == 'select':
            for option in field.find_all('option'):
                option.attrs.pop('selected', None)
                if option.get('value', option.text) in submitted:
                    option['selected'] = ''
            known = {option.get('value', option.text) for option in field.find_all('option')}
            for value in submitted:
                if value not in known:
                    option = soup.new_tag('option', attrs={'value':value, 'selected':''})
                    option.string = value + ' (choose a supported option)'
                    field.append(option)
        elif field.name == 'textarea':
            field.string = values.get(name, '')
        else:
            field['value'] = values.get(name, '')
    if error:
        alert = soup.new_tag('p', attrs={'role':'alert'})
        alert.string = error
        soup.find('form').insert_before(alert)
    return str(soup)


def clear_generation_session():
    # Moving between legacy tools must not discard an in-progress modular draft.
    for key in ('prompt', 'input_data', 'worksheet_data', 'content', 'content_type'):
        session.pop(key, None)


def _is_enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def html_to_docx(html_content: str) -> BytesIO:
    """Export block content in order, including native Word tables and lists."""
    from word_export import export_html
    return export_html(html_content)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"app": "LPAPP", "version": APP_VERSION}


@app.route("/")
def landing():
    return render_template("home.html")


@app.route("/second_landing")
def second_landing():
    return render_template("second_landing.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/products")
def products():
    return render_template("products.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


DESIGN_OPTIONS = {
    "workspace": "Teacher workspace",
    "guided": "Guided journey",
    "studio": "Studio first",
}


@app.route("/design-options/")
def design_options():
    return render_template(
        "design_options.html",
        current=None,
        options=DESIGN_OPTIONS,
        has_draft=bool(session.get("builder_draft")),
    )


@app.route("/design-options/<option>")
def design_option(option):
    if option not in DESIGN_OPTIONS:
        return "Design option not found.", 404
    return render_template(
        "design_options.html",
        current=option,
        options=DESIGN_OPTIONS,
        has_draft=bool(session.get("builder_draft")),
    )


@app.route("/choose")
def choose():
    return render_template("choose.html")


@app.route("/clear_cache", methods=["POST"])
def clear_cache():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/redirect_choice", methods=["POST"])
def redirect_choice():
    choice = request.form.get("choice")
    if choice == "lesson":
        clear_generation_session()
        return redirect(url_for("prompt_selection"))
    if choice == "worksheet":
        clear_generation_session()
        return redirect(url_for("worksheet"))
    return redirect(url_for("landing"))


@app.route("/prompt_selection", methods=["GET", "POST"])
def prompt_selection():
    if request.method == "POST":
        prompt = request.form.get("prompt", "")
        if prompt not in lesson_planner.SECTION_ORDER:
            return "Invalid lesson-plan type.", 400
        clear_generation_session()
        session["prompt"] = prompt
        return redirect(url_for("home"))
    return redirect(url_for("builder.index"))


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        input_data = {
            field: request.form.get(field, "")
            for field in (
                "topic", "number_of_words", "grade_level", "number_of_students",
                "prior_knowledge", "learner_supports", "state", "lesson_type",
            )
        }
        input_data["prompt"] = session.get("prompt")
        if input_data["prompt"] not in lesson_planner.SECTION_ORDER:
            return redirect(url_for("prompt_selection"))
        try:
            lesson_planner.validate_input(input_data)
        except ValueError as exc:
            return legacy_form(f"prompt{input_data['prompt'][-1]}_form.html", request.form, str(exc)), 400
        if session.get("content_type") == "Lesson Plan" and session.get("content"):
            session["previous_lesson"] = {key: session.get(key) for key in ("content", "content_type", "input_data")}
        session.pop("worksheet_data", None)
        session.pop("content", None)
        session.pop("content_type", None)
        session["input_data"] = input_data
        return redirect(url_for("output"))

    prompt = session.get("prompt")
    if prompt in lesson_planner.SECTION_ORDER:
        return render_template(f"prompt{prompt[-1]}_form.html")
    return redirect(url_for("prompt_selection"))


@app.route("/worksheet", methods=["GET", "POST"])
def worksheet():
    if request.method == "POST":
        try:
            num_questions = int(request.form["num_questions"])
            if not 1 <= num_questions <= 50:
                raise ValueError("Number of questions must be between 1 and 50.")
            if request.form.get("question_types") not in {"multiple_choice", "short_answer", "essay", "true_false", "matching", "Short Answer Questions", "Fill in the Blanks", "Matching", "Mix"}:
                raise ValueError("Invalid question type")
            if not request.form.get("topic", "").strip() or len(request.form["topic"]) > 300:
                raise ValueError("Invalid topic")
            if not 0 <= int(request.form.get("grade_level", "5")) <= 12:
                raise ValueError("Invalid grade")
            delimiter = request.form.get("delimiter", "----")
            if len(delimiter) > 20 or "\n" in delimiter or "\r" in delimiter:
                raise ValueError("Invalid delimiter")
            session.pop("input_data", None)
            session.pop("content", None)
            session.pop("content_type", None)
            session["worksheet_data"] = {
                "topic": request.form["topic"].strip(),
                "question_types": request.form["question_types"],
                "grade_level": int(request.form.get("grade_level", "5")),
                "num_questions": num_questions,
                "formatting_delimiter": request.form.get("delimiter", "----"),
            }
            return redirect(url_for("output"))
        except (KeyError, ValueError):
            app.logger.exception("Invalid worksheet form submission")
            return legacy_form("worksheet_input_form.html", request.form, "Please check the worksheet fields and try again."), 400
    return render_template("worksheet_input_form.html")


def _render_saved_content():
    content_type = session.get("content_type")
    content = session.get("content")
    if content_type == "Lesson Plan" and content:
        input_data = session.get("input_data", {})
        return render_template(
            "unit_plan.html",
            unit_plan=content,
            grade_level=input_data.get("grade_level", ""),
            num_students=input_data.get("number_of_students", ""),
            state=input_data.get("state", ""),
        )
    if content_type == "Worksheet" and content:
        return render_template("worksheet_display.html", content=content)
    return None


@app.route("/output", methods=["GET", "POST"])
def output():
    try:
        if request.method == "POST" and request.form.get("restore_previous"):
            previous = session.get("previous_lesson")
            if not previous:
                return "No previous lesson is available.", 400
            session.update(previous)
            session.pop("worksheet_data", None)
            return redirect(url_for("output"))
        if request.method == "POST" and (request.form.get("download_word") or request.form.get("download_pdf")):
            rendered = _render_saved_content()
            content_type = session.get("content_type")
            if not rendered or content_type not in {"Lesson Plan", "Worksheet"}:
                return "No generated content is available for download.", 400
            if request.form.get("download_pdf"):
                return send_file(convert_docx(html_to_docx(rendered)),as_attachment=True,download_name=f"{content_type}.pdf",mimetype="application/pdf")
            return send_file(
                html_to_docx(rendered),
                as_attachment=True,
                download_name=f"{content_type}.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        saved = _render_saved_content()
        if saved:
            return saved

        if request.method == "GET":
            return render_template("generation_ready.html")
        if request.form.get("generate") != "1":
            return "Choose an explicit generation or download action.", 400

        input_data = session.get("input_data")
        worksheet_data = session.get("worksheet_data")

        if input_data:
            lesson_plan, _ordered_sections = lesson_planner.generate_lesson_plan(input_data)
            session["content_type"] = "Lesson Plan"
            session["content"] = lesson_plan
            return redirect(url_for("output"))

        if worksheet_data:
            generated = generate_worksheet(
                worksheet_data["topic"],
                worksheet_data["num_questions"],
                worksheet_data["question_types"],
                worksheet_data["formatting_delimiter"],
                grade_level=worksheet_data.get("grade_level", 5),
            )
            session["content_type"] = "Worksheet"
            session["content"] = generated
            return redirect(url_for("output"))

        return "No data found. Please return to the home page and try again.", 400
    except PDFExportError as exc:
        return render_template("generation_error.html", message=str(exc), previous=False, export_error=True), 503
    except GenerationUnavailableError as exc:
        return render_template("generation_error.html", message=str(exc), previous=bool(session.get("previous_lesson"))), 503
    except (lesson_planner.LessonFormatError, WorksheetFormatError) as exc:
        return render_template("generation_error.html", message=str(exc), previous=bool(session.get("previous_lesson"))), 502
    except Exception:
        app.logger.exception("Unable to render generated content")
        return render_template("generation_error.html", message="Generation is unavailable. Your inputs have been kept. Please retry shortly.", previous=bool(session.get("previous_lesson"))), 503


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=_is_enabled("FLASK_DEBUG"),
    )
