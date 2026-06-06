# app.py
# Flask page for showing the GradCafe SQL analysis.

from flask import Flask, render_template

from query_data import get_analysis_results


app = Flask(__name__)


@app.route("/")
def index():
    results = get_analysis_results()
    return render_template("analysis.html", results=results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)