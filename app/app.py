import os

from flask import Flask, render_template, request, redirect, url_for

from search_db import search
from config import Config


app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/help")
def show_help():
    return render_template("help.html")


@app.route("/results", methods=["get"])
def show_results():
    if not request.args:
        return redirect("/")

    results = search(request.args["query"])
    return render_template("results.html", query=request.args["query"], results=results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
