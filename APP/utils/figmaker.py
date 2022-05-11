from statistics import median, mean, quantiles
from plotly.colors import make_colorscale
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import json
import re
import os

from .constantes import TEMPLATES


# GLOBAL VARIABLES TO BUILD GRAPHS: json, output directory, colors
with open("APP/data/json/export_catalog.json", mode="r") as f:
    js_cat = json.load(f)
with open("APP/data/json/export_item.json", mode="r") as f:
    js_item = json.load(f)
outdir = os.path.join(TEMPLATES, "partials")
colors = {"cream": "#fcf8f7", "blue": "#0000ef", "burgundy1": "#890c0c", "burgundy2": "#a41a6a", "pink": "#ff94c9"}
scale = make_colorscale([colors["blue"], colors["burgundy2"]])  # create a colorscale


# haven't found a way to change fonts yet but the basic font is ok
# fonts = """
#            "urlaub", "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif,
#            "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
#        """
# fontdir = os.path.join(STATIC, "fonts")


# TEMPLATE TO NAME THE HTML FIGURES (! VERY IMPORTANT TO BUILD URLS AND DISPLAY THEM !)
# fig_(IDX|CAT_XXXX)(_[0-9])?
# ^     ^     ^        ^
# |     |     |        |_____ for the index: the identifier of the figure (7 figs are created)
# |     |_____|______________ for the index figures: IDX ; for the catalogue figures: the cat's ID (CAT_0001...)
# |__________________________ indicate it is a figure


