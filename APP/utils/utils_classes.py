from flask import make_response, jsonify
from werkzeug import exceptions
from lxml import etree
import datetime
import re

from ..utils.constantes import DATA, TEMPLATES
from ..app import app

# -------------------------------------------
# classes containing useful stuff for the app
# -------------------------------------------


class Match:
    """
    comparison and matching methods
    """
    @staticmethod
    def set_match_mode(req):
        """
        for katapi.py
        set the matching mode when req["name"], req["level"]=="itm"
        depending on whether req["sell_date"] and req["orig_date"] have been given by the user
        :param req:
        :return:
        """
        if "sell_date" in req.keys() and "orig_date" in req.keys():
            mode = 0
        elif "orig_date" in req.keys():
            mode = 1
        elif "sell_date" in req.keys():
            mode = 2
        else:
            mode = 3
        return mode

    @staticmethod
    def match_date(req_date: str, entry_date: str):
        """
        for routes_api.py
        check whether 2 dates are equal or a date is contained in a date range
        :param req_date: the date (or date range) supplied by user, with format \d{4}(-\d{4})?
        :param entry_date: the date in the catalogue entry (a json)
        :return: match, a bool indicating wether entry_date matches with req_date
        """
        if re.match(r"\d{4}-\d{4}", req_date):
            req_date = req_date.split("-")
            match = int(req_date[0]) < int(entry_date) < int(req_date[1])
        else:
            match = int(req_date) == int(entry_date)

        return match

    @staticmethod
    def match_cat(req_name: str, req_date, entry: dict):
        r"""
        for routes_api.py
        try to match a catalogue in export_catalog.json based on a name and a date or date range
        :param req_name: the name (AUC|LAC|LAV|RDA|OTH) provided by the user
        :param req_date: a date or date range matching \d{4}(-\d{4})?
        :param entry: the json entry we're comparing name and date with
        :return: match, a bool indicating wether the entry matches with req_name and req_date
        """
        match = False
        # if name and cat_type match,
        # extract a year from entry["sell_date"] and try to match the dates.
        # if they match, match is True. else false
        if "cat_type" in entry.keys() and entry["cat_type"] == req_name:
            if req_date is not None and "sell_date" in entry.keys():
                match = Match.match_date(req_date, re.match(r"\d{4}", entry["sell_date"])[0])
        return match

    @staticmethod
    def match_item(req: dict, entry: dict, mode: int):
        """
        for routes_api.py
        try to match a dict entry using a list of dict params
        :param req: the user request on which to perform the match
        :param entry: the json entry (from export_item.json) to try a match with
        :param mode: the mode (an indicator of the supplied query params)
        :return:
        """
        match = False  # whether the entry matches with req or not
        name = None
        sell_date = None
        orig_date = None
        if "author" in entry.keys() and entry["author"] is not None:
            name = entry["author"].lower()
        if "sell_date" in entry.keys() and entry["sell_date"] is not None and entry["sell_date"] != "none":
            try:
                sell_date = re.match(r"\d{4}", entry["sell_date"])[0]
            except TypeError:
                sell_date = None
        if "date" in entry.keys() and entry["date"] is not None and entry["date"] != "none":
            try:
                orig_date = re.match(r"\d{4}", entry["date"])[0]
            except TypeError:
                orig_date = None

        if Match.compare(req["name"], name) is True:
            # filter by dates if client used dates in their query
            if mode == 0 and sell_date is not None and orig_date is not None:
                if Match.match_date(req["sell_date"], sell_date) is True and \
                        Match.match_date(req["orig_date"], orig_date) is True:
                    match = True
            elif mode == 1 and orig_date is not None:
                if Match.match_date(req["orig_date"], orig_date) is True:
                    match = True
            elif mode == 2 and sell_date is not None:
                if Match.match_date(req["sell_date"], sell_date) is True:
                    match = True
            elif mode == 3:
                match = True

        return match

    @staticmethod
    def compare(input, compa):
        """
        for routes_api.py
        compare two strings to check if they're the same without punctuation and
        capitals
        :param input: input string
        :param compa: string to compare input with
        :return:
        """
        punct = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-',
                 '+', '=', '{', '}', '[', ']', ':', ';', '"', "'", '|',
                 '<', '>', ',', '.', '?', '/', '~', '`']
        input = input.lower()
        compa = compa.lower()
        for p in punct:
            input = input.replace(p, "")
            compa = compa.replace(p, "")
        input = re.sub(r"\s+", " ", input)
        compa = re.sub(r"\s+", " ", compa)
        input = re.sub(r"(^\s|\s$)", "", input)
        compa = re.sub(r"(^\s|\s$)", "", compa)
        same = (input == compa)  # true if same, false if not
        return same


