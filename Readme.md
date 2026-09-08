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