def figmaker_idx():
    """
    create the figures to be displayed on the index page. 7 figures are created:
    - total sales per year (bar graph)
    - average sales for a whole catalogue per year (bar graph)
    - median sales for a whole catalogue per year (bar graph)
    - average sale price of an item per year (bar graph)
    - median sale price of an item per year (bar graph)
    - number of items per sale for year (2 overlayed bar graphs)

    the basis of plotly is to map data on an x and y axis ; both x and y are arrays.
    so what is needed is to create data for an x and y axis, so that the y data can
    be properly mapped to x (the y data for year 1234 must be at the same position
    as the year 1234 on the x axis. hope that makes sense).

    the figures are created in 3 steps:
    - the data is created by looping through the 2 json files and storing relevant
      data in dictionaries. those dictionaries take a year as key and other data as
      value. after that, the dictionaries are sorted and prepared to build the y axis
    - the x and y axis are created.
      - x = array containing every year between the two extreme dates for which there is price info
      - y = the relevant data (prices, number of items...) ; if there is no data, for a year,
        the value of 0 is added
    - the figures are created ; they are saved in APP/templates/partials as html files

    the figures are called within the html page using a URL : this url points to a flask route
    that renders the html files. the urls for this flask route are built using url_for
    (for the figure displayed by default) or javascript. the figures are displayed within an
    iframe.

    :return: figpath (boolean; True if figures are created; False if not)
    """
    # DEFINING VARIABLES
    # ------------------
    x = []  # x axis of the plot : years
    y_total = []  # first y axis of the plot: total of the sales in a year
    y_avg_cat = []  # y axis of the plot: average sales per catalog in a year
    y_med_cat = []  # y axis of the plot: median catalogue sales in a year
    y_avg_item = []  # y axis of the plot: average item price per year
    y_med_item = []  # y axis of the plot: median item price per year
    y_fix_item = []  # y axis of the plot: sum of fixed price items per year
    y_auc_item = []  # y axis of the plot: sum of non-fixed price items per year
    y_q1_gpitem = []  # y axis of the plot: the first quartile of item prices per 5 year range
    y_med_gpitem = []  # y axis of the plot: the median of item prices per 5 year range
    y_q3_gpitem = []  # y axis of the plot: the third quartile of item prices per 5 year range
    pdict_ls_cat = {}  # dictionnary mapping to a year a list of catalogue prices to calculate totals, medians + means
    pdict_ls_item = {}  # dictionnary mapping to a year a list of item prices, to calculate median and mean values
    cdict_fix_item = {}  # dictionary mapping to a year the total of fixed price items sold (cdict = count dictionary)
    cdict_auc_item = {}  # dictionary mapping to a year the total of non fixed price items sold: the auction items
    quart_ls_item = {}  # dictionary mapping to a 5 year range its quartiles
    sort_fix_item = {}  # "sort" dictionaries below are used to sort the above dicts by year
    sort_auc_item = {}
    sort_ls_item = {}
    sort_ls_cat = {}
    figpath = False  # return value : true if figures are created and an url can be built
    #                  in the templates pointing to those files

    # PREPARE THE DATA
    # ----------------
    # create a one dictionnary: pdict_ls_cat, a dictionnary containing the list of total catalogue
    # prices for any given year ; from that list, we can calculate
    # - the total price of all items sold
    # - the median price of a full catalogue per year
    # - the average price of a full catalogue
    for c in js_cat:  # loop over every catalogue item
        if "total price" in js_cat[c] \
                and "currency" in js_cat[c] \
                and js_cat[c]["currency"] == "FRF":
            date = re.findall(r"\d{4}", js_cat[c]["sell_date"])[0]  # year of the sale
            # if it is the first time a date is encountered, add it to the dictionnaries
            if date not in list(pdict_ls_cat.keys()):
                pdict_ls_cat[date] = [js_cat[c]["total price"]]
            else:
                pdict_ls_cat[date].append(js_cat[c]["total price"])
            figpath = True  # at this point, it is certain that figures are created

    # create three dictionnaries:
    # - pdict_ls_item: list of item prices per year
    # - cdict_fix_item: number of fixed price items sold per year
    # - cdict_auc_item: number of non-fixed price items sold per year
    for i in js_item:  # loop over every item in the json
        if js_item[i]["sell_date"] is not None:
            date = re.findall(r"\d{4}", js_item[i]["sell_date"])[0]  # year of the sale
            # calculate the number of fixed price and auction items put up for sale every year
            if js_item[i]["price"] is not None:
                if date not in cdict_fix_item.keys():
                    cdict_fix_item[date] = 1
                else:
                    cdict_fix_item[date] += 1
            else:
                if date not in cdict_auc_item.keys():
                    cdict_auc_item[date] = 1
                else:
                    cdict_auc_item[date] += 1

            # if there is price info on an item, create pdict_ls_item
            if js_item[i]["price"] is not None \
                    and "currency" in js_item[i] \
                    and js_item[i]["currency"] == "FRF":
                # at this point we should convert the price to take into accound
                # inflation and other currencies ; we should probably create a function
                # in a different file for that
                if date not in pdict_ls_item.keys():
                    pdict_ls_item[date] = [js_item[i]["price"]]
                elif date in pdict_ls_item.keys():
                    pdict_ls_item[date].append(js_item[i]["price"])

    # finalise the data creation ; for some reason, the lengths of catalogues vary depending on the
    # source catalogue and what is being calculated ; the keys also vary from one dictionary to another.
    # in turn, we need to loop over the different kinds of dicts separately
    datelist = sorted(set(pdict_ls_cat.keys()))  # sorted list of dates on which we have sale info
    # sort the price per catalog dictionnaries
    for k in sorted(list(pdict_ls_cat.keys())):
        sort_ls_cat[k] = pdict_ls_cat[k]
    pdict_ls_cat = sort_ls_cat
    # sort the price per item dictionnaries
    for k in sorted(list(pdict_ls_item.keys())):
        sort_ls_item[k] = pdict_ls_item[k]
    pdict_ls_item = sort_ls_item
    # sort the cdict_* dictionnaires
    for k in sorted(list(cdict_fix_item.keys())):
        sort_fix_item[k] = cdict_fix_item[k]
    for k in sorted(list(cdict_auc_item.keys())):
        sort_auc_item[k] = cdict_auc_item[k]
    cdict_auc_item = sort_auc_item
    cdict_fix_item = sort_fix_item
    # create data for the box charts: group pdict_ls_item values per 5 year range + calculate quartiles for each range
    group_ls_item = sorter(pdict_ls_item)  # dictionary mapping to a 5 year range the list prices for that range
    for k, v in group_ls_item.items():
        quart_ls_item[k] = quantiles(v)

    # BUILD THE X AND Y AXIS
    # ----------------------
    x = list(range(int(datelist[0])-1, int(datelist[-1])+1))  # years between the extremes of datelist (included)
    # loop through all the dates; if the date is a key in the dictionnaries, it means that there
    # data associated with that year. in that case, in that case, add the data for that year to the y axis; else, add
    # 0 to y_total and y_avg_cat. in turn, the y axis are populated with data if it exists, with 0 it doesn't
    for d in x:
        if str(d) in list(pdict_ls_cat.keys()):
            y_total.append(sum(pdict_ls_cat[str(d)]))
            y_avg_cat.append(mean(pdict_ls_cat[str(d)]))
            y_med_cat.append(median(pdict_ls_cat[str(d)]))
        else:
            y_total.append(0)
            y_avg_cat.append(0)
            y_med_cat.append(0)
        if str(d) in list(pdict_ls_item.keys()):
            y_avg_item.append(mean(pdict_ls_item[str(d)]))
            y_med_item.append(median(pdict_ls_item[str(d)]))
        else:
            y_avg_item.append(0)
            y_med_item.append(0)
        if str(d) in list(cdict_auc_item.keys()):
            y_auc_item.append(cdict_auc_item[str(d)])
        else:
            y_auc_item.append(0)
        if str(d) in list(cdict_fix_item.keys()):
            y_fix_item.append(cdict_fix_item[str(d)])
        else:
            y_fix_item.append(0)
        if d in list(quart_ls_item.keys()):
            y_q1_gpitem.append(quart_ls_item[d][0])
            y_q3_gpitem.append(quart_ls_item[d][2])
            y_med_gpitem.append(quart_ls_item[d][1])
        else:
            y_q1_gpitem.append(0)
            y_q3_gpitem.append(0)
            y_med_gpitem.append(0)

    # CREATE PLOTS
    # ------------
    # store the titles as string and basic layout as a dictionnary
    title_total = "Total sales per year (in french francs)"
    title_avg_cat = "Average sales per catalogue and per year (in french francs)"
    title_med_cat = "Median sales price per catalogue per year (in french francs)"
    title_avg_item = "Average sale price of an item per year (in french francs)"
    title_med_item = "Median sale price of an item per year (in french francs)"
    title_cnt = "Number of items for sale per year"
    title_qnt = "Evolution of the price of an item (in 5 year ranges, in quartiles)"
    layout = {
        "paper_bgcolor": colors["cream"],
        "plot_bgcolor": colors["cream"],
        "margin": {"l": 5, "r": 5, "t": 30, "b": 30},
        "showlegend": False,
        "xaxis": {"anchor": "x", "title": {"text": "Year"}},
        "barmode": "overlay"  # only affects plot 6
    }
    # figure 1 : sum of sales per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Total sales"}}
    layout["title"] = title_total
    fig1 = go.Figure(
        data=[go.Bar(x=x, y=y_total, marker={"color": y_total, "colorscale": scale},
                     hovertemplate="<b>Year</b>: %{x}<br><b>Sum of all catalogues' "
                                   + "prices </b>: %{y:.2f} FRF<extra></extra>")],
        layout=go.Layout(layout)
    )
    # figure 2 : average of the sum of sales in a catalogue per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Average sales per catalogue"}}
    layout["title"] = title_avg_cat
    fig2 = go.Figure(
        data=[go.Bar(x=x, y=y_avg_cat, marker={"color": y_avg_cat, "colorscale": scale},
                     hovertemplate="<b>Year</b>: %{x}<br><b>Average sum of prices per catalogue"
                                   + "</b>: %{y:.2f} FRF<extra></extra>")],
        layout=go.Layout(layout)
    )
    # figure 3 : median of the sum of sales in a catalogue per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Median sales per catalogue"}}
    layout["title"] = title_med_cat
    fig3 = go.Figure(
        data=[go.Bar(x=x, y=y_med_cat, marker={"color": y_med_cat, "colorscale": scale},
                     hovertemplate="<b>Year</b>: %{x}<br><b>Median sales per catalogue"
                                   + "</b>: %{y:.2f} FRF<extra></extra>")],
        layout=go.Layout(layout)
    )
    # figure 4 : average price of an item per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Average item price"}}
    layout["title"] = title_avg_item
    fig4 = go.Figure(
        data=[go.Bar(x=x, y=y_avg_item, marker={"color": y_avg_item, "colorscale": scale},
                     hovertemplate="<b>Year</b>: %{x}<br><b>Average item price</b>: %{y:.2f} FRF<extra></extra>")],
        layout=go.Layout(layout)
    )
    # figure 5 : median price of an item per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Median item price"}}
    layout["title"] = title_med_item
    fig5 = go.Figure(
        data=[go.Bar(x=x, y=y_med_item, marker={"color": y_med_item, "colorscale": scale},
                     hovertemplate="<b>Year</b>: %{x}<br><b>Median item price</b>: %{y:.2f} FRF<extra></extra>")],
        layout=go.Layout(layout)
    )
    # figure 6 : number of fixed price and auction items per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Number of items for sale"}}
    layout["title"] = title_cnt
    fig6 = go.Figure(
        data=[
            go.Bar(x=x, y=y_fix_item, marker={"color": colors["burgundy2"], "opacity": 0.7},
                   hovertemplate="<b>Year</b>: %{x}<br><b>Number of fixed-price "
                                 + "items for sale </b>: %{y}<extra></extra>"),
            go.Bar(x=x, y=y_auc_item, marker={"color": colors["blue"], "opacity": 0.55},
                   hovertemplate="<b>Year</b>: %{x}<br><b>Number of auction items for sale </b>: %{y}<extra></extra>")
        ],
        layout=go.Layout(layout)
    )
    # figure 7 : 1 box chart per 5 year range
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Price of an item (in quantiles)"}}
    layout["title"] = title_qnt
    fig7 = go.Figure(
        data=[go.Box(x=x, q1=y_q1_gpitem, median=y_med_gpitem, q3=y_q3_gpitem,
                     marker={"color": colors["blue"]},
                     fillcolor=colors["cream"],
                     width=4)
              ],
        layout=go.Layout(layout)
    )

    # saving the files ; the file will be called in an iframe using a url_for
    with open(f"{outdir}/fig_IDX_1.html", mode="w") as out:
        fig1.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_2.html", mode="w") as out:
        fig2.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_3.html", mode="w") as out:
        fig3.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_4.html", mode="w") as out:
        fig4.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_5.html", mode="w") as out:
        fig5.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_6.html", mode="w") as out:
        fig6.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_IDX_7.html", mode="w") as out:
        fig7.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)

    # return
    return figpath


