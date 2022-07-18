from flask import jsonify, request
from lxml import etree
import json
import time
import glob
import re

from ..app import app
from ..utils.utils_classes import Match, ErrorHandlers
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
#
# about setting an xml mimetype and finetuning the response:
# https://stackoverflow.com/questions/29023035/how-to-create-xml-endpoint-in-flask
# -------------------------------------------------------------------------------------------------------------------


ns = {'tei': 'http://www.tei-c.org/ns/1.0'}  # tei namespace


def get_item_from_id(item_id):
    """
    find a tei:item depending on the @xml:id provided in an xml file
    :param item_id: the item's desc's id, from export_item.json
    :return: item, a tei:item with the relevant tei:desc
    """
    item = None
    cat = re.search(r"^CAT_\d+", item_id)[0]
    try:
        with open(f"{DATA}/{cat}_tagged.xml", mode="r") as fh:
            tree = etree.parse(fh)
            item = tree.xpath(
                f"./tei:text//tei:item[.//tei:desc/@xml:id='{item_id}']",
                namespaces=ns
            )[0]
            for desc in item.xpath(f".//tei:desc[@xml:id!='{item_id}']", namespaces=ns):
                desc.getparent().remove(desc)
    except FileNotFoundError:  # the xml file doesn't exist
        pass
    except IndexError:  # if no tei:item matches the 1st xpath().
        pass

    return item


def katapi_set_response(response, response_format: str):
    """
    set the response format for the API
    :param response: the response object for which we'll set the format, esp. mimetype
    :param response_format: the format to set the mimetype to
    :return: response
    """
    if response_format == "json":
        response = jsonify(response)
    else:
        response = app.response_class(response, mimetype="application/xml")
    return response


def katapi_itm(req):
    """
    return all matching items (catalogue entries) from export_item.json
    :param req: the user request from which we try to match entries
    :return:
    """
    if req["format"] == "json":
        with open(f"{DATA}/json/export_item.json", mode="r") as fh:
            data = json.load(fh)
        results = {}
        # if querying an id
        if "id" in req.keys():
            if req["id"] in data.keys():
                results[req["id"]] = data[req["id"]]

        # if we're querying a name
        else:
            # determine on which params to query in the json
            mode = Match.set_match_mode(req)

            # loop through all items and search results using the supplied parameters
            for k, v in data.items():
                if v["author"] is not None:
                    if Match.match_item(req, v, mode) is True:
                        results[k] = v
    else:

        # if querying an id, read the entry in the relevant xml file,
        # delete irrelevant tei:descs and save it
        if "id" in req.keys():
            results = get_item_from_id(req["id"])

        # if querying a name
        else:
            results = etree.fromstring(r"<TEI></TEI>")
            with open(f"{DATA}/json/export_item.json", mode="r") as fh:
                data = json.load(fh)
            relevant = []  # list of relevant @xml:id

            # determine on which params to query in the json
            mode = Match.set_match_mode(req)

            # build a list of relevant items based on the json.
            # retrieve the tei representation of all those items
            for k, v in data.items():
                if v["author"] is not None:
                    if Match.match_item(req, v, mode) is True:
                        relevant.append(k)  # add the item's id to the list of relevant ids
            for r in relevant:
                results.append(get_item_from_id(r))  # add the relevant items to our tei
    return results


def katapi_cat_full(req_id):
    """
    return a full tei catalogue from its id
    only iterables can be sent through WSGI => xml needs to be sent in a file with mimetype application/xml,
    not as a parsed xml.
    :param req_id: the id of the catalogue
    :return: results, a file object
    """
    try:
        results = open(f"{DATA}/{req_id}_tagged.xml", mode="r", encoding="utf-8")
    except FileNotFoundError:
        results = None
    return results


