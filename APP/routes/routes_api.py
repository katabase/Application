from flask import jsonify, request
import json
import re

from ..app import app
from ..utils.utils_classes import Compare, ErrorHandlers
from ..utils.constantes import DATA

# -------------------------------------------------------------------------------------------------------------------
# an API to send raw data to users
#
# code released under gnu gpl-3.0 license. developpers:
# - Paul Kervegan
#
# API documentation/tutorials:
# https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxiii-application-programming-interfaces-apis
# https://anderfernandez.com/en/blog/how-to-create-api-python/ (this one is good)
# https://roytuts.com/how-to-return-different-response-formats-json-xml-in-flask-rest-api/ (about XML return formats)
#
# about RESTulness:
# https://restfulapi.net/
# -------------------------------------------------------------------------------------------------------------------


@app.route("/katapi", methods=["GET"])
def katapi():
    r"""
    api the retrieve data from the catalogues in JSON or XML-TEI

    api parameters:
    ---------------
    global parameters:
    - level: the level of the query.
             values: "itm" => item, "cat" => catalogue
    - id: the identifier of the item or catalogue (depending on the value of level)
          values: a string corresponding to :
                  - if level=cat, a catalogue entry's @xml:id (CAT_\d+)
                  - if level=itm, an items @xml:id (CAT_\d+_e\d+_d\d+)
    - format: the return format
              values: "tei" / "json"

    parameters specific to level=itm
    - name: the tei:name being queried. use it only if id is none
            values: a string corresponding to the name searched for
    - sell_date: the date the manuscript is being sold.
                 values: \d{4} (aka a year in YYYY format)
    - orig_date: the original date of the manuscript
                 values: \d{4} (aka a year in YYYY format)
    - reconciliation: whether or not to return reconciliated items (aka, other values for the item)

    :return:
    """
    # =================== VAIRABLES =================== #
    output = {
        "head": {
            "status_code": 0,
            "vars": []
        },
        "results": {}
    }  # output json
    errors = []  # keys to errors that happened
    invalid_params = []  # list of invalid parameters (for certain error messages)
    results = {}  # to store the result of a query
    status_code = 0  # HTTP status code

    # =================== PROCESS THE USER INPUT =================== #
    # get arguments request
    req = dict(request.args)
    search_params = list(req.keys())
    # level = request.args.get("level")
    # format = request.args.get("format")
    # id = request.args.get("id")
    # name = request.args.get("name")
    # sell_date = request.args.get("sell_date")
    # orig_date = request.args.get("orig_date")
    # reconciliation = request.args.get("reconciliation")

    # check the input (compulsory values provided + validity) + add queried vars to the output
    output["head"]["vars"] = search_params
    if "level" not in req.keys():
        errors.append("level")
    elif not re.search(r"^(cat|itm)$", req["level"]):
        errors.append("level")
    if "name" in req.keys() and "id" in req.keys():
        errors.append("name+id")
    if "name" not in req.keys() and "id" not in req.keys():
        errors.append("no_name+id")
    if "sell_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["sell_date"]):
        errors.append("sell_date")
    if "orig_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["orig_date"]):
        errors.append("orig_date")
    if req["level"] == "cat" and (
            "name" in req.keys() 
            or "sell_date" in req.keys() 
            or "orig_date" in req.keys()
            or "reconciliation" in req.keys()):
        errors.append("cat_invalid_params")
        if req["name"] is not None:
            invalid_params.append("name")
        if req["sell_date"] is not None:
            invalid_params.append("sell_date")
        if req["orig_date"] is not None:
            invalid_params.append("orig_date")
        if req["reconciliation"] is not None:
            invalid_params.append("reconciliation")

    # define default behaviour
    if "format" not in req.keys():
        req["format"] = "json"

    # =================== RUN THE USER QUERY =================== #
    # if there's an error, return it and stop the script
    if len(errors) > 0:
        results, status_code = ErrorHandlers.error_maker(errors, invalid_params)

    # if there's no error, proceed and try and retrieve results
    else:
        # if we're working at item level
        if req["level"] == "itm":
            with open(f"{DATA}/json/export_item.json", mode="r") as fh:
                data = json.load(fh)

            # if querying an id
            if "id" in req.keys():
                if req["id"] in data.keys():
                    results[req["id"]] = data[req["id"]]

            # if we're querying a name
            else:
                # determine on which params to query in the json
                if "name" in req.keys() and "sell_date" in req.keys() and "orig_date" in req.keys():
                    mode = 0
                elif "name" in req.keys() and "orig_date" in req.keys():
                    mode = 1
                elif "name" in req.keys() and "sell_date" in req.keys():
                    mode = 2
                elif "name" in req.keys():
                    mode = 3

                # loop through all items and search results using the supplied parameters
                for k, v in data.items():
                    if v["author"] is not None:
                        if Compare.match_entry(req, v, mode) is True:
                            results[k] = v

    # build output
    output["head"]["status_code"] = status_code
    output["results"] = results

    return jsonify(output)
