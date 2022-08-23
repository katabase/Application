from flask import request
from io import StringIO
from lxml import etree
import traceback
import datetime
import json
import re

from ..app import app
from ..utils.constantes import DATA
from ..utils.api_classes.match import Match
from ..utils.api_classes.representations_tei import XmlTei
from ..utils.api_classes.representations_json import Json
from ..utils.api_classes.client_server import APIInvalidInput, APIInternalServerError, ErrorLog


# -------------------------------------------------------------------------------------------------------------------
# an API to send raw data to users. this API follows the REST standard where possible, especially the
# `stateless` and `uniform interface` conditions (which are the only ones under our control)
#
# code released under gnu gpl-3.0 license. developpers:
# - Paul Kervegan
#
# following the principle of separation of concerns, this API can be separarted into
# different elements and are also separated into different functions:
# - the interaction with the client, which happens in the `katapi()` function of this file
# - the interaction with the database, which also happens in this file
#   (`katapi_cat_full()`, `katapi_cat_stat()`, `katapi_itm()`)
# - the creation of representations, or views (aka, a whole response body in xml-tei or json)
#   to return to the client. see the `utils/classes/representations.py` file for those functions
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
    not as an etree.
    :param req_id: the id of the catalogue
    :return: results, a file object
    """
    found = True  # boolean indicating wether a file has been found, which will define the
    #               way the response object is built
    try:
        results = open(f"{DATA}/{req_id}.xml", mode="r", encoding="utf-8")
    except FileNotFoundError:
        results = etree.Element("div", nsmap=XmlTei.ns)
        results.set("type", "search-results")
        found = False
    return results, found


def katapi_cat_stat(req):
    """
    return statistical data for all matching catalogues from export_catalog.json

    workflow: first, we retrieve relevant data from `data/export_catalog.json`.
    then, if `format==tei`, we build a tei representation of those results.
    finally, we return the whole thing to `katapi()`

    json return format:
    -------------------
    {
        "CAT_id": {
            "key": "value"
        },
        # other results
    }

    xml return format:
    ------------------
    <div type="search-results">
        <list>
            <item @ana=""> <!-- ana: reference to an external source: the catalogue's id -->
                <label><!-- title of the current item --></label>
                <term key="" type="" ana="" n=""><!-- value ;--></term>
                <!--
                    @key: the key (name of the data inside the elt): "sell_date", "total_price_c"...
                    @type: the type of data (for numerals only): "date"|"constant_price"
                    @ana: when @key="high_price_items_c" only: the most expensive item's @xml:id
                -->
            </item>
        </list>
    </div>

    :param req: the user's request
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

    # if req["format"] == "tei", translate results to tei
    if req["format"] == "tei":
        results = XmlTei.build_response_teibody_cat_stat(data=results, req=req)
    return results


