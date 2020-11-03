import json
from time import process_time
import tqdm
from difflib import SequenceMatcher
import sys
import os
import re
import networkx
from networkx.algorithms.components.connected import connected_components
import argparse


# https://stackoverflow.com/a/17388505
def similar(a, b):
    """
    This function is used to compare pairs of sequences of any type.
    :param a: a string
    :param b: a string
    :return: a measure of the sequences' similarity as a float in the range [0, 1]
    """
    return SequenceMatcher(None, a, b).ratio()


# https://stackoverflow.com/a/4843408
def to_graph(l):
    """
    This function is used to create graphs (collections of nodes).
    :param l: a list
    :return: a list with graphs
    """
    graphed_list = networkx.Graph()
    for part in l:
        # each sublist is a bunch of nodes
        graphed_list.add_nodes_from(part)
        # it also imlies a number of edges:
        graphed_list.add_edges_from(to_edges(part))
    return graphed_list


# https://stackoverflow.com/a/4843408
def to_edges(l):
    """
    This function creates edges from graphs :
    It reats the param `l` as a Graph and returns it's edges :
    Ex : to_edges(['a','b','c','d']) -> [(a,b), (b,c),(c,d)]
    :param l: a list of graphs
    """
    it = iter(l)
    last = next(it)

    for current in it:
        yield last, current
        last = current


def double_loop(input_dict, searched_date):
    """
    This function creates pairs of matching entries.
    :param input_dict: a dictionary
    :param searched_date: a string (optional parameter)
    """
    print("Comparing the entries")

    output_dict1 = {}
    # First we compare each entry with each other one and give a score to each pair.
    for i in tqdm.tqdm(input_dict):
        catalog_entry_i = i.split("_d")[0]
        desc = input_dict[i]["desc"]
        term = input_dict[i]["term"]
        date = input_dict[i]["date"]
        format = input_dict[i]["format"]
        price = input_dict[i]["price"]
        pn = input_dict[i]["number_of_pages"]
        for j in input_dict:
            catalog_entry_j = j.split("_d")[0]
            # To compare two sub-entries (two tei:desc from the same item) makes no sense.
            if catalog_entry_i == catalog_entry_j:
                pass
            else:
                dict2 = {}
                score = 0
                if j == i:
                    pass
                else:
                    # Desc of a same document are often strongly similar.
                    if similar(input_dict[j]["desc"], desc) > 0.75:
                        score = score + 0.3
                    else:
                        score = score - 0.2

                    if input_dict[j]["term"] == term:
                        score = score + 0.2
                    else:
                        score = score - 0.1

                    if input_dict[j]["date"] == date and input_dict[j]["date"] is not None:
                        score = score + 0.5
                    else:
                        score = score - 0.5

                    if input_dict[j]["number_of_pages"] == pn:
                        score = score + 0.1
                    else:
                        score = score - 0.1

                    if input_dict[j]["format"] == format:
                        score = score + 0.1
                    else:
                        score = score - 0.3

                    if input_dict[j]["price"] == price:
                        score = score + 0.1
                    else:
                        score = score - 0.1
                    try:
                        dict2["author_distance"] = similar(input_dict[j]["author"], input_dict[i]["author"])
                    except:
                        dict2["author_distance"] = 0
                    dict2["score"] = score
                    # We clean the dictionary, as A-B comparison equals B-A comparison
                    if "%s-%s" % (j, i) in output_dict1:
                        pass
                    else:
                        output_dict1["%s-%s" % (i, j)] = dict2

    # The final list contains the result of the whole comparison process, without filtering, sorted by score.
    final_list = []
    for key in output_dict1:
        first_entry = key.split("-")[0]
        second_entry = key.split("-")[1]
        final_list.append((
                          output_dict1[key]["score"], [first_entry, second_entry], output_dict1[key]["author_distance"],
                          {first_entry: my_dict[first_entry]}, {second_entry: my_dict[second_entry]}))
    # We sort by author distance first, and then by the score.
    final_list.sort(reverse=True, key=lambda x: (x[2], x[0]))

    # The filtered list removes all entries with a score lower or equal to 0.6
    sensibility = 0.6
    filtered_list_with_score = [[item[1], item[0]] for item in final_list if item[0] > sensibility and item[2] >= 0.4]

    # Now let's create the clusters. We transform the list of pairs into a graph. The connected nodes are our clusters !
    # See https://stackoverflow.com/a/4843408
    filtered_list = [item[0] for item in filtered_list_with_score]
    graphed_list = to_graph(filtered_list)
    cleaned_list = [list(item) for item in list(connected_components(graphed_list))]
    cleaned_output_list = []
    n = 0
    for item in cleaned_list:
        temp_list = []
        for entry in item:
            temp_list.append({entry: my_dict[entry]})
        cleaned_output_list.append(temp_list)
        cleaned_output_list[n].append(item)
        temp_list.reverse()
        n += 1

    print("Number of pairs found: %s" % (len(filtered_list)))
    print("Number of reconciliated documents: %s" % (len(cleaned_output_list)))
    if searched_date:
        path = 'data/json/%s/%s' % (norm_author, searched_date)
    else:
        path = 'data/json/%s' % norm_author

    # reconciliated_pairs.json contains the score of each pair.
    with open('%s/reconciliated_pairs.json' % path, 'w') as outfile:
        json.dump(filtered_list_with_score, outfile)

    # reconciliated_documents.json contains contains the reconciliated entries.
    with open('%s/reconciliated_documents.json' % path, 'w') as outfile:
        outfile.truncate(0)
        json.dump(cleaned_output_list, outfile)


