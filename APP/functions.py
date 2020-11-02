from lxml import etree
import os
import glob
import re

# Namespace definition :
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}


### FUNCTIONS USED TO OPEN XML FILES

def validate_id(id):
    """
    This function verifies that the id matches predefined filenames for security reasons.
    :param id: an id to be validate.
    :return: the validated id.
    """
    # Each file starts with 'CAT_' and digits.
    good_id = re.match("CAT_[0-9]+", id)
    return good_id[0]


def open_file(good_id):
    """
    This function opens the file that matches the id in oder to be able to parse it.
    :param good_id: an id created before
    :return: the matching file parsed by lxml
    """
    # !!!! Ajouter une condition pour renforcer la sécurité.
    file = "data/" + good_id + "_tagged.xml"
    actual_path = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(actual_path, file))


### FUNCTIONS USED TO GENERATE AN INDEX

def create_index():
    """
    This function creates an index of all catalogues to display.
    :param directory: a directory, the data directory to be specific.
    :return: a list of ids, one id per catalogue.
    """
    index = []
    # Only catalogues that have been tagged are displayed.
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(ROOT_DIR, "data", "*_tagged.xml"))
    for file in files:
        file_info = {}
        file_id = os.path.basename(file)
        file_id = file_id.replace("_tagged.xml", "")
        file_info["id"] = file_id
        index.append(file_info)
    # Alphanumeric order is used, index is sorted by id.
    index = sorted(index, key = lambda i: i['id'])
    return index


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
    item_list = []
    # Only items with an @xml:id are used.
    items = file.xpath('//tei:text//tei:item[@xml:id]', namespaces=ns)

    for item in items:
        # The dictionary 'data' will contain information of each entry.
        data = {}
        data["id"] = item.xpath('./@xml:id', namespaces=ns)[0]
        data["num"] = item.xpath('./@n', namespaces=ns)[0]

        # In case there is an author :
        if item.xpath('./tei:name[@type="author"]/text()', namespaces=ns):
            data["author"] = item.xpath('./tei:name[@type="author"]/text()', namespaces=ns)[0]
            if item.xpath('./tei:trait/tei:p/text()', namespaces=ns):
                trait = item.xpath('./tei:trait/tei:p/text()', namespaces=ns)[0]
                # Line breaks and duplicate whitespaces are removed.
                data["trait"] = (" ".join(trait.split()))

        # In case there is a note.
        if item.xpath('./tei:note/text()', namespaces=ns):
            note = item.xpath('./tei:note/text()', namespaces=ns)[0]
            data["note"] = (" ".join(note.split()))

        # In case there is a price.
        if item.xpath('./tei:measure[@commodity="currency"]', namespaces=ns):
            quantity = item.xpath('./tei:measure/@quantity', namespaces=ns)[0]
            unit = item.xpath('./tei:measure/@unit', namespaces=ns)[0]
            data["price"] = quantity + " " + unit

        # In case there is one (or more) desc(s).
        if item.xpath('./tei:desc', namespaces=ns):
            descs = item.xpath('./tei:desc', namespaces=ns)
            # Descs are contained in a list of dictionaries (one dictonary per desc).
            descs_list = []
            for desc in descs:
                # Desc information are contained in a dictionary.
                desc_dict = {}
                desc_dict["id"] = desc.xpath('./@xml:id', namespaces=ns)[0]
                # strip_tags is used to remove children tags of a tag, keeping the text.
                etree.strip_tags(desc, '{http://www.tei-c.org/ns/1.0}*')
                desc_dict["text"] = desc.text
                descs_list.append(desc_dict)
            data["desc"] = descs_list

        item_list.append(data)

    return item_list

create_index()