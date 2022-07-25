from lxml import etree
import subprocess
import re
import os


from ..constantes import DATA, TEMPLATES


# --------------------------------------------------
# classes related to manipulating file fomats
# (creating, reading, checking...)
#
# at the moment, these are only used for the API
#
# contains:
# - XmlTei
# - Json
# --------------------------------------------------


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
    parser = etree.XMLParser(remove_blank_text=True)

    @staticmethod
    def get_item_from_id(item_id):
        """
        find a tei:item depending on the @xml:id provided in an xml file
        :param item_id: the item's desc's id, from export_item.json
        :return: tei_item, a tei:item with the relevant tei:desc
        """
        tei_item = None
        cat = re.search(r"^CAT_\d+", item_id)[0]
        try:
            with open(f"{DATA}/{cat}_tagged.xml", mode="r") as fh:
                tree = etree.parse(fh)
                tei_item = tree.xpath(
                    f"./tei:text//tei:item[@xml:id='{item_id}']",
                    namespaces=XmlTei.ns
                )[0]
        except FileNotFoundError:  # the xml file doesn't exist
            pass
        except IndexError:  # if no tei:item matches the 1st xpath().
            pass

        return tei_item

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
        XmlTei.xml_to_file(fpath=fpath, tree=tree)

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

    @staticmethod
    def strip_ns(tree):
        """
        strip all the namespaces and @xmlns attributes from tree
        :param tree: the tree to strip namespaces from
        :return: tree without namespaces
        """
        for el in tree.getiterator():
            if not isinstance(el, etree._Comment) or isinstance(el, etree._ProcessingInstruction):
                el.tag = etree.QName(el).localname  # strip namespaces
                etree.strip_attributes(el, "xmlns")
        etree.cleanup_namespaces(tree)
        tree = etree.fromstring(
            etree.tostring(tree).replace(b"xmlns=\"http://www.tei-c.org/ns/1.0\"", b"")
        , parser=XmlTei.parser)  # it's ugly but i lost my mind over removing the @xmlns at the top of the tree
        return tree

    @staticmethod
    def compare_trees(response_tree, validation_tree):
        """
        comparing trees (both as strings and elements) is HELL, so instead,
        we'll compare :
        - their tags (the element names in the trees)
        - their textual content (spaces in the text are considered unimportant
        cause it spaces mess up the comparison)
        - their attributes
        another possibility would be to use ETree.canonicalize, but i discovered it
        too late.

        :param response_tree: the tree returned from the API of which we'll check the validity
        :param validation_tree: a tree from our database that we'll use to check that response_tree is ok
        :return: same, a boolean indicating wether the trees are the same or not
        """
        response_tree = XmlTei.strip_ns(response_tree)  # strip the namespaces cause they make everything harder

        r_tags = [el.tag for el in response_tree.getiterator()]  # element names
        r_vals = []  # text inside elements
        r_attr = []  # element values
        for el in response_tree.getiterator():
            if el.text is not None:
                r_vals.append(re.sub(r"\s*", "", el.text))
            for name, value in el.items():
                r_attr.append({name: value})

        v_tags = [el.tag for el in validation_tree.getiterator()]
        v_vals = []
        v_attr = []
        for el in validation_tree.getiterator():
            if el.text is not None:
                v_vals.append(re.sub(r"\s*", "", el.text))
            for name, value in el.items():
                v_attr.append({name: value})

        if r_tags == v_tags and r_vals == v_vals and r_attr == v_attr:
            same = True
        else:
            if r_tags != v_tags:
                print(r_tags, "\n", v_tags)
            if r_vals != v_vals:
                print(r_vals, "\n", v_vals)
            if r_attr != v_attr:
                print(r_attr, "\n", v_attr)
            same = False
        return same

    @staticmethod
    def xml_to_file(fpath, tree):
        """
        write an lxml etree to file
        :param fpath: the file path to write the tree to
        :param tree: the tree to write to fpath
        :return: None
        """
        with open(fpath, mode="w+") as fh:
            fh.write(str(etree.tostring(
                tree, xml_declaration=True, encoding="utf-8"
            ).decode("utf-8")))
        return None

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
        build a response object with content in tei format:
        - build a tei document from a template:
          - a tei:teiHeader containing the request params
          - a tei:text/tei:body to store the results
        - append headers
        :param req: the user's request
        :param response_body: the response body, an lxml tree or string representation of tree
        :param status_code: the http status code
        :param timestamp: a timestamp in iso compliant format of when the katapi function was called
        :param found: a flag for req["level"] == "cat_full" indicating wether
                      a catalogue has been found for the id or not
        :return:
        """

        # if level isn't cat full, or if a cat hasn't been found for level==cat_full,
        # we build a full xml document, teiheader and all
        if "level" not in req.keys() \
                or (
                "level" in req.keys()
                and (
                        (req["level"] != "cat_full")
                        or (req["level"] == "cat_full" and found is False)
                )):
            with open(f"{TEMPLATES}/partials/katapi_tei_template.xml", mode="r") as fh:
                tree = etree.parse(fh, XmlTei.parser)

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
        # append paragraphs to tei:publicationStmt//tei:availability
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
            tei_availability.append(tei_p)

            # 2nd paragram = date
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "Query run on"
            tei_date = etree.Element("date", nsmap=XmlTei.ns)
            tei_date.set("when-iso", timestamp)
            tei_date.text = str(timestamp)
            tei_p.append(tei_date)
            tei_availability.append(tei_p)

            # 3rd paragrah: status code
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "Query ran with HTTP status code:"
            tei_ref = etree.Element("ref", nsmap=XmlTei.ns)
            tei_ref.set("target", f"https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/{status_code}")
            tei_p.append(tei_ref)
            tei_availability.append(tei_p)

            # 4rth paragraph: table
            tei_p = etree.Element("p", nsmap=XmlTei.ns)
            tei_p.text = "The current file has been retrieved and updated as a response to the query:"
            tei_query_table = XmlTei.build_tei_query_table(req, flag_cat_full=True)
            tei_p.append(tei_query_table)
            tei_p = XmlTei.pretty_print(tei_p)
            tei_availability.append(tei_p)
            tei_availability = XmlTei.pretty_print(tei_availability)

        XmlTei.xml_to_file(fpath="./save.xml", tree=tree)

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


from .client_server import APIInvalidInput, APIGlobal  # avoid circular imports
