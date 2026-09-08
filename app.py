import logging
import os
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_file, session, url_for
from flask_session import Session

import lesson_planner
from worksheet_generator import generate_worksheet


BASE_DIR = Path(__file__).resolve().parent
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
    SESSION_USE_SIGNER=True,
)
Session(app)


def _is_enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def html_to_docx(html_content: str) -> BytesIO:
    """Convert the rendered lesson or worksheet HTML to a Word document in memory."""
    document = Document()
    soup = BeautifulSoup(html_content, "html.parser")

    for element in soup.find_all(["h1", "h2", "h3", "p", "li", "pre"]):
        text = element.get_text(" ", strip=True)
        if not text:
            continue
        if element.name == "h1":
            document.add_heading(text, level=1)
        elif element.name == "h2":
            document.add_heading(text, level=2)
        elif element.name == "h3":
            document.add_heading(text, level=3)
        elif element.name == "li":
            document.add_paragraph(text, style="List Bullet")
        elif element.name == "pre":
            for line in text.splitlines():
                if line.strip():
                    document.add_paragraph(line.strip())
        else:
            document.add_paragraph(text)

    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output


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


@app.route("/choose")
def choose():
    return render_template("choose.html")


@app.route("/clear_cache")
def clear_cache():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/redirect_choice", methods=["POST"])
def redirect_choice():
    choice = request.form.get("choice")
    if choice == "lesson":
        session.clear()
        return redirect(url_for("prompt_selection"))
    if choice == "worksheet":
        session.clear()
        return redirect(url_for("worksheet"))
    return redirect(url_for("landing"))


@app.route("/prompt_selection", methods=["GET", "POST"])
def prompt_selection():
    if request.method == "POST":
        prompt = request.form.get("prompt", "")
        if prompt not in lesson_planner.SECTION_ORDER:
            return "Invalid lesson-plan type.", 400
        session.clear()
        session["prompt"] = prompt
        return redirect(url_for("home"))
    return render_template("prompt_selection.html")


@app.route("/home", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        input_data = request.form.to_dict()
        input_data["culture_group"] = request.form.getlist("culture_group")
        for field in ("disabled", "ell", "gifted"):
            input_data[field] = field in request.form
        input_data["prompt"] = session.get("prompt")
        if input_data["prompt"] not in lesson_planner.SECTION_ORDER:
            return redirect(url_for("prompt_selection"))
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
            session.clear()
            session["worksheet_data"] = {
                "topic": request.form["topic"].strip(),
                "question_types": request.form["question_types"],
                "num_questions": num_questions,
                "formatting_delimiter": request.form.get("delimiter", "----"),
            }
            return redirect(url_for("output"))
        except (KeyError, ValueError):
            app.logger.exception("Invalid worksheet form submission")
            return "Please check the worksheet fields and try again.", 400
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
        if request.method == "POST" and request.form.get("download_word"):
            rendered = _render_saved_content()
            content_type = session.get("content_type")
            if not rendered or content_type not in {"Lesson Plan", "Worksheet"}:
                return "No generated content is available for download.", 400
            return send_file(
                html_to_docx(rendered),
                as_attachment=True,
                download_name=f"{content_type}.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        saved = _render_saved_content()
        if saved:
            return saved

        input_data = session.get("input_data")
        worksheet_data = session.get("worksheet_data")

        if input_data:
            lesson_plan, _ordered_sections = lesson_planner.generate_lesson_plan(input_data)
            session["content_type"] = "Lesson Plan"
            session["content"] = lesson_plan
            return _render_saved_content()

        if worksheet_data:
            generated = generate_worksheet(
                worksheet_data["topic"],
                worksheet_data["num_questions"],
                worksheet_data["question_types"],
                worksheet_data["formatting_delimiter"],
            )
            session["content_type"] = "Worksheet"
            session["content"] = generated
            return _render_saved_content()

        return "No data found. Please return to the home page and try again.", 400
    except Exception:
        app.logger.exception("Unable to render generated content")
        return "The content could not be generated. Please try again.", 500


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=_is_enabled("FLASK_DEBUG"),
    )