def katapi_cat_stat(req):
    """
    return statistical data for all matching catalogues from export_catalog.json
    :return:
    """
    results = {}
    with open(f"{DATA}/json/export_catalog.json", mode="r") as fh:
        data = json.load(fh)

    # if we're searching for an ID
    if "id" in req.keys():
        if req["id"] in data.keys():
            results[req["id"]] = data[req["id"]]

    # if we're searching for a name with an optional sell_date
    else :
        req_name = req["name"]
        req_sell_date = req["sell_date"] if "sell_date" in req.keys() else None
        for k, v in data.items():
            if Match.match_cat(req_name, req_sell_date, v) is True:
                results[k] = v
    return results


@app.route("/katapi", methods=["GET"])
def katapi():
    r"""
    api the retrieve data from the catalogues in JSON or XML-TEI

    api parameters:
    ---------------
    global parameters:
    - level: the level of the query.
             values: a string corresponding to:
                    - itm => item
                    - cat_full => complete catalogue (only works with format=tei)
                    - cat_data => statistical data on one/several catalogues (from export_catalog.json)
    - id: the identifier of the item or catalogue (depending on the value of level)
          values: a string corresponding to :
                  - if level=cat(_full|_stat), a catalogue entry's @xml:id (CAT_\d+)
                  - if level=itm, an items @xml:id (CAT_\d+_e\d+_d\d+)
    - format: the return format
              values: "tei" / "json"
    - name: the name of the entry/catalogue:
            - if level=itm, the tei:name being queried. use it only if id is none. only a last name will yield results
            - if level=cat_stat, the catalogue type (TEI//sourceDesc/bibl/@ana of the cats.). possible values:
                                 - 'LAC': Vente Jacques Charavay,
                                 - 'RDA': Revue des Autographes,
                                 - 'LAV': Catalogue Laveredet,
                                 - 'AUC': Auction sale
                                 - 'OTH': not yet in use in our dataset
    - sell_date: the date the manuscript is being sold or the date of a catalogue.
                 values: \d{4}(-\d{4})? (aka a year in YYYY format or a date range in YYYY-YYYY format)

    parameters specific to level=itm
    - orig_date: the original date of the manuscript
                 values: \d{4} (aka a year in YYYY format)
    - reconciliation: whether or not to return reconciliated items (aka, other values for the item)

    tl;dr - possible argument combinations:
    ---------------------------------------
    name or id are compulsory, format defaults to json, level defaults to itm. if id is provided, the
    only other params allowed are level and format.
    - level:itm
          |______format: a value corresponding to tei|json. defaults to json
          |______id: an identifier matching CAT_\d+_e\d+_d\d+.
          |          if id is provided, the only other allowed params are level and format
          |______name: any string corresponding to a last name. compulsory if no id is provided
          |______sell_date: a date matching \d{4}(-\d{4})?. optional
          |______orig_date: a date matching \d{4}(-\d{4})?. optional
          |______reconciliation: to be determined

    - level:cat_stat
          |______format: a value corresponding to tei|json. defaults to json
          |______id: an identifier matching CAT_\d+.
          |          if id is provided, the only other allowed params are level and format
          |______name: a string matching (). compulsory if no id is provided
          |______sell_date: a date matching \d{4}(-\d{4})?. optional

    - level:cat_full
          |______format: only tei is supported
          |______id: a catalogue identifier, matching CAT_\d+
                     if id is provided, the only other allowed params are level and format
    :return:
    """
    # =================== VARABLES =================== #
    response = {
        "head": {
            "status_code": 0,
            "query": {}
        },
        "results": {}
    }  # output json
    errors = []  # keys to errors that happened
    invalid_params = []  # list of invalid parameters (for certain error messages)
    status_code = 0  # HTTP status code

    # =================== PROCESS THE USER INPUT =================== #
    # get arguments request
    req = dict(request.args)

    # level = request.args.get("level")
    # format = request.args.get("format")
    # id = request.args.get("id")
    # name = request.args.get("name")
    # sell_date = request.args.get("sell_date")
    # orig_date = request.args.get("orig_date")
    # reconciliation = request.args.get("reconciliation")

    # check the input (compulsory values provided + validity)
    if "format" in req.keys() and not re.search(r"^(tei|json)$", req["format"]):
        errors.append("format")
    if "level" in req.keys() and not re.search(r"^(cat_full|cat_stat|itm)$", req["level"]):
        errors.append("level")
    if "name" in req.keys() and "id" in req.keys():
        errors.append("name+id")
    if "id" in req.keys() and (
            "orig_date" in req.keys() or "sell_date" in req.keys() or "reconciliation" in req.keys()):
        errors.append("id_invalid_params")
        if "sell_date" in req.keys():
            invalid_params.append("sell_date")
        if "orig_date" in req.keys():
            invalid_params.append("orig_date")
        if "reconciliation" in req.keys():
            invalid_params.append("reconciliation")
    if "name" not in req.keys() and "id" not in req.keys():
        errors.append("no_name+id")
    if "id" in req.keys() and not re.match(r"^CAT_\d+(_e\d+_d\d+)?$", req["id"]):
        errors.append("id")
    if "sell_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["sell_date"]):
        errors.append("sell_date")
    if "orig_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["orig_date"]):
        errors.append("orig_date")

    # invalid values specific to cat_stat and cat_full
    if "level" in req.keys() and req["level"] == "cat_stat":
        # check for invalid names
        if "name" in req.keys() and not re.search(r"^(LAC|RDA|LAV|AUC|OTH)$", req["name"]):
            errors.append("cat_stat+name")
        # check for general invalid data
        if "orig_date" in req.keys() or "reconciliation" in req.keys():
            errors.append("cat_stat_invalid_params")
            if "orig_date" in req.keys():
                invalid_params.append("orig_date")
            if "reconciliation" in req.keys():
                invalid_params.append("reconciliation")
    if "level" in req.keys() and req["level"] == "cat_full" and (
            "name" in req.keys()
            or "sell_date" in req.keys()
            or "orig_date" in req.keys()
            or "reconciliation" in req.keys()):
        errors.append("cat_full_invalid_params")
        if "name" in req.keys():
            invalid_params.append("name")
        if "sell_date" in req.keys():
            invalid_params.append("sell_date")
        if "orig_date" in req.keys():
            invalid_params.append("orig_date")
        if "reconciliation" in req.keys():
            invalid_params.append("reconciliation")
        if "format" in req.keys() and req["format"] != "tei":
            errors.append("cat_full_format")

    # =================== RUN THE USER QUERY =================== #
    # if there's an error, return it and stop the script
    if len(errors) > 0:
        response["head"]["query"] = req  # add queried data to the output
        invalid_params = list(set(invalid_params))
        results, status_code = ErrorHandlers.error_maker(errors, invalid_params)
        print(results)

    # if there's no error, proceed and try and retrieve results
    else:
        # define default behaviour
        if "level" in req.keys() and req["level"] == "cat_full" and "format" not in req.keys():
            req["format"] = "tei"
        if "level" not in req.keys():
            req["level"] = "itm"
        if "format" not in req.keys():
            req["format"] = "json"
        response["head"]["query"] = req  # add queried data + default behaviour to the output

        # if we're working at item level
        if req["level"] == "itm":

            results = katapi_itm(req)

        # if we're retrieving catalogue statistics
        elif req["level"] == "cat_stat":
            results = katapi_cat_stat(req)

        # if we're retrieving a full catalogue in xml-tei (req_level=="cat_full")
        else:
            results = katapi_cat_full(req["id"])
            if results is None:
                print("empty xml")

    # build output
    response["head"]["status_code"] = status_code
    # response["results"] = results  # proper version

    # build the response class (set mimetype...)
    # response = katapi_set_response(response, req["format"])
    response = katapi_set_response(results, req["format"])

    return response