def katapi_itm(req):
    """
    return all matching items (catalogue entries) from export_item.json
    - if `format==json`, the json is build directly from reading the data
      and there is no need to build an extra representation
    - if `format==tei`, data is retrieved here and then a tei representation
      is built using `XmlTei.build_response_teibody_itm()`

    json return format:
    -------------------
    - if there are no results: {}
    - if there are results:
    "CAT_item_id": {
        "key": "value",
    }

    xml return format:
    ------------------
    - if there are no results:
    <div type="search-results"/>
    - if there are results:
    <div type="search-results">
        <list>
            <head>A descriptive list title</head>
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
        </list>
    </div>

    :param req: the user request from which we try to match entries
    :return: results, either a json or etree containing matching results
    """
    # json format
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

    # tei format
    else:
        # if querying an id, read the entry in the relevant xml file and put it in a list
        if "id" in req.keys():
            results = etree.Element("div", nsmap=XmlTei.ns)
            results.set("type", "search-results")
            data = [XmlTei.get_item_from_id(re.search(r"CAT_\d+_e\d+", req["id"])[0])]

        # if querying a name, build a list of relevant tei:items
        else:
            # build a list of relevant items's @xml:id from the json in order to retrieve
            # these elements in the xml-tei catalogues
            with open(f"{DATA}/json/export_item.json", mode="r") as fh:
                data = json.load(fh)
            relevant = []  # list of relevant @xml:id
            mode = Match.set_match_mode(req)  # determine on which params to query in the json
            for k, v in data.items():
                if v["author"] is not None:
                    if Match.match_item(req, v, mode) is True:
                        # add the item's id to the list of relevant ids
                        relevant.append(re.search(r"^CAT_\d+_e\d+", k)[0])
            relevant = set(relevant)  # deduplicate
            data = []

            # get the relevant tei:items from the tei catalogues
            for r in relevant:
                try:
                    data.append(XmlTei.get_item_from_id(r))
                except TypeError:
                    pass

        # pass the list of relevant tei:items to build the response body
        results = XmlTei.build_response_teibody_itm(data)
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

    - level:cat_stat
          |______format: a value corresponding to tei|json. defaults to json
          |______id: an identifier matching CAT_\d+.
          |          if id is provided, the only other allowed params are level and format
          |______name: a string matching ^(LAC|RDA|LAV|AUC|OTH)$. compulsory if no id is provided
          |______sell_date: a date matching \d{4}(-\d{4})?. optional

    - level:cat_full
          |______format: only tei is supported
          |______id: a catalogue identifier, matching CAT_\d+
                     if id is provided, the only other allowed params are level and format
    :return:
    """
    # =================== VARABLES =================== #
    timestamp = datetime.datetime.utcnow().isoformat()  # timestamp for when a request is sent
    errors = []  # keys to errors that happened
    allowed_params = ["level", "orig_date", "sell_date", "name", "format", "id"]  # list of all allowed parameters
    incompatible_params = []  # list of incompatible parameters (for certain error messages)
    status_code = 200  # HTTP status code: 200 by default. custom codes will
    #                    be added if there are errors

    # =================== PROCESS THE USER INPUT =================== #
    req = dict(request.args)  # get arguments requested by client
    unallowed_params = [p for p in req.keys() if p not in allowed_params]  # list of forbidden params
    #                                                                        (aka, parameters that are never allowed)

    # check the input (compulsory values provided + validity)
    if len(unallowed_params) > 0:
        errors.append("unallowed_params")
    if "format" in req.keys() and not re.search(r"^(tei|json)$", req["format"]):
        errors.append("format")
    if "level" in req.keys() and not re.search(r"^(cat_full|cat_stat|itm)$", req["level"]):
        errors.append("level")
    if "name" in req.keys() and "id" in req.keys():
        errors.append("name+id")
    if "id" in req.keys() and (
            "orig_date" in req.keys() or "sell_date" in req.keys()):
        errors.append("id_incompatible_params")
        if "sell_date" in req.keys():
            incompatible_params.append("sell_date")
        if "orig_date" in req.keys():
            incompatible_params.append("orig_date")
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
        if "name" in req.keys() and not re.search(
                r"^([Ll][Aa][Cc]|[Rr][Dd][Aa]|[Ll][Aa][Vv]|[Aa][Uu][Cc]|[Oo][Tt][Hh])$", req["name"]
        ):
            errors.append("cat_stat+name")
        # check for general invalid data
        if "orig_date" in req.keys():
            errors.append("cat_stat_incompatible_params")
            if "orig_date" in req.keys():
                incompatible_params.append("orig_date")
    if "level" in req.keys() and req["level"] == "cat_full" and (
            "name" in req.keys()
            or "sell_date" in req.keys()
            or "orig_date" in req.keys()):
        errors.append("cat_full_incompatible_params")
        if "name" in req.keys():
            incompatible_params.append("name")
        if "sell_date" in req.keys():
            incompatible_params.append("sell_date")
        if "orig_date" in req.keys():
            incompatible_params.append("orig_date")
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
        elif "format" not in req.keys():
            req["format"] = "json"
        raise APIInvalidInput(req, errors, incompatible_params, unallowed_params, timestamp)

    # if there's no error, proceed and try and retrieve results
    else:
        # if there's an error here, throwback an unexpected server error (http 500)
        try:
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
                response_body, found = katapi_cat_full(req["id"])

            # build the complete response (build_response functions build a body
            # from a template + call APIGlobal.set_headers to append headers to the body)
            if "level" in req and req["level"] == "cat_full":  # full catalogue in tei
                response = XmlTei.build_response(req, response_body, timestamp, status_code, found)
            elif req["format"] == "tei":  # other tei formats
                response = XmlTei.build_response(req, response_body, timestamp, status_code)
            else:  # json formats
                response = Json.build_response(req, response_body, status_code, timestamp)

        # raise an error that will build a valid json/tei response and return it to the user
        except:
            # prepare the error stack
            dummy1 = StringIO()  # dummy file object to write the stack to
            dummy2 = StringIO()  # dummy file object to write the exception to
            traceback.print_stack(file=dummy1)
            traceback.print_exc(file=dummy2)
            stack = dummy1.getvalue() + dummy2.getvalue()  # extract the string from stack
            stack = f"Error on {timestamp} \n" + stack

            ErrorLog.dump_error(stack)
            raise APIInternalServerError(req, timestamp)

    return response