def figmaker_cat(cat_id):
    """
    function to create the figures to be called on the catalogue pages. 2 figures are created:
    - price distribution in the catalogue (violin plot)
    - 10 most expensive items (bar chart)

    the figures are created in 3 steps:
    - data preparation:
      - for figure 1, the price of all items in the catalogue are added to x1
      - for figure 2, the 10 most expensive items are extracted from x1 and used
        to build a dictionary of 10 most expensive items sorted by price (this dict
        is basically a copy of their export_item.json version)
    - preparing the x and y axis: this step only concerts figure 2:
      - build y2 (height of the bars, aka the price of the items)
      - build data for the hover templates
    - creating the figures (the two figures are subplots, i.e. they are subfigures in a
    single figure) and saving them as html files

    the html figures are displayed on the html catalogue pages within an iframe and
    called with a url_for pointing towards that figure
    see the description of figmaker_idx for a few extra details

    :return: figpath (boolean: True if there is price info and a price is created, false if not)
    """
    # DEFINING VARIABLES
    # ------------------
    x1 = []  # x axis of the 1st plot (violin plot): the prices of all items in a catalogue
    x2 = []  # x axis of the 2nd plot: tei:name of the most expensive items
    y2 = []  # y axis of the 2nd plot: top 10 prices
    hovdata = []  # list of lists to pass to fig2's template
    pdict_top = {}  # dictionary mapping to the 10 most expensive item's xml:id their data in export_item.json
    #                 pdict_top can have more than 10 items if several items share the same top prices
    sort_pdict_top = {}  # dictionary to sort pdict_top by item price
    figpath = False  # variable to check if a figure will be created and if a path towards a figure
    #                  will exist ; if there's price info on that catalogue, a figure will be created

    # PREPARE THE DATA
    # ----------------
    # prepare data for the x1 (the x axis of the first figure)
    for i in js_item:
        if js_item[i]["price"] is not None \
                and js_item[i]["currency"] == "FRF" \
                and re.match(f"{cat_id}_e\d+(_d\d+)?", i):
            x1.append(js_item[i]["price"])
            figpath = True

    # prepare data for the second figure
    # small safeguard in case there are less than 10 items with a price
    if len(x1) >= 10:
        top_price = sorted(x1)[-10:]  # 10 highest prices prices
    else:
        top_price = sorted(x1)
    for i in js_item:
        if re.match(f"{cat_id}_e\d+(_d\d+)?", i) \
                and js_item[i]["price"] is not None \
                and js_item[i]["currency"] == "FRF" \
                and js_item[i]["price"] in top_price:
            pdict_top[i] = js_item[i]

    # order pdict_top by price
    for p in top_price:
        for k, v in pdict_top.items():
            if p == v["price"]:
                sort_pdict_top[k] = v
    pdict_top = sort_pdict_top

    # BUILD THE X AND Y AXIS
    # ----------------------
    # create the x2 axis, y2 axis and data for the hover template
    for v in pdict_top.values():
        y2.append(v["price"])
        x2.append(v["author"]) if v["author"] is not None else x2.append("unknown")
        itlist = []  # list of data on an item to pass to hovdata
        itlist.append(v["author"]) if v["author"] is not None else itlist.append("unknown")
        itlist.append(v["date"]) if v["date"] is not None else itlist.append("unknown")
        itlist.append(v["number_of_pages"]) if v["number_of_pages"] is not None else itlist.append("unknown")
        if v["desc"] is not None and len(v["desc"]) <= 90:
            itlist.append(v["desc"])
        elif v["desc"] is not None and len(v["desc"]) > 90:
            itlist.append(v["desc"][:90] + "[...]")
        else:
            itlist.append("unknown")
        hovdata.append(itlist)
    # update x2 if there are duplicates
    # if several items have the same title, plotly treats them as a single item and stacks them up. to
    # avoid this, check if there are duplicates ; if there are duplicates, rename the duplicate titles
    # by adding a number in parentheses: "Title (1)" for the first one, "Title (2)" for the second...
    if len(set(x2)) != len(x2):
        duplicates = [t for t in x2 if x2.count(t) > 1]
        tlist = []  # list to temporarily store the titles for fig2 (tlist = "title list")
        dupldict = {}  # mapping of title to the number of duplicates
        for t in x2:
            if t not in list(dupldict.keys()):
                dupldict[t] = 1
            else:
                dupldict[t] += 1
            if t in duplicates:
                tlist.append(f"{t} ({dupldict[t]})")
            else:
                tlist.append(t)
        x2 = tlist

    # CREATE PLOTS
    # ------------
    layout = {
        "paper_bgcolor": colors["cream"],
        "plot_bgcolor": colors["cream"],
        "margin": {"l": 5, "r": 5, "t": 30, "b": 30},
        "showlegend": False,
    }

    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4],
        subplot_titles=("Distribution of the prices in the catalogue (in french francs)", "Ten most expensive items")
    )
    # subplot 1: violin plot showing the price distribution in the catalogue, with quartiles and mean prices
    fig.add_trace(
        go.Violin(
            x=x1, meanline={"visible": True, "color": colors["blue"]}, width=1,
            marker={"color": colors["burgundy2"],
                    "outliercolor": colors["blue"]},
            box={"visible": True, "line": {"color": colors["blue"]}},
            fillcolor=colors["cream"]
        ),
        row=1, col=1
    )
    # subplot 2: bar chart of the most expensive items in the catalogue
    fig.add_trace(
        go.Bar(y=y2, x=x2, marker={"color": y2, "colorscale": scale},
               hovertemplate="<b>Author or document's title</b>: %{customdata[0]}<br>"
                             + "<b>Date of the document</b>: %{customdata[1]}<br>"
                             + "<b>Number of pages</b>: %{customdata[2]}<br>"
                             + "<b>Description</b>: %{customdata[3]}"
                             + "<extra></extra>",
               customdata=hovdata),
        row=2, col=1
    )
    # layout
    fig.update_layout(layout)
    fig["layout"]["xaxis"]["title"] = "Price (in french francs)"
    fig["layout"]["yaxis"]["title"] = "Proportion of items"
    fig["layout"]["yaxis"]["showticklabels"] = False
    fig["layout"]["yaxis2"]["title"] = "Price"

    # saving the files ; the file will be called in an iframe using a url_for
    with open(f"{outdir}/fig_{cat_id}.html", mode="w") as out:
        fig.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=650)
        
    # return : if there is price data, figpath is true and a path to a figure for that catalogue will be available
    return figpath


