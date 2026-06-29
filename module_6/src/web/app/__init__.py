"""Flask application factory and routes for the GradCafe analytics app."""

from __future__ import annotations

import os
from typing import Callable

from flask import Flask, jsonify, redirect, render_template, url_for

from src.web.publisher import publish_task
from src.worker.etl.query_data import get_analysis_results

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_RESULTS = [
    {"question": "Analysis unavailable", "answer": "N/A", "sql": ""},
]


def create_app(
    config: dict | None = None,
    *,
    query_func: Callable[..., list[dict]] | None = None,
    publish_func: Callable[..., None] | None = None,
) -> Flask:
    """Create a testable Flask app with injectable query and publish functions."""
    flask_app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    flask_app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-secret-key"),
        DATABASE_URL=os.getenv("DATABASE_URL"),
        TESTING=False,
    )
    if config:
        flask_app.config.update(config)

    flask_app.extensions["query_func"] = query_func or get_analysis_results
    flask_app.extensions["publish_func"] = publish_func or publish_task

    @flask_app.get("/")
    def index():
        return analysis()

    @flask_app.get("/analysis")
    def analysis():
        results = flask_app.extensions["query_func"](
            flask_app.config.get("DATABASE_URL")
        )
        return render_template(
            "analysis.html",
            results=results or DEFAULT_RESULTS,
        )

    @flask_app.post("/pull-data")
    def pull_data_route():
        try:
            flask_app.extensions["publish_func"](
                "scrape_new_data",
                {},
            )
        except Exception:  # pylint: disable=broad-exception-caught
            flask_app.logger.exception("Unable to queue scrape task")
            return jsonify(
                {
                    "ok": False,
                    "queued": False,
                    "message": "Task queue unavailable.",
                }
            ), 503

        return redirect(url_for("analysis"), code=303)

    @flask_app.post("/update-analysis")
    def update_analysis():
        try:
            flask_app.extensions["publish_func"](
                "recompute_analytics",
                {},
            )
        except Exception:  # pylint: disable=broad-exception-caught
            flask_app.logger.exception("Unable to queue analytics task")
            return jsonify(
                {
                    "ok": False,
                    "queued": False,
                    "message": "Task queue unavailable.",
                }
            ), 503

        return redirect(url_for("analysis"), code=303)

    return flask_app
