import subprocess
import sys
import os

# Define the path to your app's directory
app_dir_path = r'Q:\AI\LPAPP\Lesson Planner App v 094(Back to Basics) Works!_WordDL - Simplified - Copy'

# Define the virtual environment path
venv_path = os.path.join(app_dir_path, 'venv')

# Create the virtual environment
subprocess.run([sys.executable, '-m', 'venv', venv_path])

# Path to the activate script
activate_script = os.path.join(venv_path, 'Scripts', 'activate')
if not os.path.exists(activate_script):  # For non-Windows systems
    activate_script = os.path.join(venv_path, 'bin', 'activate')

# Install dependencies from requirements.txt
requirements_file_path = os.path.join(app_dir_path, 'requirements.txt')
pip_install_command = [os.path.join(venv_path, 'Scripts', 'pip'), 'install', '-r', requirements_file_path]

# Execute the command to install dependencies
subprocess.run(pip_install_command)
