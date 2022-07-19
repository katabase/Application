from flask import jsonify, request
from lxml import etree
import json
import time
import glob
import re

from ..app import app
from ..utils.constantes import DATA
from ..utils.utils_classes import Match, APIGlobal, APIInvalidInput, XmlTei, Json



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
#
# custom http error and error handling
# https://medium.com/datasparq-technology/flask-api-exception-handling-with-custom-http-response-codes-c51a82a51a0f
# -------------------------------------------------------------------------------------------------------------------


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

    json return format:
    -------------------
    "CAT_id": {
        "key": "value"
    }

    xml return format:
    ------------------
    <list>
        <item n=""> <!-- n: number of the element -->
            <label><!-- title of the current item --></label>
            <term corresp="" ><!-- value ;--></term>
            <!-- corresp points to TEI//publicationStmt//row[position=1]/cell/@xml:id :
                 title of the search key -->
        </item>
    </list>
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
    else:
        req_name = req["name"]
        req_sell_date = req["sell_date"] if "sell_date" in req.keys() else None
        for k, v in data.items():
            if Match.match_cat(req_name, req_sell_date, v) is True:
                results[k] = v
    return results


def katapi_itm(req):
    """
    return all matching items (catalogue entries) from export_item.json

    json return format:
    -------------------
    "CAT_item_id": {
        "key": "value",
    }

    xml return format:
    ------------------
    <item n="80" xml:id="CAT_000146_e80">
       <num>80</num>
       <name type="author">Cherubini (L.),</name>
       <trait>
          <p>l'illustre compositeur</p>
       </trait>
       <desc>
          <term>L. a. s.</term>;<date>1836</date>,
          <measure type="length" unit="p" n="1">1 p.</measure>
          <measure unit="f" type="format" n="8">in-8</measure>.
          <measure commodity="currency" unit="FRF" quantity="12">12</measure>
        </desc>
    </item>

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
            results = XmlTei.get_item_from_id(req["id"])

        # if querying a name
        else:
            results = etree.Element("div", nsmap=XmlTei.ns)
            results.set("type", "search-results")
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
                        # add the item's id to the list of relevant ids
                        relevant.append(re.search(r"^CAT_\d+_e\d+", k)[0])
            relevant = set(relevant)  # deduplicate
            if len(relevant) > 0:
                results.append(etree.Element("list", nsmap=XmlTei.ns))
                for r in relevant:
                    results.append(XmlTei.get_item_from_id(r))  # add the relevant items to our tei
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
    errors = []  # keys to errors that happened
    incompatible_params = []  # list of incompatible parameters (for certain error messages)
    status_code = 200  # HTTP status code: 200 by default. custom codes will
    #                    be added if there are errors

    # =================== PROCESS THE USER INPUT =================== #
    req = dict(request.args)  # get arguments request

    # check the input (compulsory values provided + validity)
    if "format" in req.keys() and not re.search(r"^(tei|json)$", req["format"]):
        errors.append("format")
    if "level" in req.keys() and not re.search(r"^(cat_full|cat_stat|itm)$", req["level"]):
        errors.append("level")
    if "name" in req.keys() and "id" in req.keys():
        errors.append("name+id")
    if "id" in req.keys() and (
            "orig_date" in req.keys() or "sell_date" in req.keys() or "reconciliation" in req.keys()):
        errors.append("id_incompatible_params")
        if "sell_date" in req.keys():
            incompatible_params.append("sell_date")
        if "orig_date" in req.keys():
            incompatible_params.append("orig_date")
        if "reconciliation" in req.keys():
            incompatible_params.append("reconciliation")
    if "name" not in req.keys() and "id" not in req.keys():
        errors.append("no_name+id")
    if "id" in req.keys() and not re.match(r"^CAT_\d+(_e\d+_d\d+)?$", req["id"]):
        errors.append("id")
    if "sell_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["sell_date"]):
        errors.append("sell_date")
    if "orig_date" in req.keys() and not re.search(r"^\d{4}(-\d{4})?$",  req["orig_date"]):
        errors.append("orig_date")

    # look for invalid values specific to cat_stat and cat_full
    if "level" in req.keys() and req["level"] == "cat_stat":
        # check for invalid names
        if "name" in req.keys() and not re.search(r"^(LAC|RDA|LAV|AUC|OTH)$", req["name"]):
            errors.append("cat_stat+name")
        # check for general invalid data
        if "orig_date" in req.keys() or "reconciliation" in req.keys():
            errors.append("cat_stat_incompatible_params")
            if "orig_date" in req.keys():
                incompatible_params.append("orig_date")
            if "reconciliation" in req.keys():
                incompatible_params.append("reconciliation")
    if "level" in req.keys() and req["level"] == "cat_full" and (
            "name" in req.keys()
            or "sell_date" in req.keys()
            or "orig_date" in req.keys()
            or "reconciliation" in req.keys()):
        errors.append("cat_full_incompatible_params")
        if "name" in req.keys():
            incompatible_params.append("name")
        if "sell_date" in req.keys():
            incompatible_params.append("sell_date")
        if "orig_date" in req.keys():
            incompatible_params.append("orig_date")
        if "reconciliation" in req.keys():
            incompatible_params.append("reconciliation")
        if "format" in req.keys() and req["format"] != "tei":
            errors.append("cat_full_format")

    # =================== RUN THE USER QUERY =================== #
    # if there's an error, raise an http 422 error for which we have custom handling:
    # a custom response object with the user query, a status code and a response log
    # will be returned to the user.
    # the script stops if this error is encountered
    if len(errors) > 0:
        if "format" in req.keys() and not re.search("^(tei|json)$", req["format"]):
            req["format"] = "json"  # set default format
        raise APIInvalidInput(req, errors, incompatible_params)

    # if there's no error, proceed and try and retrieve results
    else:
        # define default behaviour
        if "level" in req.keys() and req["level"] == "cat_full" and "format" not in req.keys():
            req["format"] = "tei"
        if "level" not in req.keys():
            req["level"] = "itm"
        if "format" not in req.keys():
            req["format"] = "json"

        # if we're working at item level
        if req["level"] == "itm":
            response_body = katapi_itm(req)

        # if we're retrieving catalogue statistics
        elif req["level"] == "cat_stat":
            response_body = katapi_cat_stat(req)

        # if we're retrieving a full catalogue in xml-tei (req_level=="cat_full")
        else:
            response_body = katapi_cat_full(req["id"])
            if response_body is None:
                print("empty xml")

        # build the complete response (build_response functions build a body
        # from a template + call APIGlobal.set_headers to append headers to the body)
        # create the response body
        if req["format"] == "tei":
            response = XmlTei.build_response(req, response_body, status_code)

            # to check the output quality: save tei output to file
            with open("./test_xml_response.xml", mode="w+") as fh:
                tree = etree.fromstring(response.get_data())
                fh.write(str(etree.tostring(
                    tree, pretty_print=True, xml_declaration=True, encoding="utf-8"
                ).decode("utf-8")))
        else:
            response = Json.build_response(req, response_body, status_code)

    return response
