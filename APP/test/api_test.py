from urllib.parse import urlencode
from lxml import etree, objectify
from werkzeug import Client
from pprint import pprint
from io import StringIO
import unittest
import requests
import json
import re

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
        :return: None
        """
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        self.app = app.test_client()
        self.client = Client(self.app)
        return None

    def tearDown(self):
        """
        tear down the test fixture
        :return: None
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
        params = {
            "p1": {"level": "itm", "name": "sévigné", "sell_date": "1800-1900", "orig_date": "1500-1800"},
            "p2": {"level": "itm", "name": "sévigné", "sell_date": "1800-1900"},
            "p3": {"level": "itm", "name": "sévigné", "orig_date": "1000-1000"},  # this one should return no result
            "p4": {"level": "itm", "id": "CAT_000204_e108_d1"}
        }

        for k, v in params.items():
            with self.subTest(msg=f"error on {k}"):
                # test json format
                v["format"] = "json"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                r = json.loads(r.get_data())

                if k == "p3":  # check the empty return
                    self.assertEqual(r["results"], {})
                if k == "p4":  # check id parameter
                    self.assertEqual(
                        r["results"],
                        {"CAT_000204_e108_d1": {
                                "price": None,
                                "author": "BEETHOVEN",
                                "date": "1820-05-31",
                                "number_of_pages": 2.0,
                                "format": 4,
                                "term": 9,
                                "sell_date": "1882",
                                "desc": "L. s. \u00e0 M. M. Schlesinger, "
                                        "\u00e0 Berlin; Vienne, 31 mai 1820, 2 p. in-4, cachet"
                            }
                        }
                    )

                # test the tei format
                v["format"] = "tei"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                self.assertEqual(r.headers["Content-Type"], "application/xml; charset=utf-8")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                tree = etree.fromstring(r.get_data())
                XmlTei.xml_to_file(fpath="./save.xml", tree=tree)
                self.assertTrue(XmlTei.validate_tei(tree))

                if k == "p3":  # check the empty return
                    tei_div = etree.Element("div")
                    tei_div.set("type", "search-results")
                    self.assertEqual(
                        tree.xpath(".//tei:body//tei:div[@type='search-results']//*", namespaces=XmlTei.ns),
                        []
                    )  # check that an empty tei response is a tei:div with @type="search-results" and no children
                if k == "p4":  # check id parameter
                    t_item = etree.fromstring("""
                        <item n="108" xml:id="CAT_000204_e108">
                            <num type="lot">108</num>
                            <name type="author">BEETHOVEN (L. van)</name>
                            <trait>
                                <p>le grand compositeur de musique.</p>
                            </trait>
                            <desc xml:id="CAT_000204_e108_d1">
                                <term ana="#document_type_9">L. s.</term> 
                                à M. M. Schlesinger, à Berlin; Vienne, 
                                <date when="1820-05-31">31 mai 1820</date>, 
                                <measure type="length" unit="p" n="2">2 p.</measure> 
                                <measure type="format" unit="f" ana="#document_format_4">in-4</measure>
                                , cachet
                            </desc>
                            <note>Curieuse lettre sur ses ouvrages. Il leur accorde le droit de vendre ses 
                                compositions en Angleterre, y compris les airs écossais, aux conditions indiquées par lui. 
                                Il s'engage à leur livrer dans trois mois trois sonates pour le prix de 90 florins qu'ils 
                                ont fixé. C'est pour leur être agréable qu'il accepte un si petit honoraire. 
                                « Je suis habitué à faire des sacrifices, la composition de mes OEuvres 
                                n'étant pas faite seulement au point de vue du rapport des honoraires, mais 
                                surtout dans l'intention d'en tirer quelque chose de bon pour l'art.»
                            </note>
                        </item>
                        """, parser=XmlTei.parser)
                    r_item = tree.xpath(".//tei:body//tei:list/*[name()!='head']", namespaces=XmlTei.ns)
                    self.assertEqual(len(r_item), 1)  # assert there's only 1 tei:item in the result
                    self.assertTrue(XmlTei.compare_trees(r_item[0], t_item))

        return None

    def api_cat_stat(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="cat_stat",
        with "format"=="tei" and "json":
        - with params "name" + "sell_date" + "orig_date"
        - with params "name" + "sell_date"
        - with params "name"
        - with params "id"
        :return: None
        """
        params = {
            "p1": {"level": "cat_stat", "name": "RDA", "sell_date": "1800-1900", "orig_date": "1500-1800"},
            "p2": {"level": "cat_stat", "name": "RDA", "sell_date": "1000-1100"},  # this one should return no result
            "p3": {"level": "cat_stat", "name": "RDA"},
            "p4": {"level": "cat_stat", "id": "CAT_000153"}
        }

        for k, v in params.items():
            with self.subTest(msg=f"error on {k}"):
                # test json format
                v["format"] = "json"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                r = json.loads(r.get_data())

                if k == "p3":  # check the empty return
                    self.assertEqual(r["results"], {})

                # test the tei format
                v["format"] = "tei"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                self.assertEqual(r.headers["Content-Type"], "application/xml; charset=utf-8")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                tree = etree.fromstring(r.get_data())
                self.assertTrue(XmlTei.validate_tei(tree))

                if k == "p3":  # check the empty return
                    tei_div = etree.Element("div")
                    tei_div.set("type", "search-results")
                    self.assertEqual(
                        tree.xpath(".//tei:body//tei:div[@type='search-results']//*", namespaces=XmlTei.ns),
                        []
                    )  # check that an empty tei response is a tei:div with @type="search-results" and no children

        return None

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
    suite.addTest(APITest("api_itm"))
    suite.addTest(APITest("api_cat_stat"))
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
