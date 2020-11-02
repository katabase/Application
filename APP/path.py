from flask import render_template
from .app import app
from .functions import *
from lxml import etree

@app.route("/")
def home():
    return render_template("pages/Home.html")


@app.route("/About_us")
def about_us():
    return render_template("pages/AboutUs.html")


@app.route("/Search")
def search():
    return render_template("pages/Search.html")


@app.route("/Index")
def index():
    return render_template("pages/Index.html", index=create_index())


@app.route("/View/<id>")
def view(id):
    file = validate_id(id)
    doc = open_file(file)
    return render_template("pages/View.html", metadata=get_metadata(doc), content=get_entries(doc))