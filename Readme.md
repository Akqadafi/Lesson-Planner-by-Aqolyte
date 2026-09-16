# LPAPP

LPAPP is a Flask application that uses OpenAI to generate classroom lesson plans and worksheets. Teachers choose a lesson format, enter class context, and can download the generated material as a Word document.

## Features

- Six lesson-plan formats, including WebQuest/SAMR, concept-based, skills-based, scaffolded reading, and discovery learning
- Configurable grade, class size, standards, and learner context
- Short-answer, fill-in-the-blank, matching, mixed, and multiple-choice worksheets
- In-memory Word document export
- Server-side sessions so generated content is not stored in browser cookies

## Local setup

1. Install Python 3.11 or newer.
2. Run `setup_and_run.bat`, or create a virtual environment manually:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`.
4. Add a current OpenAI API key and a long, random Flask secret to `.env`.
5. Start the app:

   ```powershell
   python app.py
   ```

Then open <http://127.0.0.1:5000>.

The default model is `gpt-5.4-mini`. Set `OPENAI_MODEL` in `.env` to use another Responses API-compatible model.

## Tests

Tests mock the OpenAI boundary and do not make network requests:

```powershell
python -m unittest discover -s tests -v
```

## Security

Never commit `.env`, API keys, generated logs, or user data. See [SECURITY.md](SECURITY.md) for credential-rotation guidance.


## Modular lesson studio

Open `/builder/` to use a preset, customize a preset, or build from scratch.
The six existing instructional types remain available. Exploration now includes inquiry;
Skill Development includes explicit instruction. Backward Design and multi-session
Project-Based Learning are additional presets. Classroom, station-based and blended
learning are delivery options across approaches.

1. Choose a path, approach, sections, grade, session duration and classroom context.
2. Create an outline. This makes no AI request. Write sections yourself or generate them.
3. Save edits before rearranging, adding/removing or regenerating sections.
4. Review factual claims, standards, activities, exercise answers and timing.
5. Mark the draft teacher-reviewed and download Word. Any change clears that status.

Only one modular draft is stored in the browser's server-side session; this is not a
permanent lesson library. Download before replacing it. Separate tabs share the draft;
stale submissions are rejected. Opening legacy worksheets preserves the modular draft.

### What checks mean

AI output must be JSON containing every requested section exactly once with nonempty
text. Invalid output and API failures leave the previous draft intact. Input bounds,
CSRF protection on builder mutations, and revision checks guard the editing workflow.
The app flags missing objectives, assessment, answer keys and source context.

Source excerpts are teacher supplied. URLs are not fetched; citations, source quality,
standards alignment, factual accuracy, timing and answer correctness are NOT independently
verified. Prompt instructions request evidence and uncertainty labels but do not guarantee
compliance. Teacher review is an acknowledgement, not certification. Independent retrieval,
claim verification and mathematical answer validation remain future work.

The app is a local prototype: it has no authentication, persistent user library, deployment
rate limits, or independent educational-quality evaluation. Do not expose its paid generation
routes publicly without access and usage controls. Do not enter student identifying records.

Tests use mocked AI responses. Real-model output quality must be evaluated separately.


## Student practice handouts

After saving a lesson section, open Student handouts from the builder. Create an outline
with 1–20 exercises; enter questions and answers manually or generate them from the
selected section. Save before exporting separate student and teacher Word copies.
The print-friendly design supports 10–18 pt text, 1–8 writing lines and Letter/A4 paper.
Answers are stored separately and omitted from the student export; teachers must still
check that prompts themselves do not reveal answers. All content remains unverified.

A lesson content/configuration change flags the handout and pauses export until the teacher
regenerates it or acknowledges reviewing its alignment. One worksheet is stored within
the current session draft; starting a new lesson replaces it. Durable storage, additional
handout types, color themes, image uploads and automatic PDF downloads remain planned.
No additional graphics packages are required for this initial text-based workflow.
