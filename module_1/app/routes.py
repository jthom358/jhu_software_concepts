from flask import Blueprint, render_template

# Blueprint used to organize main website routes
main = Blueprint('main', __name__)

@main.route('/')
def home():
    """Display homepage with biography and profile """
    return render_template('home.html', active_page='home')

@main.route('/projects')
def projects():
    """Display projects page with Module 1 project info"""
    return render_template('projects.html', active_page='projects')

@main.route('/contact')
def contact():
    """Display contact page with contact information"""
    return render_template('contact.html', active_page='contact')