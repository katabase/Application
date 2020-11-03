from flask import render_template, request
from .app import app
from APP.main_functions import *
from .reconciliator import *

@app.route("/")
def home():
    return render_template("pages/Home.html")


@app.route("/About_us")
def about_us():
    return render_template("pages/AboutUs.html")


@app.route("/Search", methods=['GET', 'POST'])
def search():
    author = request.args.get('author')
    date = request.args.get('date')
    if author:
        return render_template('pages/search.html', results=reconciliator(author, date))
    return render_template('pages/search.html')


@app.route("/Index")
def index():
    return render_template("pages/Index.html", index=create_index())


@app.route("/View/<id>")
def view(id):
    file = validate_id(id)
    doc = open_file(file)
    return render_template("pages/View.html", metadata=get_metadata(doc), content=get_entries(doc))