Module 1: Personal Developer Website

Description:
This project is a personal site built using Flask, HTML, and CSS.
It includes a homepage, projects page, and contact page. The website displays
my biography, project information, and contact information.

Technologies Used:
Python 3.12
Flask
HTML
CSS
Git/GitHub

Project Structure:
run.py - Starts the Flask application.
requirements.txt - Lists the Python packages needed to run the project.
app/__init__.py - Creates and configures the Flask application.
app/routes.py - Defines the website routes.
app/templates/ - Contains the HTML templates.
app/static/css/style.css - Contains the CSS styling.
app/static/images/ - Contains website images.

How to Run:
1. Open a terminal.
2. Navigate to the module_1 folder:

   cd module_1

3. Create a virtual environment if one does not already exist:

   py -3.12 -m venv .venv

4. Activate the virtual environment in PowerShell:

   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1

5. Install the required packages:

   pip install -r requirements.txt

6. Run the Flask application:

   python run.py

7. Open a browser and go to:

   http://localhost:8080

Pages:
Home - Includes my name, position, biography, and profile image.
Projects - Includes details about the Module 1 personal website project.
Contact - Includes my email address and LinkedIn information.

Notes:
This project was developed for Module 1 of Modern Software Concepts in Python.
The website is intended to be updated throughout the course as additional Python
projects are completed.