class Json:
    """
    a bunch of tools to build a Json file for routes_api.py
    """
    @staticmethod
    def build_response_body(req: dict, response_body: dict, status_code: int):
        """
        build a json body to store the API output to return to the user
        :param req: the user's request
        :return: template with the request added
        """
        template = {
            "head": {
                "status_code": status_code,  # status code to be changed upon response completion
                "query": req  # user query: params and value
            },
            "results": response_body  # results returned by the server (or error message)
        }  # output json

        return template

    # @staticmethod
    # def error_response(response_body, error_log: dict, status_code: int):
        """
        for error_handlers.py
        build a JSON response for a defined error (see classes below):
        append the error_log and status code to response_body and
        jsonify the response.
        return the response object to the error handler
        :param response_body: the response body
        :param error_log: a dict mapping to keys (search params) values (error messages)
        :param status_code: the http status code
        :return: the complete response object: response + headers
        """
    #     response_body["head"]["status_code"] = status_code
    #     response_body["results"] = error_log
    #     response = katapi_set_response(response_body, "json", status_code)

    #     return response


class XmlTei:
    """
    a bunch of xml methods to build and manipulate XML for routes_api.py.
    """
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}  # tei namespace
    xmlid = {"id": "http://www.w3.org/XML/1998/namespace"}  # @xml:id namespace

    @staticmethod
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
                    f"./tei:text//tei:item[@xml:id='{item_id}']",
                    namespaces=XmlTei.ns
                )[0]
        except FileNotFoundError:  # the xml file doesn't exist
            pass
        except IndexError:  # if no tei:item matches the 1st xpath().
            pass

        return item

    @staticmethod
    def build_response_body(req, response_body, status_code):
        """
        for routes_api.py
        build a tei document from a template:
        - a tei:teiHeader containing the request params
        - a tei:text/tei:body to store the results
        :param req:
        :return:
        """
        with open(f"{TEMPLATES}/partials/katapi_tei_template.xml", mode="r") as fh:
            tree = etree.parse(fh)

        # build the table of queried data
        el_query_table = tree.xpath(".//tei:publicationStmt//tei:table", namespaces=XmlTei.ns)[0]
        row1 = etree.Element("row", nsmap=XmlTei.ns)
        row2 = etree.Element("row", nsmap=XmlTei.ns)
        for k, v in req.items():
            # first, the parameters
            cell_k = etree.Element("cell", nsmap=XmlTei.ns)
            cell_k.text = k
            cell_k.set("role", "key")
            cell_k.attrib["{http://www.w3.org/XML/1998/namespace}id"] = k
            row1.append(cell_k)

            # then, the values mapped to the params
            cell_v = etree.Element("cell", nsmap=XmlTei.ns)
            cell_v.text = v
            cell_v.set("role", "value")
            cell_v.set("corresp", k)
            row2.append(cell_v)
        el_query_table.append(row1)
        el_query_table.append(row2)

        # set the status code
        el_status = tree.xpath(".//tei:publicationStmt//tei:ref", namespaces=XmlTei.ns)[0]
        el_status.set("target", f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status_code}")
        el_status.text = str(status_code)

        # set the date
        now = datetime.datetime.now().isoformat()
        el_date = tree.xpath(".//tei:publicationStmt//tei:date", namespaces=XmlTei.ns)[0]
        el_date.set("when-iso", now)
        el_date.text = now

        # set the response body
        el_body = tree.xpath(".//tei:body", namespaces=XmlTei.ns)[0]
        el_body.append(response_body)

        print(etree.tostring(tree))
        return tree

    # @staticmethod
    # def error_response():
        """
        for error_handlers.py
        build an XML-TEI response for a defined error (see classes below).
        :return:
        """


