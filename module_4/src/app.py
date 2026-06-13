"""Flask application factory and routes for the GradCafe analytics app."""

from __future__ import annotations

import os
from typing import Callable

from flask import Flask, jsonify, render_template

from .pull_data import pull_and_insert
from .query_data import get_analysis_results

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_RESULTS = [
    {"question": "Analysis unavailable", "answer": "N/A", "sql": ""},
]


def create_app(
    config: dict | None = None,
    *,
    pull_func: Callable[..., dict] | None = None,
    query_func: Callable[..., list[dict]] | None = None,
) -> Flask:
    """Create a testable Flask app with injectable pull and query functions."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-secret-key"),
        DATABASE_URL=os.getenv("DATABASE_URL"),
        TESTING=False,
        PULL_IN_PROGRESS=False,
    )
    if config:
        app.config.update(config)

    app.extensions["pull_func"] = pull_func or pull_and_insert
    app.extensions["query_func"] = query_func or get_analysis_results

    @app.get("/")
    def index():
        return analysis()

    @app.get("/analysis")
    def analysis():
        results = app.extensions["query_func"](app.config.get("DATABASE_URL"))
        return render_template(
            "analysis.html",
            results=results or DEFAULT_RESULTS,
            scraping_running=app.config["PULL_IN_PROGRESS"],
        )

    @app.post("/pull-data")
    def pull_data_route():
        if app.config["PULL_IN_PROGRESS"]:
            return jsonify({"ok": False, "busy": True}), 409

        app.config["PULL_IN_PROGRESS"] = True
        try:
            summary = app.extensions["pull_func"](app.config.get("DATABASE_URL"))
        finally:
            app.config["PULL_IN_PROGRESS"] = False

        return jsonify({"ok": True, **summary}), 200

    @app.post("/update-analysis")
    def update_analysis():
        if app.config["PULL_IN_PROGRESS"]:
            return jsonify({"ok": False, "busy": True}), 409

        results = app.extensions["query_func"](app.config.get("DATABASE_URL"))
        return jsonify({"ok": True, "count": len(results)}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
