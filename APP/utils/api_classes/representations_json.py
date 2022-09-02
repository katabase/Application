from collections import OrderedDict

# -----------------------------------------------------
# functions to build json representations
# of the data and to build complete responses in those
# formats
#
# contains:
# - Json
# -----------------------------------------------------


class Json:
    """
    a bunch of tools to build a Json file for routes_api.py
    """
    taxonomy_cat_stat_keys = {
        "sell_date": "The year of the sale presented in the catalogue.",
        "title": "The title of the catalogue, and, by extension, of the sale.",
        "cat_type": "The type of catalogue (`LAD`|`LAV`|`RDA`|`AUC`|`OTH`)",
        "currency": "The currency of the prices returned. `FRF` corresponds to french francs.",
        "high_price_c": "The most expensive items in the catalogue, in constant 1900 francs. "
                        + "In the whole API, the `_c` suffix indicates that a price "
                        + "is expressed in constant 1900 francs.",
        "high_price_items_c": "The most expensive items in the catalogue. Each item's "
                              + "`@xml:id` is associated to its price, in constant francs.",
        "item_count": "The number of manuscripts for sale in the catalogue.",
        "low_price_c": "The least expensive item's price, in constant 1900 francs.",
        "mean_price_c": "The average price for a catalogue item, in constant 1900 francs.",
        "median_price_c": "The median price for a catalogue item, in constant francs.",
        "mode_price_c": "The mode price (the price that appears the most often in a catalogue)"
                        + "For an item, in constant francs.",
        "total_price_c": "The sum of each item's price, in constant francs",
        "variance_price_c": "The variance of the prices inside the catalogue.",
    }
    taxonomy_format = {
        "document_format_1": "In-folio",
        "document_format_2": "In-2°",
        "document_format_3": "In-3°",
        "document_format_4": "In-quarto",
        "document_format_8": "In-octavo",
        "document_format_12": "In-12",
        "document_format_16": "In-16",
        "document_format_18": "In-18",
        "document_format_32": "In-32",
        "document_format_40": "In-40",
        "document_format_48": "In-48",
        "document_format_64": "In-64",
        "document_format_101": "In-folio oblong",
        "document_format_102": "In-2° oblong",
        "document_format_103": "In-3° oblong",
        "document_format_104": "In-quarto oblong",
        "document_format_108": "In-octavo oblong",
        "document_format_112": "In-12 oblong",
        "document_format_116": "In-16 oblong",
        "document_format_118": "In-18 oblong",
        "document_format_132": "In-32 oblong",
        "document_format_140": "In-40 oblong",
        "document_format_148": "In-48 oblong",
        "document_format_164": "In-64 oblong"
    }
    taxonomy_term = {
        "document_term_1": "Apostille autographe signée | signed autograph apostilla",
        "document_term_2": "Pièce autographe signée | signed autograph document",
        "document_term_3": "Pièce autographe | signed autograph",
        "document_term_4": "Pièce signée | signed document",
        "document_term_5": "Billet autographe signé | signed autograph short document",
        "document_term_6": "Billet signé | signed short document",
        "document_term_7": "Lettre autographe signée | signed autograph letter",
        "document_term_8": "Lettre autographe | autograph letter",
        "document_term_9": "Lettre signée | signed letter",
        "document_term_10": "Brevet signé | signed certificate",
        "document_term_11": "Quittance autographe signée | signed ",
        "document_term_12": "Quittance signée | signed receipt",
        "document_term_13": "Manuscrit autographe | autograph manuscript",
        "document_term_14": "Chanson autographe | autograph song",
        "document_term_15": "Document (?) Autographe signé | signed autograph document (?)"
    }
    prefix_def = {
        "wd:": "https://www.wikidata.org/wiki/"
    }

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
                "query": req,  # user query: params and value
                "license": "Attribution 2.0 Generic (CC BY 2.0)",
                "encoding_desc": Json.build_encoding_desc(req)
            },
            "results": response_body  # results returned by the server (or error message)
        }  # response body

        # add necessary taxonomies, if any
        # encoding_desc = Json.build_encoding_desc(req)
        # if encoding_desc is not None:
        #     template["head"]["encoding_desc"] = encoding_desc

        response = APIGlobal.set_headers(response_body=template,
                                         response_format=req["format"],
                                         status_code=status_code)

        return response

    @staticmethod
    def build_encoding_desc(req: dict):
        """
        build an encoding description similar to a tei:encodingDesc
        can contain: `Json.prefix_def`, `Json.taxonomy_term`, `Json.taxonomy_format`
        that contains definitions of project-specific terms present in the response.
        encoding_desc is None if not needed.
        :param req: the client's request
        :return: encoding_desc, a dict containing the relevant data
        """
        if "level" in req.keys():
            if req["level"] == "item":
                encoding_desc = {
                    "prefix_definition": Json.prefix_def,
                    "taxonomy_term": Json.taxonomy_term,
                    "taxonomy_format": Json.taxonomy_format
                }
            elif req["level"] == "cat_stat":
                encoding_desc = Json.taxonomy_cat_stat_keys
            else:
                encoding_desc = None
        else:
            encoding_desc = None

        return encoding_desc


from .client_server import APIGlobal  # avoid circular imports