def figmaker_itm():
    pass

def sorter(input_dict):
    """
    group the values of input_dict in 5 year ranges. input_dict is a dictionnary mapping to
    each year a list of item prices. the values of input_dict must be non-nested lists containing integers
    only (no lists within lists).
    sorter groups the keys of input_dict in 5 year ranges (1821-1826, 1826-1830...) ;
    the keys of output_dict are the average between floor and roof values for a
    5 year range (1821-1826 => 1823); the values of output_dict are a list of item prices
    for that 5 year range

    :param input_dict: the input dictionary to sort
    :return: output_dict, a dictionnary mapping to an average year the item prices for a range
    """
    output_dict = {}
    for d in input_dict.keys():
        d = int(d)
        last = d % 10
        if last >= 6:
            floor = (d - last) + 6
            roof = d + (10 - last)
            k = mean([floor, roof])
        else:
            floor = (d - last) + 1
            roof = (d - last) + 5
            k = mean([floor, roof])
        if k not in output_dict.keys():
            output_dict[k] = input_dict[str(d)]
        else:
            for v in input_dict[str(d)]:
                output_dict[k].append(v)
    return output_dict

# FOR FIGMAKER_CAT IF THE FIGURES ARE SAVED IN TWO SEPARATE FILES
#    # figure 1: violin plot showing the price distribution in the catalogue, with quarties and mean prices
#    fig1 = go.Figure(
#        data=go.Violin(x=x1, meanline={"visible": True, "color": colors["blue"]}, width=1,
#                       marker={"color": colors["burgundy2"],
#                               "outliercolor": colors["blue"]},
#                       box={"visible": True, "line": {"color": colors["blue"]}},
#                       fillcolor=colors["cream"]),
#        layout=go.Layout(layout)
#    )
#    # figure 2: bar chart of the most expensive items in the catalogue
#    layout["xaxis_tickangle"] = -25
#    fig2 = go.Figure(
#        data=go.Bar(y=y2, x=x2, marker={"color": y2, "colorscale": scale},
#                    hovertemplate="<b>Author or document's title</b>: %{customdata[0]}<br>"
#                                  + "<b>Date of the document</b>: %{customdata[1]}<br>"
#                                  + "<b>Number of pages</b>: %{customdata[2]}<br>"
#                                  + "<b>Description</b>: %{customdata[3]}",
#                    customdata=hovdata),
#        layout=go.Layout(layout)
#    )
#
#    # saving the files ; the file will be called in an iframe using a url_for
#    with open(f"{outdir}/fig_{cat_id}_1.html", mode="w") as out:
#        fig1.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
#    with open(f"{outdir}/fig_{cat_id}_2.html", mode="w") as out:
#        fig2.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)


# https://plotly.com/python-api-reference/generated/plotly.colors.html
# https://plotly.com/python/reference/layout/coloraxis/