def author_filtering(dictionary, name):
    """
    This function extracts the entries based on the similarity with the searched author name.
    :param dictionary: a dictionary
    :param name: a string
    :return: a dictionary
    """
    output_dict = {}
    for key in dictionary:
        if dictionary[key]["author"] is not None and similar(dictionary[key]["author"].lower(), name) > 0.75:
            output_dict[key] = dictionary[key]
    with open('data/json/%s/filtered_db.json' % norm_author, 'w') as outfile:
        outfile.truncate(0)
        print("Number of documents of %s in the database: %s" % (author, len(output_dict)))
        json.dump(output_dict, outfile)
    return output_dict


def year_filtering(dictionary):
    output_dict = {}
    # a= stands for after.
    if re.compile("^a=").match(date):
        norm_date = date.split("=")[1]
        for key in dictionary:
            print(dictionary[key]["date"])
            if dictionary[key]["date"] is not None and dictionary[key]["date"] >= norm_date:
                output_dict[key] = dictionary[key]
    # b= stands for before.
    elif re.compile("^b=").match(date):
        norm_date = date.split("=")[1]
        for key in dictionary:
            if dictionary[key]["date"] is not None and dictionary[key]["date"] <= norm_date:
                output_dict[key] = dictionary[key]
    # Any year range.
    else:
        date_before = date.split("-")[0]
        date_after = date.split("-")[1]
        for key in dictionary:
            if dictionary[key]["date"] is not None and date_before <= dictionary[key]["date".split("-")[0]] <= date_after:
                output_dict[key] = dictionary[key]
    with open('data/json/%s/%s/filtered_db.json' % (norm_author, date), 'w') as outfile:
        outfile.truncate(0)
        json.dump(output_dict, outfile)
    return output_dict


def dircreate(path):
    try:
        os.mkdir(path)
    except:
        pass


def reconciliator(author, date):
    """
    This function is the main function used for queries.
    :param author: a string
    :param date: an integer
    :return:
    """
    # We normalize author names to create the folders.
    normalisation_table = str.maketrans("éèêàç", "eeeac")
    norm_author = author.translate(normalisation_table)

    # Creation of the output directory
    dircreate("data/json/%s" % norm_author)
    if date:
        dircreate("data/json/%s/%s" % (norm_author, date))

    # Only entries of the searched author are remained.
    my_dict = author_filtering(my_dict, author)

    if date:
        my_dict = year_filtering(my_dict)

    double_loop(my_dict, date)

