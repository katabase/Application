from urllib.parse import urlencode
from werkzeug import Client
from pprint import pprint
from io import StringIO
from lxml import etree
import unittest
import requests
import json

# modules inside ../APP must be imported from run, and thus be imported in run.py
from ..app import app
from ..utils.api_classes import APIInvalidInput, XmlTei


# ----------------------------------------------
# a bunch of tests for the API. understanding
# what's written here implies a proper knowledge
# of the API's parameters and possible values
# ----------------------------------------------


class APITest(unittest.TestCase):
    """
    to run the tests we don't use requests, but werkzeug.Client,
    which simulates requests to a wsgi application while running
    this wsgi app (with requests we'd need to have 2 scripts:
    one to launch the app, the other to lauch the tests).
    werkzeug.Client returns TestResponse objects, similar to
    a flask Response object.
    see:
    - https://werkzeug.palletsprojects.com/en/2.1.x/test/
    - https://werkzeug.palletsprojects.com/en/2.1.x/test/#werkzeug.test.TestResponse
    """
    # client = Client(app)  # the client on which we'll run queries
    url = "http://127.0.0.1:5000/katapi"  # the base url of the API

    def setUp(self):
        """
        set up the test fixture
        :return:
        """
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["DEBUG"] = False
        self.app = app.test_client()
        self.client = Client(self.app)

    def tearDown(self):
        """
        tear down the test fixture
        :return:
        """
        pass

    def api_invalid_input(self):
        """
        test that, given certain parameters, the API will raise an
        APIInvalidInput error and return to the client an http 422
        error.
        :return: None
        """
        # ================== first test ================== #
        params = {
            "format": "xml",  # invalid value for format
            "api": "Durga Mahishasuraparini",  # unallowed param
            "id": "CAT_0001_e0001_d0001",  # allowed
            "sell_date": "200000",  # invalid value + incompatible with id
            "name": "Guyan Yin"  # incompatible with id
        }
        query = f"/katapi?{urlencode(params)}"

        # check the headers
        # self.assertRaises(APIInvalidInput, self.app.get(query))  # the proper error is raised
        r = self.app.get(query)
        self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
        self.assertEqual(str(r.status_code), "422")  # check the http status code

        # check the content
        # loading the json allows to check that it's well formed
        # + that the proper error messages are present
        error_keys = json.loads(r.get_data())["results"]["error_description"].keys()
        # check for errors that should be keys to response["results"]
        error_test = ["name+id", "sell_date", "unallowed_params", "id_incompatible_params", "format"]
        for e in error_test:
            self.assertIn(e, error_keys)

        # ================== second test ================== #
        params = {
            "format": "tei",  # allowed
            "sell_date": "2000?5000",  # incompatible with id
            }
        query = f"/katapi?{urlencode(params)}"

        # check the headers
        # self.assertRaises(APIInvalidInput, self.client.get("/katapi", json=params))  # the proper error is raised
        r = self.app.get(query)
        self.assertEqual(r.headers["Content-Type"], "application/xml; charset=utf-8")  # check the return type
        self.assertEqual(str(r.status_code), "422")  # check the http status code

        # check that the proper error keys are in the tei:body
        tree = etree.fromstring(r.get_data())
        error_test = ["sell_date", "no_name+id"]
        error_keys = tree.xpath(".//tei:body//tei:item/tei:label/text()", namespaces=XmlTei.ns)  # list of error keys
        for e in error_test:
            self.assertIn(e, error_keys)

        # check that the tei file is valid
        self.assertTrue(XmlTei.validate_tei(tree))

        return None

    def api_itm(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="itm",
        with "format"=="tei" and "json":
        - with params "name" + "sell_date" + "orig_date"
        - with params "name" + "sell_date"
        - with params "name" + "orig_date"
        - with params "name"
        - with params "id"
        :return: None
        """

    def api_cat_stat(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="cat_stat",
        with "format"=="tei" and "json":
        - with params "name" + "sell_date" + "orig_date"
        - with params "name" + "sell_date"
        - with params "name" + "orig_date"
        - with params "name"
        - with params "id"
        :return: None
        """

    def api_cat_full(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="cat_stat"
        - with params "id" (only allowed parameter for cat_stat)
        :return: None
        """


def suite():
    suite = unittest.TestSuite()
    suite.addTest(APITest("setUp"))
    suite.addTest(APITest("api_invalid_input"))
    suite.addTest(APITest("tearDown"))
    return suite


def run():
    # app.config.update({"TESTING": True})
    # app.run(port=5000, debug=True)
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    result = runner.run(suite())
    stream.seek(0)
    print("test output", stream.read())

