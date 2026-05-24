from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html', active_page='home')

@main.route('/projects')
def projects():
    return render_template('projects.html', active_page='projects')

@main.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')