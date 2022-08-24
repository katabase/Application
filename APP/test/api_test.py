from urllib.parse import urlencode
from lxml import etree
from io import StringIO
import unittest
import json
import os


# modules inside ../APP must be imported from run, and thus be imported in run.py
from ..app import app
from ..utils.constantes import TEST
from ..utils.api_classes.representations_tei import XmlTei


# -----------------------------------------------------
# a bunch of tests for the API. understanding
# what's written here implies a proper knowledge
# of the API's parameters and possible values
#
# the tests also save examples of different return
# formats for different values of `level` parameter
# -----------------------------------------------------

class APITest(unittest.TestCase):
    """
    to run the tests we use Flask().test_client(), a Flask util
    which runs the app and lets you run queries as client.
    """
    url = "http://127.0.0.1:5000/katapi"  # the base url of the API

    def setUp(self):
        """
        set up the test fixture
        :return: None
        """
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        self.app = app.test_client()
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
        APIInvalidInput error and return to the client a http 422
        error.
        :return: None
        """
        # first test
        params = {
            "format": "xml",  # invalid value for format
            "api": "Durga Mahishasuraparini",  # unallowed param
            "id": "CAT_0001_e0001_d0001",  # allowed
            "sell_date": "200000",  # invalid value + incompatible with id
            "name": "Guyan Yin"  # incompatible with id
        }
        query = f"/katapi?{urlencode(params)}"

        # check the headers
        r = self.app.get(query)
        self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
        self.assertEqual(str(r.status_code), "422")  # check the http status code

        # check the content
        # loading the json allows to check that it's well-formed
        # + that the proper error messages are present
        error_keys = json.loads(r.get_data())["results"]["error_description"].keys()
        # check for errors that should be keys to response["results"]
        error_test = ["name+id", "sell_date", "unallowed_params", "id_incompatible_params", "format"]
        for e in error_test:
            self.assertIn(e, error_keys)

        # write output to file
        with open(f"{TEST}/api_output_examples/api_error.json", mode="w") as fh:
            json.dump(json.loads(r.get_data()), fh, indent=4)

        # second test
        params = {
            "format": "tei",  # allowed
            "sell_date": "2000?5000",  # invalid value
            }
        query = f"/katapi?{urlencode(params)}"

        # check the headers
        r = self.app.get(query)
        self.assertEqual(r.headers["Content-Type"], "application/xml; charset=utf-8")  # check the return type
        self.assertEqual(str(r.status_code), "422")  # check the http status code

        # check that the proper error keys are in the tei:body
        tree = etree.fromstring(r.get_data())
        XmlTei.xml_to_file(fpath=f"{TEST}/api_output_examples/api_error.xml", tree=tree)  # write to file

        error_test = ["sell_date", "no_name+id"]
        error_keys = tree.xpath(".//tei:body//tei:item/tei:label/text()", namespaces=XmlTei.ns)  # list of error keys
        for e in error_test:
            self.assertIn(e, error_keys)

        # check that the tei file is valid
        self.assertTrue(XmlTei.validate_tei(tree))

        return None

    def api_item(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="item",
        with "format"=="tei" and "json":
        - with params "name" + "sell_date" + "orig_date"
        - with params "name" + "sell_date"
        - with params "name" + "orig_date"
        - with params "name"
        - with params "id"
        :return: None
        """
        params = {
            "p1": {"level": "item", "name": "sévigné", "sell_date": "1800-1900", "orig_date": "1500-1800"},
            "p2": {"level": "item", "name": "sévigné", "sell_date": "1800-1900"},
            "p3": {"level": "item", "name": "sévigné", "orig_date": "1000-1000"},  # this one should return no result
            "p4": {"level": "item", "id": "CAT_000204_e108_d1"}
        }

        for k, v in params.items():
            with self.subTest(msg=f"error on {k}"):
                # test json format
                v["format"] = "json"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                if str(r.status_code) == "500":
                    print(r.get_data())  # to check the validity of error messages
                self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                r = json.loads(r.get_data())

                # write output to file
                if k == "p1":
                    # write output to file
                    with open(f"{TEST}/api_output_examples/api_item.json", mode="w") as fh:
                        json.dump(r, fh, indent=4)

                if k == "p3":  # check the empty return
                    self.assertEqual(r["results"], {})
                if k == "p4":  # check id parameter
                    self.assertEqual(
                        r["results"],
                        {"CAT_000204_e108_d1": {
                                "author": "BEETHOVEN",
                                "author_wikidata_id": "wd:Q255",
                                "date": "1820-05-31",
                                "desc": "\n                        L. s. \u00e0 M. M. Schlesinger, \u00e0 Berlin; Vienne, 31 mai 1820, 2 p.\n                        in-4, cachet",
                                "format": 4,
                                "number_of_pages": 2.0,
                                "price": None,
                                "sell_date": "1882",
                                "term": 9,
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
                    XmlTei.xml_to_file(fpath=f"{TEST}/api_output_examples/api_item.xml", tree=tree)  # write to file
                    t_item = etree.fromstring("""
                        <item n="108" xml:id="CAT_000204_e108">
                            <num type="lot">108</num>
                            <name type="author" ref="wd:Q255">BEETHOVEN (L. van)</name>
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
            "p1": {"level": "cat_stat", "name": "RDA", "sell_date": "1800-1900"},
            "p2": {"level": "cat_stat", "name": "RDA", "sell_date": "1000-1100"},  # this one should return no result
            "p3": {"level": "cat_stat", "name": "RDA"},
            "p4": {"level": "cat_stat", "id": "CAT_000362"}
        }

        for k, v in params.items():
            with self.subTest(msg=f"error on {k}"):
                # test json format
                v["format"] = "json"
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                if str(r.status_code) == "500":
                    print(r.get_data())
                self.assertEqual(r.headers["Content-Type"], "application/json")  # check the return type
                self.assertEqual(str(r.status_code), "200")  # check the http status code
                r = json.loads(r.get_data())

                # write output to file
                if k == "p1":
                    with open(f"{TEST}/api_output_examples/api_cat_stat.json", mode="w") as fh:
                        json.dump(r, fh, indent=4)

                if k == "p2":  # check the empty return
                    self.assertEqual(r["results"], {})
                if k == "p4":  # check the exact return
                    self.assertEqual(
                        r["results"],
                        {
                            "CAT_000362": {
                                "title": "Vente Jacques Charavay, ao\u00fbt 1875, n\u00ba 185",
                                "cat_type": "LAC",
                                "sell_date": "1875",
                                "item_count": 106,
                                "currency": "FRF",
                                "total_price_c": 1039,
                                "low_price_c": 1.27,
                                "high_price_c": 102.0,
                                "mean_price_c": 9.810188679245282,
                                "median_price_c": 4.59,
                                "mode_price_c": 3.06,
                                "variance_price_c": 194.2879773228907,
                                "high_price_items_c": {
                                    "CAT_000362_e27096": 102.0
                                }
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
                self.assertTrue(XmlTei.validate_tei(tree))

                if k == "p2":  # check the empty return
                    tei_div = etree.Element("div")
                    tei_div.set("type", "search-results")
                    self.assertEqual(
                        tree.xpath(".//tei:body//tei:div[@type='search-results']//*", namespaces=XmlTei.ns),
                        []
                    )  # check that an empty tei response is a tei:div with @type="search-results" and no children
                if k == "p4":  # check the "id" parameter

                    XmlTei.xml_to_file(fpath=f"{TEST}/api_output_examples/api_cat_stat.xml", tree=tree)  # write to file
                    t_item = etree.fromstring("""
                        <item ana="CAT_000362">
                            <label>CAT_000362</label>
                            <term key="title">Vente Jacques Charavay, août 1875, nº 185</term>
                            <term key="cat_type">LAC</term>
                            <term key="sell_date" type="date">1875</term>
                            <term key="item_count">106</term>
                            <term key="currency">FRF</term>
                            <term key="total_price_c" type="constant-price">1039</term>
                            <term key="low_price_c" type="constant-price">1.27</term>
                            <term key="high_price_c" type="constant-price">102.0</term>
                            <term key="mean_price_c" type="constant-price">9.810188679245282</term>
                            <term key="median_price_c" type="constant-price">4.59</term>
                            <term key="mode_price_c" type="constant-price">3.06</term>
                            <term key="variance_price_c" type="constant-price">194.2879773228907</term>
                            <term key="high_price_items_c" type="constant-price" ana="CAT_000362_e27096">102.0</term>
                        </item>
                    """, parser=XmlTei.parser)
                    r_item = tree.xpath(".//tei:body//tei:list/*[name()!='head']", namespaces=XmlTei.ns)
                    self.assertEqual(len(r_item), 1)  # assert there's only 1 tei:item in the result
                    self.assertTrue(XmlTei.compare_trees(r_item[0], t_item))

        return None

    def api_cat_full(self):
        """
        test that valid responses will be returned for
        different queries run with param "level"=="cat_stat"
        - one that will return a result
        - one that won't.
        :return: None
        """
        params = {
            "p1": {"id": "CAT_000300", "format": "tei", "level": "cat_full"},  # will return a result
            "p2": {"id": "CAT_000000", "format": "tei", "level": "cat_full"}   # won't return a result
        }
        for k, v in params.items():
            with self.subTest(msg=f"error on {k}"):

                # base tests
                query = f"/katapi?{urlencode(v)}"
                r = self.app.get(query)
                if str(r.status_code) == "500":
                    print(r.get_data())
                tree = etree.fromstring(r.get_data())
                self.assertEqual(str(r.status_code), "200")
                self.assertEqual(r.headers["Content-Type"], "application/xml; charset=utf-8")
                self.assertTrue(XmlTei.validate_tei(tree))

                # check the tei:table on both
                self.assertEqual(
                    [t.text for t in tree.xpath(".//tei:table/tei:row[1]/tei:cell", namespaces=XmlTei.ns)],
                    list(v.keys())
                )  # assert that the query keys are described inside the tei:table
                self.assertEqual(
                    [t.text for t in tree.xpath(".//tei:table/tei:row[2]/tei:cell", namespaces=XmlTei.ns)],
                    list(v.values())
                )  # assert that the query values are described inside the tei:table

                # p1 will return a complete catalogue (hard to verify the tei:body)
                # => check the teiHeader//tei:availability
                if k == "p1":
                    XmlTei.xml_to_file(fpath=f"{TEST}/api_output_examples/api_cat_full.xml", tree=tree)  # write to file
                    tei_availability = tree.xpath(".//tei:availability", namespaces=XmlTei.ns)[0]
                    self.assertEqual(
                        tei_availability.xpath("count(.//tei:p)", namespaces=XmlTei.ns), 4
                    )  # assert that there are 4 paragrams in the availability describing the request context
                    self.assertEqual(
                        tei_availability.xpath("count(./tei:p[tei:date/@when-iso])", namespaces=XmlTei.ns), 1
                    )  # assert there's a tei:date inside the tei:availability
                    self.assertEqual(
                        tei_availability.xpath("count(./tei:p[tei:ref])", namespaces=XmlTei.ns), 2
                    )  # assert that there are 2 links: for the mozilla documentation on http status code + for katabase

                # p2 will return no results => check the body
                if k == "p2":
                    tei_div = etree.Element("div")
                    tei_div.set("type", "search-results")
                    self.assertEqual(
                        tree.xpath(".//tei:body//tei:div[@type='search-results']//*", namespaces=XmlTei.ns),
                        []
                    )  # check that an empty tei response is a tei:div with @type="search-results" and no children

        return None


def suite():
    """
    build the suite of tests
    :return: suite
    """
    suite = unittest.TestSuite()
    suite.addTest(APITest("setUp"))
    suite.addTest(APITest("api_invalid_input"))
    suite.addTest(APITest("api_item"))
    suite.addTest(APITest("api_cat_stat"))
    suite.addTest(APITest("api_cat_full"))
    suite.addTest(APITest("tearDown"))
    return suite


def run():
    """
    run the tests
    :return: None
    """
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    result = runner.run(suite())
    stream.seek(0)
    print("test output", stream.read())
    os.remove("./save.xml")
    return None
