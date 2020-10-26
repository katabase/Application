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


@app.route("/Corpus")
def corpus():
    return render_template("pages/Corpus.html")