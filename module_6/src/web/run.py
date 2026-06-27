"""Flask entry point for the Module 6 web service."""

from src.web.app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
