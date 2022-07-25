from flask import make_response, jsonify, Response
from werkzeug import exceptions
import logging
import os


from ..constantes import UTILS


# ----------------------------------------------------------
# classes related to http and client-server interaction
#
# at the moment, these are only used for the API
#
# contains:
# - APIGlobal
# - APIInvalidInput
# - APIInternalServerError
# - ErrorLog
# ----------------------------------------------------------


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
        create main logging instance for the API
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
        build a logger and dump an error message to a file
        __main__ == root logger defined in create_logger; __name__ = current module (routes_api.py)
        => this logger will inherit from the behaviour defined in root logger. could be used elsewhere
        see: https://stackoverflow.com/questions/50714316/how-to-use-logging-getlogger-name-in-multiple-modules
        :param stack: the error stack (list of functions that led to the error)
        :return: None
        """
        logger = logging.getLogger("__main__." + __name__)
        logger.setLevel(logging.ERROR)
        logger.error(stack)  # write full error message to log

        return None


from .file_formats import XmlTei, Json  # avoid circular imports