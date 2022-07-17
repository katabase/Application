from flask import jsonify, request
import re

from ..app import app

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
            "status_code": None,
            "vars": []
        },
        "results": {}
    }  # output json
    errors = []  # keys to errors that happened
    invalid_params = []  # list of invalid parameters (for certain error messages)

    # =================== PROCESS THE USER INPUT =================== #
    # get arguments request
    level = request.args.get("level")
    format = request.args.get("format")
    id = request.args.get("id")
    name = request.args.get("name")
    sell_date = request.args.get("sell_date")
    orig_date = request.args.get("orig_date")
    reconciliation = request.args.get("reconciliation")

    # check the the (compulsory values provided) + add queried vars to the output
    if not level:
        errors.append("level")
    else:
        output["head"]["vars"].append("level")
    if format:

        output["head"]["vars"].append("format")
    if id:
        output["head"]["vars"].append("id")
    if name:
        output["head"]["vars"].append("name")
    if sell_date:
        output["head"]["vars"].append("sell_date")
    if orig_date:
        output["head"]["vars"].append("orig_date")
    if reconciliation:
        output["head"]["vars"].append("reconciliation")

    if name and id:
        errors.append("name+id")
    if not name and not id:
        errors.append("no_name_or_id")
    if sell_date and not re.search(r"^\d{4}$", sell_date):
        errors.append("sell_date")
    if orig_date and not re.search(r"^\d{4}$", orig_date):
        errors.append("orig_date")
    if level == "cat" and (name or sell_date or orig_date or reconciliation is not None):
        errors.append("cat_invalid_params")
        if name is not None:
            invalid_params.append("name")
        if sell_date is not None:
            invalid_params.append("sell_date")
        if orig_date is not None:
            invalid_params.append("orig_date")
        if reconciliation is not None:
            invalid_params.append("reconciliation")

    # define default behaviour
    if format is None:
        format = "json"

    # =================== RUN THE USER QUERY =================== #
    # if there's an error, return it and stop the script. else, process and search for results
    if len(errors) > 0:
        output["results"], output["head"]["status_code"] = error_maker(errors, invalid_params)
    else:
        pass

    print(output)

    return jsonify(output)


def error_maker(errors: list, invalid_params: list):
    """
    build a custom json to return error messages

    return format: {"request parameter on which error happened": "error message"}
    :param errors:
    :param invalid_params: invalid research parameters
    :return: 
    """
    status_code = 400
    error_log = {
        "error_type": "invalid parameters or parameters combination",
        "error_description": {}
    }  # output dictionnary
    error_messages = {
        "level": "you must specify a request level matching: (itm|cat)",
        "format": "the format must match: (xml|json)",
        "id": r"if level=itm, id must match CAT_\d+_e\d+_d\d+ ; if level=cat, id must match CAT_\d+",
        "sell_date": r"the format must match: \d{4}",
        "orig_date": r"the format must match: \d{4}",
        "name+id": "you cannot provide both a name and an id",
        "no_name_or_id": "you must specify at least a name or an id",
        "cat_invalid_params": f"invalid parameters for level=cat: {str(invalid_params)}",
        "no_params": "no request parameters were provided"
    }

    # build a dictionnary of error messages
    for e in errors:
        error_log["error_description"][e] = error_messages[e]

    return error_log, status_code
