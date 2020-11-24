from lxml import etree
import os
import glob
import re
import urllib.parse

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


def validate_entry_id(id):
    """
    This function verifies that the id matches predefined filenames for security reasons.
    :param id: an id to be validate.
    :return: the validated id.
    """
    # Each file starts with 'CAT_' and digits.
    good_id = re.match("CAT_[0-9]+_e[0-9]+", id)
    return good_id[0]


def open_file(good_id):
    """
    This function opens the file that matches the id in oder to be able to parse it.
    :param good_id: an id created before
    :return: the matching file parsed by lxml
    """
    file = "data/" + good_id + "_tagged.xml"
    actual_path = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(actual_path, file))


### FUNCTIONS USED TO GENERATE AN INDEX

def create_index():
    """
    This function creates an index of all catalogues to display.
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
        # The main title is used.
        opened_file = open_file(file_id)
        metadata = get_metadata(opened_file)
        file_info["title"] = metadata["main_title"]
        file_info["date"] = metadata["date"]
        if 'publisher' in metadata:
            file_info["publisher"] = metadata["publisher"]
        index.append(file_info)
    # Alphanumeric order is used, index is sorted by id.
    index = sorted(index, key=lambda i: i['id'])
    return index


### FUNCTIONS USED TO GET INFORMATIONS

def get_metadata(file):
    """
    This function retrieves metadata from the file.
    :param file: an XML file
    :return: a dictionary containing the metadata
    """
    metadata = {}
    # Information about the printed publication.
    if file.xpath('//tei:titleStmt//tei:title/text()', namespaces=ns):
        metadata["main_title"] = file.xpath('//tei:titleStmt//tei:title/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:title/text()', namespaces=ns):
        metadata["title"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:title/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:num/text()', namespaces=ns):
        metadata["num"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:num/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:editor/text()', namespaces=ns):
        metadata["editor"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:editor/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:publisher/text()', namespaces=ns):
        metadata["publisher"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:publisher/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:pubPlace/text()', namespaces=ns):
        metadata["pubPlace"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:pubPlace/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:date/text()', namespaces=ns):
        metadata["date"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:date/text()', namespaces=ns)[0]
    if file.xpath('//tei:sourceDesc//tei:bibl/tei:date/@when', namespaces=ns):
        metadata["norm_date"] = file.xpath('//tei:sourceDesc//tei:bibl/tei:date/@when', namespaces=ns)[0]

    # Information about the digital publication.
    if file.xpath('//tei:titleStmt//tei:respStmt/tei:persName/text()', namespaces=ns):
        metadata["encoder"] = file.xpath('//tei:titleStmt//tei:respStmt/tei:persName/text()', namespaces=ns)[0]
    if file.xpath('//tei:publicationStmt//tei:publisher/text()', namespaces=ns):
        metadata["XML_publisher"] = file.xpath('//tei:publicationStmt//tei:publisher/text()', namespaces=ns)[0]
    if file.xpath('//tei:publicationStmt//tei:licence/text()', namespaces=ns):
        metadata["licence"] = file.xpath('//tei:publicationStmt//tei:licence/text()', namespaces=ns)[0]

    # Information about the auction.
    if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]', namespaces=ns):
        if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:addrLine/text()', namespaces=ns):
            metadata["auction_place"] = file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:addrLine/text()', namespaces=ns)[0]
        if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="auctioneer"]/text()', namespaces=ns):
            metadata["auctioneer"] = file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="auctioneer"]/text()', namespaces=ns)
        if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="expert"]/text()', namespaces=ns):
            metadata["expert"] = file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="expert"]/text()', namespaces=ns)
        if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="collector"]/text()', namespaces=ns):
            metadata["collector"] = file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:persName[@type="collector"]/text()', namespaces=ns)
        if file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:date/text()', namespaces=ns):
            metadata["auction_date"] = file.xpath('//tei:sourceDesc//tei:event[@type="auction"]//tei:date/text()', namespaces=ns)[0]

    # Information about the witness(es)
    if file.xpath('//tei:sourceDesc//tei:listWit//tei:msDesc', namespaces=ns):
        witnesses = file.xpath('//tei:sourceDesc//tei:listWit/tei:witness', namespaces=ns)
        witnesses_list = []
        for witness in witnesses:
            witness_dict = {}
            if witness.xpath('.//tei:country/text()', namespaces=ns):
                witness_dict["ms_country"] = witness.xpath('.//tei:country/text()', namespaces=ns)[0]
            if witness.xpath('.//tei:settlement/text()', namespaces=ns):
                witness_dict["ms_settlement"] = witness.xpath('.//tei:settlement/text()', namespaces=ns)[0]
            if witness.xpath('.//tei:repository/text()', namespaces=ns):
                witness_dict["ms_repository"] = witness.xpath('.//tei:repository/text()', namespaces=ns)[0]
            if witness.xpath('.//tei:institution/text()', namespaces=ns):
                witness_dict["ms_institution"] = witness.xpath('.//tei:institution/text()', namespaces=ns)[0]
            if witness.xpath('.//tei:idno/text()', namespaces=ns):
                witness_dict["ms_idno"] = witness.xpath('.//tei:idno/text()', namespaces=ns)[0]
            if witness.xpath('.//tei:desc/text()', namespaces=ns):
                witness_dict["desc"] = witness.xpath('.//tei:desc/text()', namespaces=ns)[0]
            # Sometimes, there are multiple pointers for a single witness.
            if witness.xpath('./tei:ptr', namespaces=ns):
                ptrs = witness.xpath('./tei:ptr', namespaces=ns)
                ptrs_list = []
                for ptr in ptrs:
                    ptr_dict = {}
                    if ptr.xpath('./@type', namespaces=ns)[0] == "digit":
                        ptr_dict["ptr_type"] = "digital version"
                    else:
                        ptr_dict["ptr_type"] = ptr.xpath('./@type', namespaces=ns)[0]
                    if ptr.xpath('./@target', namespaces=ns):
                        ptr_dict["ptr_target"] = ptr.xpath('./@target', namespaces=ns)[0]
                    ptrs_list.append(ptr_dict)
                witness_dict["ptr"] = ptrs_list

            witnesses_list.append(witness_dict)

        metadata["witness"] = witnesses_list

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
        data = get_entry(item)

        item_list.append(data)

    return item_list


def get_entry(item):
    """
    This function retrieves data of a single item.
    :param item: an XML element
    :return: a dict
    """
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

    return data


def id_to_item(file, id):
    """
    This function transforms an id into an XML item to be parsed.
    :param file: an opened XML file
    :param id: a string
    :return: an item to pe parsed
    """
    # First, the id of a desc element is changed to the id of its entry.
    id_entry = re.match("CAT_[0-9]+_e[0-9]+", id)[0]

    item = file.xpath('.//tei:text//tei:item[@xml:id="%s"]' % id_entry, namespaces=ns)
    return item[0]
