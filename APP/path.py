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
        results = reconciliator(author, date)
        for CAT in results["filtered_data"]:
            file = validate_id(CAT)
            doc = open_file(file)
            results["filtered_data"][CAT]["metadata"] = get_metadata(doc)
            results["filtered_data"][CAT]["text"] = get_entry(id_to_item(doc, CAT))
        return render_template('pages/search.html', results=results, author=author, date=date)
    return render_template('pages/search.html')


@app.route("/Index")
def index():
    index = create_index()
    return render_template("pages/Index.html", index=index)


@app.route("/View/<id>")
def view(id):
    file = validate_id(id)
    doc = open_file(file)
    return render_template("pages/View.html", metadata=get_metadata(doc), content=get_entries(doc))