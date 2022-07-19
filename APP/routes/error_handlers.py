

from ..app import app
from ..utils.utils_classes import APIInvalidInput, APIInternalServerError, XmlTei, Json


# -----------------------------------------------------------------------------------------------------------------
# error handling for the API.
#
# about HTTP error handling in flask:
# https://medium.com/datasparq-technology/flask-api-exception-handling-with-custom-http-response-codes-c51a82a51a0f
# -----------------------------------------------------------------------------------------------------------------



@app.errorhandler(APIInternalServerError)
def handle_500(err, req):
    """
    handle an http 500 error (unexpected internal server error)
    :param err:
    :param req:
    :return:
    """
