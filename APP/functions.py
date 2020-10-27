from flask import url_for
from lxml import etree
import os
import re

# Namespace definition :
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}


### FUNCTIUNS USED TO OPEN XML FILES

def create_id(file):
    """
    This function creates an unique identifier for each file in the data directory.
    :param file: a file in the data directory.
    :return: the id
    """
    file_name = os.path.basename(file)
    # Each file starts with 'CAT_' and digits.
    id = re.match("CAT_[0-9]+", file_name)
    return id[0]


def open_file(id):
    """
    This function opens the file that matches the id to be able to parse it.
    :param id: an id created before
    :return: the matching file parsed by lxml
    """
    file = "data/" + id + "_tagged.xml"
    actual_path = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(actual_path, file))


### FUNCTIONS USED TO GET INFORMATIONS

def get_metadata(file):
    """
    This function retrieves metadata from the file.
    :param file: an XML file
    :return: a dictionary containing the metadata
    """
    metadata = {}
    metadata["title"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:title/text()', namespaces=ns)[0]
    metadata["num"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:num/text()', namespaces=ns)[0]
    metadata["editor"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:editor/text()', namespaces=ns)[0]
    metadata["publisher"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:publisher/text()', namespaces=ns)[0]
    metadata["pubPlace"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:pubPlace/text()', namespaces=ns)[0]
    metadata["date"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:date/text()', namespaces=ns)[0]

    metadata["encoder"] = file.xpath('//tei:titleStmt//tei:respStmt/tei:persName/text()', namespaces=ns)[0]

    return metadata


def get_entries(file):
    """
    This function retrieves entries from the file.
    :param file: an XML file
    :return: a dictionary of dictionaries containing the entries
    """
    entries = {}
    entries["id"] = file.xpath('//tei:text//tei:item[@xml:id]/@xml:id', namespaces=ns)

    for entry in entries:
        item = {}
        item["id"] = entry.xpath('//tei:')


id = create_id("data/CAT_000222_tagged.xml")
file = open_file(id)
dict = get_metadata(file)
print(dict)
