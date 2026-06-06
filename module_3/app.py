# app.py
# Flask page for showing the GradCafe SQL analysis.

import os
import subprocess
import sys

from flask import Flask, flash, redirect, render_template, url_for

from query_data import get_analysis_results


app = Flask(__name__)
app.secret_key = "module3-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(BASE_DIR, "scrape.lock")


@app.route("/")
def index():
    results = get_analysis_results()
    scraping_running = os.path.exists(LOCK_FILE)

    return render_template(
        "analysis.html",
        results=results,
        scraping_running=scraping_running
    )


@app.route("/pull-data", methods=["POST"])
def pull_data():
    if os.path.exists(LOCK_FILE):
        flash("A data pull is already running. Please wait before starting another one.")
        return redirect(url_for("index"))

    # The lock file tells the app that a scrape is currently running.
    with open(LOCK_FILE, "w", encoding="utf-8") as file:
        file.write("running")

    # Run pull_data.py in a separate process so the webpage does not freeze.
    subprocess.Popen(
        [sys.executable, "pull_data.py"],
        cwd=BASE_DIR
    )

    flash("Pull Data started. The app is checking GradCafe for recent records and will add new ones to the database.")
    return redirect(url_for("index"))


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    if os.path.exists(LOCK_FILE):
        flash("Analysis cannot be updated while Pull Data is running. Please try again shortly.")
        return redirect(url_for("index"))

    flash("Analysis updated using the most recent database results.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)