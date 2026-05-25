from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register main blueprint containing the website page routes
    from app.routes import main
    app.register_blueprint(main)

    return app