@echo off
cd "Q:\AI\LPAPP\Lesson Planner App v 094(Back to Basics) Works!_WordDL - Simplified - Copy"

:: Create virtual environment
python -m venv venv

:: Activate virtual environment
call venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Run the Flask application
python app.py