class APIGlobal:
    """
    for routes_api.py
    global methods for the API
    """
    @staticmethod
    def build_response_full(response_body, response_format: str, status_code=200):
        """
        set the response for the API: append headers to the body (mimetype, statuscode)
        :param response_body: the body of the repsonse object for which we'll set the headers:
                              - format, esp. mimetype
                              - http status code
        :param response_format: the format to set the mimetype to (jsonify sets the mimetype automatically)
        :param status_code: the http status code for the response. defaults to 200
        :return: response, a complete response object with headers
        """
        if response_format == "json":
            response = make_response(jsonify(response_body), status_code)
            print(type(response))
        else:
            response = app.response_class(response_body, mimetype="application/xml")
        return response


class APIInvalidInput(exceptions.HTTPException):
    """
    for routes_api.py
    the user request is valid syntaxically, but invalid semantically: it is impossible
    to process the request because the request contains invalid arguments, invalid values
    to valid arguments or invalid argument combination.

    http status code 422 specification
    ------------------------
    https://datatracker.ietf.org/doc/html/rfc4918#section-11.2

    process:
    --------
    - this error is raised because of invalid user input.
    - __init__() instantiates an APIInvalidInput object by defining a description
      and creating a response object. the response object is created as follows:
      - (Json|XmlTei).build_template() builds a template for the response object
      - error_logger() logs the errors in a dict
      - (Json|XmlTei).error_response() build a valid json|tei response object
    - werkzeug kindly returns our custom error message, body and headers, to the client.
    """
    def __init__(self, req: dict, errors: list, incompatible_params: list):
        """
        a valid http response object to be handled by werkzeug
        :param req: the request on which the error happened (to pass to build_response)
        :param errors: the list of errors (keys of error_logger to pass to build_response())
        :param incompatible_params: the list of incompatible parameters
               (argument of error_logger to pass to build_response())
        """
        self.description = "Invalid parameters or parameters combination"
        self.status_code = 422
        self.response = APIGlobal.build_response_full(
            response_body=APIInvalidInput.build_response_body(req, errors, incompatible_params),
            response_format=req["format"],
            status_code=self.status_code
        )  # create a full response object, with headers

    @staticmethod
    def error_logger(errors: list, incompatible_params: list):
        """
        for routes_api.py
        build a custom json describing the invalid input to return error messages to the user
         return format: {"request parameter on which error happened": "error message"}
        :param errors:
        :param incompatible_params: invalid research parameters
        :return:
        """
        error_log = {
            "__error_type__": "Invalid parameters or parameters combination",
            "error_description": {}
        }  # output dictionnary
        error_messages = {
            "level": "You must specify a request level matching: ^(itm|cat_full|cat_stat)$",
            "format": "The format must match: (tei|json)",
            "id": r"Invalid id. if level=itm, id must match CAT_\d+_e\d+_d\d+ ;"
                  + r"if level=cat(_full|_stat), id must match CAT_\d+",
            "sell_date": r"The format must match: \d{4}(-\d{4})?",
            "orig_date": r"The format must match: \d{4}(-\d{4})?",
            "name+id": "You cannot provide both a name and an id",
            "no_name+id": "You must specify at least a name or an id",
            "cat_stat+name": "When level:cat_stat, name must match: ^(LAC|RDA|LAV|AUC|OTH)$",
            "id_incompatible_params": f"Invalid parameters with parameter id: {str(incompatible_params)}",
            "cat_stat_incompatible_params": f"Invalid parameters for level=cat_stat: {str(incompatible_params)}",
            "cat_full_incompatible_params": f"Invalid parameters for level=cat_full: {str(incompatible_params)}",
            "cat_full_format": "The only valid format with level=cat_full is tei",
            "no_params": "No request parameters were provided"
        }
        # build a dictionnary of error messages
        for e in errors:
            error_log["error_description"][e] = error_messages[e]
        return error_log

    @staticmethod
    def build_response_body(req, errors: list, incompatible_params: list):
        """
        build a response object that werkzeug.HTTPException will pass to the client
        :return: response_body, a custom valid response body to which we'll add a header
        """
        if req["format"] == "tei":
            response_body = XmlTei.build_response_body(
                req=req,
                response_body=None,  # warning: error_logger returns JSON, we need to convert it to dict
                status_code=422
            )
        else:
            response_body = Json.build_response_body(
                req=req,
                response_body=APIInvalidInput.error_logger(errors, incompatible_params),
                status_code=422
            )  # build the response body
        print(response_body)
        return response_body


class APIInternalServerError(Exception):
    """
    for routes_api.py
    when the user query is valid but an unexpected error appears server side
    """
    statuscode = 500
    description = "Internal server error"
