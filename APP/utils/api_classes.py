from flask import make_response, jsonify, Response
from werkzeug import exceptions
from lxml import etree
import subprocess
import logging
import re
import os

from ..utils.constantes import DATA, TEMPLATES, UTILS
from ..app import app


# -------------------------------------------
# classes containing useful stuff for the api
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
        depending on whether req["sell_date"] and req["orig_date"] have been given by the user.
        this mode will be used to filter possible matching results
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
        # - if there's a date, filter by date: extract a year from entry["sell_date"]
        #   and try to match the dates. if they match, match is True. else false
        # - if there's no date, match is True
        if "cat_type" in entry.keys() and Match.compare(entry["cat_type"], req_name):
            match = True  # match is true by default. we add extra filtering by date below
            if req_date is not None \
                    and "sell_date" in entry.keys() \
                    and entry["sell_date"] is not None:
                match = Match.match_date(req_date, re.search(r"\d{4}", entry["sell_date"])[0])

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
        compare two strings to check if they're the same without punctuation,
        accented characters and capitals
        :param input: input string
        :param compa: string to compare input with
        :return:
        """
        punct = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-',
                 '+', '=', '{', '}', '[', ']', ':', ';', '"', "'", '|',
                 '<', '>', ',', '.', '?', '/', '~', '`']
        accents = {"é": "e", "è": "e", "ç": "c", "à": "a", "ê": "e",
                   "â": "a", "ô": "o", "ò": "o", "ï": "i", "ì": "i",
                   "ö": "o"}
        input = input.lower()
        compa = compa.lower()
        for p in punct:
            input = input.replace(p, "")
            compa = compa.replace(p, "")
        for k, v in accents.items():
            input = input.replace(k, v)
            compa = compa.replace(k, v)
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
    def build_response(req: dict, response_body: dict, status_code: int, timestamp: str):
        """
        build a response (json body + header) to store the API output to return to the user
        :param req: the user's request
        :param response_body: the body to which we'll add headers
        :param status_code: http status code
        :param timestamp: timestamp for when katapi was called
        :return: complete response object.
        """
        template = {
            "head": {
                "status_code": status_code,  # status code to be changed upon response completion
                "query_date": timestamp,  # the moment katapi is called (a query is run by a client)
                "query": req  # user query: params and value
            },
            "results": response_body  # results returned by the server (or error message)
        }  # response body

        response = APIGlobal.set_headers(response_body=template,
                                         response_format=req["format"],
                                         status_code=status_code)

        return response


class XmlTei:
    """
    a bunch of xml methods to build and manipulate XML for routes_api.py and api_test.py.
    """
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}  # tei namespace
    xmlid = {"id": "http://www.w3.org/XML/1998/namespace"}  # @xml:id namespace
    tei_rng = "https://tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng"  # odd in .rng to validate tei files

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
    def pretty_print(tree):
        """
        pretty print an etree object to send a ~pretty~ file to the user :3
        :param tree: the tree to pretty print
        :return: the pretty printed lxml etree object
        """
        tree = etree.tostring(tree, pretty_print=True)
        tree = etree.fromstring(tree)
        return tree

    @staticmethod
    def build_tei_query_table(req: dict, flag_cat_full=None):
        """
        build the table of queried data to append to the teiHeader
        :param req: the request
        :param flag_cat_full: flag to change an @xml:id to keep the document valid
        :return: tei_query_table
        """
        tei_query_table = etree.Element("table", nsmap=XmlTei.ns)
        tei_head = etree.Element("head", nsmap=XmlTei.ns)
        tei_head.text = "Query parameters"
        row1 = etree.Element("row", nsmap=XmlTei.ns)
        row2 = etree.Element("row", nsmap=XmlTei.ns)
        for k, v in req.items():
            # first, the parameters
            cell_k = etree.Element("cell", nsmap=XmlTei.ns)
            cell_k.text = k
            cell_k.set("role", "key")
            if k == "format" and flag_cat_full is True:
                cell_k.attrib["{http://www.w3.org/XML/1998/namespace}id"] = f"output_{k}"
            else:
                cell_k.attrib["{http://www.w3.org/XML/1998/namespace}id"] = k
            row1.append(cell_k)

            # then, the values mapped to the params
            cell_v = etree.Element("cell", nsmap=XmlTei.ns)
            cell_v.text = v
            cell_v.set("role", "value")
            cell_v.set("corresp", k)
            row2.append(cell_v)
        row1 = XmlTei.pretty_print(row1)
        row2 = XmlTei.pretty_print(row2)
        tei_query_table.append(tei_head)
        tei_query_table.append(row1)
        tei_query_table.append(row2)

        return tei_query_table

    @staticmethod
    def build_response(req: dict, response_body, timestamp: str, status_code=200, found=None):
        """
        for routes_api.py
        build a tei document from a template:
        - a tei:teiHeader containing the request params
        - a tei:text/tei:body to store the results
        :param req: the user's request
        :param response_body: the response body, an lxml tree or string representation of tree
        :param status_code: the http status code
        :param timestamp: a timestamp in iso compliant format of when the katapi function was called
        :param found: a flag for req["level"] == "cat_full" indicating wether
                      a catalogue has been found for the id or not
        :return:
        """

        # if level isn't cat full, we build a full xml document, teiheader and all
        if "level" not in req.keys() or (
                "level" in req.keys() and
                (req["level"] != "cat_full") or (req["level"] == "cat_full" and found is False)
        ):
            parser = etree.XMLParser(remove_blank_text=True)
            with open(f"{TEMPLATES}/partials/katapi_tei_template.xml", mode="r") as fh:
                tree = etree.parse(fh, parser)

            tei_query_table = XmlTei.build_tei_query_table(req)

            tree.xpath(".//tei:publicationStmt/tei:ab", namespaces=XmlTei.ns)[0].append(tei_query_table)

            # set the status code
            tei_status = tree.xpath(".//tei:publicationStmt//tei:ref", namespaces=XmlTei.ns)[0]
            tei_status.set("target", f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status_code}")
            tei_status.text = str(status_code)

            # set the date
            tei_date = tree.xpath(".//tei:publicationStmt//tei:date", namespaces=XmlTei.ns)[0]
            tei_date.set("when-iso", timestamp)
            tei_date.text = str(timestamp)

            # set the response body
            tei_body = tree.xpath(".//tei:body", namespaces=XmlTei.ns)[0]
            tei_body.append(response_body)

            tree = XmlTei.pretty_print(tree)

        # if a full tei catalogue has been found
        # append a paragraph to tei:publicationStmt//tei:availability
        # describing the whole context of the request: query, date, status code, producer
        elif "level" in req.keys() \
                and req["level"] == "cat_full" \
                and found is True:
            tree = etree.parse(response_body)
            tei_availability = tree.xpath(".//tei:publicationStmt//tei:availability", namespaces=XmlTei.ns)[0]

            # 1st paragrah = general context of the query
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "KatAPI query results. File created automatically by KatAPI, an API developped as part of the"
            tei_ref = etree.Element("ref", nsmap=XmlTei.ns)
            tei_ref.set("target", "https://katabase.huma-num.fr/")
            tei_ref.text = "Manuscript SaleS Catalogues project"
            tei_p.append(tei_ref)
            # tei_p = XmlTei.pretty_print(tei_p)
            tei_availability.append(tei_p)

            # 2nd paragram = date
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "Query run on"
            tei_date = etree.Element("date", nsmap=XmlTei.ns)
            tei_date.set("when-iso", timestamp)
            tei_date.text = str(timestamp)
            tei_p.append(tei_date)
            # tei_p = XmlTei.pretty_print(tei_p)
            tei_availability.append(tei_p)

            # 3rd paragrah: status code
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "Query ran with HTTP status code:"
            tei_ref = etree.Element("ref", nsmap=XmlTei.ns)
            tei_ref.set("target", f"https://github.com/katabase/Application/tree/main/APP/data{status_code}")
            tei_p.append(tei_ref)
            # tei_p = XmlTei.pretty_print(tei_p)
            tei_availability.append(tei_p)

            # 4rth paragraph: table
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "The current file has been retrieved and updated as a response to the query:"
            tei_query_table = XmlTei.build_tei_query_table(req, flag_cat_full=True)
            tei_p.append(tei_query_table)
            tei_p = XmlTei.pretty_print(tei_p)
            tei_availability.append(tei_p)
            tei_availability = XmlTei.pretty_print(tei_availability)

        # to check the output quality: save tei output to file
        with open("./api_xml_response.xml", mode="w+") as fh:
            fh.write(str(etree.tostring(
                tree, xml_declaration=True, encoding="utf-8"
            ).decode("utf-8")))

        response = APIGlobal.set_headers(etree.tostring(tree, pretty_print=True), req["format"], status_code)
        return response

    @staticmethod
    def build_error_teibody(error_log: dict, error_desc: str, req: dict):
        """
        build the tei:body containing an error message
        if there has been an error message
        :param error_log: the error log created by APIInvalidInput.error_logger()
        :param error_desc: the error description
        :param req: the user's request
        :return:
        """
        results = etree.Element("div", nsmap=XmlTei.ns)
        results.set("type", "error-message")

        # build the list element and header
        tei_list = etree.Element("list", nsmap=XmlTei.ns)
        head = etree.Element("head", nsmap=XmlTei.ns)
        head.text = APIInvalidInput.description
        tei_list.append(head)

        # add the errors to tei:items and append them to teilist
        for k, v in error_log["error_description"].items():
            itm = etree.Element("item", nsmap=XmlTei.ns)
            # add attributes to the tei:item:
            # - @type with k (the error type)
            # - @corresp with k if k is in the requested keys, to
            #   point towards the tei:header//tei:table containing
            #   the request.
            itm.set("ana", k)
            if k in req.keys():
                itm.set("corresp", k)

            # build the inside of the tei:item: a label containing the
            # error_log key + a desc containing the error_log value
            label = etree.Element("label", nsmap=XmlTei.ns)
            label.text = k
            desc = etree.Element("desc", nsmap=XmlTei.ns)
            desc.text = v

            # build the complete item and append it to the list
            itm.append(label)
            itm.append(desc)
            tei_list.append(itm)

        # add the list to the results and return them
        results.append(tei_list)
        results = XmlTei.pretty_print(results)
        return results

    @staticmethod
    def validate_tei(tree):
        """
        for api_test.py
        validate a tei returned by the API against the tei_all rng schema.
        to do so, we write the tei to a file, open a shell subprocess
        to run a pyjing (https://pypi.org/project/jingtrang/) validation
        of the file, check for errors and delete the file.
        :return: valid, a boolean: true if the file is valid, false if not
        """
        # save tei output to file to validate it against the schema
        fpath = "./api_xml_response.xml"
        with open(fpath, mode="w+") as fh:
            fh.write(str(etree.tostring(
                tree, xml_declaration=True, encoding="utf-8"
            ).decode("utf-8")))

        # validate the file against an rng schema
        out, err = subprocess.Popen(
            f"pyjing {XmlTei.tei_rng} {fpath}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        ).communicate()

        # check if there are no errors
        if len(out.splitlines()) == 0:
            valid = True
        else:
            valid = False

        os.remove(fpath)
        return valid


class APIGlobal:
    """
    for routes_api.py
    global methods for the API
    """
    @staticmethod
    def set_headers(response_body, response_format: str, status_code=200):
        """
        set the response headers for the API: append headers to the body (mimetype, statuscode)
        :param response_body: the body of the repsonse object for which we'll set the headers:
                              - format, esp. mimetype
                              - http status code
        :param response_format: the format to set the mimetype to (jsonify sets the mimetype automatically)
        :param status_code: the http status code for the response. defaults to 200
        :return: response, a complete response object with headers
        """
        if response_format == "json":
            response = make_response(jsonify(response_body), status_code)
        else:
            response = Response(
                response=response_body,
                status=status_code,
                mimetype="application/xml"
            )
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
    - __init__() instantiates an APIInvalidInput object by defining a description +
      builds a response object to return to the user. the response object is created
      as follows:
      - if req["format"] == "tei", a tei error body is built
      - (Json|XmlTei).build_template() builds a template for the response object
      - (Json|XmlTei).build_response() build a valid json|tei response object. this function
        calls another function APIGlobal.set_headers() that adds headers with the proper
        status code to the response object.
    - werkzeug kindly returns our custom error message, body and headers, to the client.

    """
    status_code = 422
    description = "Invalid parameters or parameters combination"

    def __init__(self,
                 req: dict,
                 errors: list,
                 incompatible_params: list,
                 unallowed_params: list,
                 timestamp: str):
        """
        a valid http response object to be handled by werkzeug
        :param req: the request on which the error happened (to pass to build_response)
        :param errors: the list of errors (keys of error_logger to pass to build_response())
        :param incompatible_params: the list of incompatible parameters
               (argument of error_logger to pass to build_response())
        :param unallowed_params: request parameters that are not allowed in the api
                                 (argument of error_logger to pass to build_response())
        """
        self.description = APIInvalidInput.description
        self.status_code = APIInvalidInput.status_code
        self.response = APIInvalidInput.build_response(req, errors, incompatible_params, unallowed_params, timestamp)

    @staticmethod
    def error_logger(errors: list, incompatible_params: list, unallowed_params: list):
        """
        for routes_api.py
        build a custom json describing the invalid input to return error messages to the user
         return format: {"request parameter on which error happened": "error message"}
        :param errors:
        :param incompatible_params: research parameters that are not compatible within each other
        :param unallowed_params: request parameters that are not allowed for the api
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
            "unallowed_params": f"Unallowed parameters for the API: {str(unallowed_params)}",
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
    def build_response(req, errors: list,
                       incompatible_params: list,
                       unallowed_params: list,
                       timestamp: str):
        """
        build a response object that werkzeug.HTTPException will pass to the client
        2 steps: first, build a response body in xml|tei; then, add headers
        :param req: the user's request
        :param errors: a list of errors (keys for error_logger)
        :param incompatible_params: a list of parameters that are not compatible with each other
        :param unallowed_params: request parameters that are not allowed in the api
        :param timestamp: a timestamp of when the function katapi was called
        :return: response, a custom valid response.
        """
        if req["format"] == "tei":
            response_body = XmlTei.build_error_teibody(
                error_log=APIInvalidInput.error_logger(errors, incompatible_params, unallowed_params),
                error_desc=APIInvalidInput.description,
                req=req
            )  # build response tei:body
            response = XmlTei.build_response(
                req=req,
                response_body=response_body,
                status_code=APIInvalidInput.status_code,
                timestamp=timestamp
            )  # build complete response object
        else:
            response = Json.build_response(
                req=req,
                response_body=APIInvalidInput.error_logger(errors, incompatible_params, unallowed_params),
                status_code=APIInvalidInput.status_code,
                timestamp=timestamp
            )  # build the response

        return response


class APIInternalServerError(exceptions.HTTPException):
    """
    for routes_api.py
    when the user query is valid but an unexpected error appears server side.
    process:
    --------
    - this error is raised because of an unexpected error on our side when using the API.
    - when this error is called, a the error is dumped in a log file so that we can
      access the call stack + detail on this error (see ErrorLog class below)
    - __init__() instantiates an APIInternalServerError object. the creation of this object
      builds a response object to return to the user. the response object is created as follows:
      - if req["format"] == "tei", a tei error body is built
      - (Json|XmlTei).build_template() builds a template for the response object
      - (Json|XmlTei).build_response() build a valid json|tei response object. this function
        calls another function APIGlobal.set_headers() that adds headers with the proper
        status code to the response object.
    - werkzeug kindly returns our custom error message, body and headers, to the client.

    """
    status_code = 500
    description = "Internal server error"

    def __init__(self, req: dict, timestamp: str):
        """
        build a response object that werkzeug.HTTPException will pass to the client
        2 steps: first, build a response body in xml|tei; then, add headers
        :param req: the user's request
        :param error_msg: the error message to dump in an error file
        :return: response, a custom valid response.
        """
        self.description = APIInternalServerError.description
        self.status_code = APIInternalServerError.status_code
        self.response = APIInternalServerError.build_response(req=req, timestamp=timestamp)

    @staticmethod
    def build_response(req: dict, timestamp: str):
        """
        for routes_api.py
        build a response in JSON|TEI describing the error.
        :param req: the user's request on which the errror happened
        :param timestamp: the timestamp of when katapi was called
        """
        error_log = {
            "__error_type__": "Internal server error",
            "error_description": {
                "error_message": "An internal server error happened. Open an issue on GitHib for us to look into it."
            }
        }  # output dictionnary
        if req["format"] == "tei":
            response_body = XmlTei.build_error_teibody(
                error_log=error_log,
                error_desc=APIInternalServerError.description,
                req=req
            )
            response = XmlTei.build_response(
                req=req,
                response_body=response_body,
                status_code=APIInternalServerError.status_code,
                timestamp=timestamp
            )  # build complete response object
        else:
            response = Json.build_response(
                req=req,
                response_body=error_log,
                status_code=APIInternalServerError.status_code,
                timestamp=timestamp
            )
        return response


class ErrorLog:
    """
    currently only for routes_api.py. could be extended to other funcs
    log errors in custom formats to file
    """
    logfile = f"{UTILS}/error_logs/error.log"

    @staticmethod
    def create_logger():
        """
        create logging instance
        configure the logger object (only used for katapi at this point)
        string formatting desc:
        - asctime: log creation time ;
        - levelname: error level (error, debug...) ;
        - module: python module on which error happened ;
        - message: actual error message
        :return: None
        """
        logfile = ErrorLog.logfile
        if not os.path.exists(logfile):
            with open(logfile, mode="w") as fh:
                fh.write("")  # create file if it doesn't exist
        root = logging.getLogger()  # create a root logger
        root.setLevel(logging.WARNING)  # set level to which an info will be logged. debug < warning < error
        root_filehandler = logging.FileHandler(ErrorLog.logfile)  # set handler to write log to file
        root_filehandler.setFormatter(
            logging.Formatter(r"%(asctime)s - %(levelname)s - %(module)s - %(message)s")
        )  # set the file formatting
        root_filehandler.setLevel(logging.WARNING)
        root.addHandler(root_filehandler)

        return None

    @staticmethod
    def dump_error(stack: str):
        """
        dump an error message to the log file:
        get the error stack, build it by adding a timestamp
        and combining it with the exception printing (print_exc).
        before the print_exc part, there may be stack frams from
        the current error logging into the log file.
        :param stack: the error stack (list of functions that led to the error)
        :return: None
        """
        # build a logger and log to file
        # __main__ == root logger defined in create_logger; __name__ = current module (routes_api.py)
        # => this logger will inherit from the behaviour defined in root logger. could be used elsewhere
        # see: https://stackoverflow.com/questions/50714316/how-to-use-logging-getlogger-name-in-multiple-modules
        logger = logging.getLogger("__main__." + __name__)
        logger.setLevel(logging.ERROR)
        logger.error(stack)  # write full error message to log

        return None
