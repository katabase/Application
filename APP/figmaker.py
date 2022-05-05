from plotly.subplots import make_subplots
from plotly.colors import make_colorscale
import plotly.graph_objs as go
from statistics import median, mean
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
colors = {"cream": "#fcf8f7", "blue": "#0000ef", "burgundy1": "#890c0c", "burgundy2": "#a41a6a"}
scale = make_colorscale([colors["blue"], colors["burgundy2"]])  # create a colorscale


# haven't found a way to change fonts yet but the basic font is ok
# fonts = """
#            "urlaub", "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif,
#            "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
#        """
# fontdir = os.path.join(STATIC, "fonts")


def plotter(avg=False):
    """
    if avg is False, we calculate the sum of sales for each year ;
    if pond is avg, we calculate revenue for each catalog
    :param avg:
    :return:
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
    pdict_total = {}  # dictionary linking to a year the sum of its sales (p = price)
    pdict_avg_cat = {}  # dictionary linking to a year the average sales for a whole catalogue
    pdict_med_cat = {}  # dictionary linking to a year the median sales for a whole catalogue
    pdict_avg_item = {}  # dictionary linking to a year the average item price
    pdict_med_item = {}  # dictionary linking to a year the median item price
    cdict_fix_item = {}  # dictionary linking to a year the total of fixed price items sold (cdict = count dictionary)
    cdict_auc_item = {}  # dictionary linking to a year the total of non fixed price items sold: the auction items
    sort_total = {}  # "sort" dictionaries below are used to sort the above dicts by year
    sort_avg_cat = {}
    sort_avg_cat = {}
    sort_med_cat = {}
    sort_avg_item = {}
    sort_med_item = {}
    sort_fix_item = {}
    sort_auc_item = {}

    # PREPARE THE DATA
    # ----------------
    # create a three dictionnaries:
    # - pdict_total takes years as keys and the total of sales as values
    # - pdict_med_cat takes years as keys and as values a list containing every catalogue's
    #   total sales price ; this list will be used to calculate the median value of the total
    #   sales in a catalogue
    # - pdict_avg_cat takes years as keys and as values a list containing the total
    #   of sales as the first item and the number of sales as second item ; from that
    #   list it is possible to build a dictionnary of average sales per year
    for c in js_cat:  # loop over every catalogue item
        if "total price" in js_cat[c] \
                and "currency" in js_cat[c] \
                and js_cat[c]["currency"] == "FRF":
            date = re.findall(r"\d{4}", js_cat[c]["sell_date"])[0]  # year of the sale
            # if it is the first time a date is encountered, add it to the dictionnaries
            if date not in list(pdict_avg_cat.keys()) and date not in list(pdict_total.keys()):
                pdict_total[date] = js_cat[c]["total price"]
                pdict_avg_cat[date] = [js_cat[c]["total price"], 1]
                pdict_med_cat[date] = [js_cat[c]["total price"]]
            else:
                pdict_total[date] += js_cat[c]["total price"]
                pdict_avg_cat[date][0] += js_cat[c]["total price"]
                pdict_avg_cat[date][1] += 1
                pdict_med_cat[date].append(js_cat[c]["total price"])

    print("1 DONE")

    # create two dictionnaries:
    # - pdict_avg_item: average price per item and per year
    # - pdict_med_item: median price per item and per year
    # build pdict_avg_item and pdict_med_item : for every year, store as values a list of every item's
    # price
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

            # if there is price info, create pdict_avg_item and pdict_med_item
            if js_item[i]["price"] is not None \
                    and "currency" in js_item[i] \
                    and js_item[i]["currency"] == "FRF":
                # at this point we should convert the price to take into accound
                # inflation and other currencies ; we should probably create a function
                # in a different file for that

                if date not in pdict_avg_item.keys():
                    pdict_avg_item[date] = [js_item[i]["price"]]
                elif date in pdict_avg_item.keys():
                    pdict_avg_item[date].append(js_item[i]["price"])

                if date not in pdict_med_item.keys():
                    pdict_med_item[date] = [js_item[i]["price"]]
                elif date in pdict_med_item.keys():
                    pdict_med_item[date].append(js_item[i]["price"])

    print("2 DONE")

    # finalise the data creation ; for some reason, the lengths of catalogues vary depending on the
    # source catalogue and what is being calculated ; the keys also vary from one dictionary to another.
    # below is a list of corresponding dictionnaries (same lengths, same keys) :
    # - pdict_total <=> pdict_avg_cat <=> pdict_med_cat
    # - pdict_med_item <=> pdict_avg_item
    # - cdict_fix_item
    # - cdict_auc_item
    # in turn, we need to loop over the different kinds of dicts separately
    datelist = sorted(set(pdict_total.keys()))  # sorted list of dates on which we have sale info
    # calculate average and median item price for every year
    # sort the price per catalog dictionnaries
    for k in sorted(list(pdict_total.keys())):
        sort_total[k] = pdict_total[k]
        sort_avg_cat[k] = pdict_avg_cat[k]
        sort_med_cat[k] = pdict_med_cat[k]
    pdict_total = sort_total
    pdict_avg_cat = sort_avg_cat
    pdict_med_cat = sort_med_cat
    # sort the price per item dictionnaries
    for k in sorted(list(pdict_med_item.keys())):
        sort_med_item[k] = pdict_med_item[k]
        sort_avg_item[k] = pdict_avg_item[k]
    pdict_med_item = sort_med_item
    pdict_avg_item = sort_avg_item
    # sort the cdict_* dictionnaires
    for k in sorted(list(cdict_fix_item.keys())):
        sort_fix_item[k] = cdict_fix_item[k]
    for k in sorted(list(cdict_auc_item.keys())):
        sort_auc_item[k] = cdict_auc_item[k]
    cdict_auc_item = sort_auc_item
    cdict_fix_item = sort_fix_item

    print("3 DONE")

    # BUILD THE X AND Y AXIS
    # ----------------------
    x = list(range(int(datelist[0])-1, int(datelist[-1])+1))  # years between the extremes of datelist (included)
    # loop through all the dates; if the date is a key in the dictionnaries, it means that there
    # data associated with that year. in that case, in that case, add the data for that year to the y axis; else, add
    # 0 to y_total and y_avg_cat. in turn, the y axis are populated with data if it exists, with 0 it doesn't
    for d in x:
        if str(d) in list(pdict_total.keys()):
            avgcat = pdict_avg_cat[str(d)][0] / pdict_avg_cat[str(d)][1]
            y_avg_cat.append(avgcat)
            y_med_cat.append(median(pdict_med_cat[str(d)]))
            y_total.append(int(pdict_total[str(d)]))
        else:
            y_total.append(0)
            y_avg_cat.append(0)
            y_med_cat.append(0)
        if str(d) in list(pdict_med_item.keys()):
            y_avg_item.append(mean(pdict_avg_item[str(d)]))
            y_med_item.append(median(pdict_med_item[str(d)]))
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

    print("4 DONE")

    # CREATE PLOTS
    # ------------
    # store the titles as string and basic layout as a dictionnary
    title_total = "Total sales per year (in french francs)"
    title_avg_cat = "Average sales per catalogue and per year (in french francs)"
    title_med_cat = "Median sales price per catalogue per year (in french francs)"
    title_avg_item = "Average sale price of an item per year (in french francs)"
    title_med_item = "Median sale price of an item per year (in french francs)"
    title_cnt = "Number of items for sale per year"
    layout = {
        "paper_bgcolor": colors["cream"],
        "plot_bgcolor": colors["cream"],
        "margin": dict(l=5, r=5, t=30, b=30),
        "showlegend": False,
        "xaxis":{"anchor": "x", "title": {"text": "Year"}},
        "barmode": "overlay"  # only affects figure6; other values: "stack", "group", relative"
    }
    # figure 1 : sum of sales per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Total sales"}}
    layout["title"] = title_total
    fig1 = go.Figure(
        data=[go.Bar(x=x, y=y_total, marker={"color": y_total, "colorscale": scale})],
        layout=go.Layout(layout)
    )
    # figure 2 : average of the sum of sales in a catalogue per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Average sales per catalogue"}}
    layout["title"] = title_avg_cat
    fig2 = go.Figure(
        data=[go.Bar(x=x, y=y_avg_cat, marker={"color": y_avg_cat, "colorscale": scale})],
        layout=go.Layout(layout)
    )
    # figure 3 : median of the sum of sales in a catalogue per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Median sales per catalogue"}}
    layout["title"] = title_med_cat
    fig3 = go.Figure(
        data=[go.Bar(x=x, y=y_med_cat, marker={"color": y_med_cat, "colorscale": scale})],
        layout=go.Layout(layout)
    )
    # figure 4 : average price of an item per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Average item price"}}
    layout["title"] = title_avg_item
    fig4 = go.Figure(
        data=[go.Bar(x=x, y=y_avg_item, marker={"color": y_avg_item, "colorscale": scale})],
        layout=go.Layout(layout)
    )
    # figure 5 : median price of an item per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Median item price"}}
    layout["title"] = title_med_item
    fig5 = go.Figure(
        data=[go.Bar(x=x, y=y_med_item, marker={"color": y_med_item, "colorscale": scale})],
        layout=go.Layout(layout)
    )
    # figure 6 : number of fixed price and auction items per year
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Number of items for sale"}}
    layout["title"] = title_cnt
    fig6 = go.Figure(
        data=[
            go.Bar(x=x, y=y_fix_item, marker={"color": colors["burgundy2"], "opacity": 0.7}),
            go.Bar(x=x, y=y_auc_item, marker={"color": colors["blue"], "opacity": 0.55})
        ],
        layout=go.Layout(layout)
    )

    # BOX OBJECTS https://plotly.com/python-api-reference/generated/plotly.graph_objects.Box.html?highlight=graph%20objects%20box

    print("5 DONE")

    # saving the files ; the file will be called in an iframe using a url_for
    with open(f"{outdir}/fig_idx1.html", mode="w") as out:
        fig1.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_idx2.html", mode="w") as out:
        fig2.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_idx3.html", mode="w") as out:
        fig3.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_idx4.html", mode="w") as out:
        fig4.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_idx5.html", mode="w") as out:
        fig5.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)
    with open(f"{outdir}/fig_idx6.html", mode="w") as out:
        fig6.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)

    print("6 DONE")

    # return
    return None

# TEPLATE FOR A SINGLE FIGURE
# fig.add_trace(go.Figure(
#     data=[go.Bar(x=x, y=y, marker={"color": y, "colorscale": scale})],
#     layout=go.Layout(
#         title=go.layout.Title(text=title_total),
#         paper_bgcolor=colors["cream"],
#         plot_bgcolor=colors["cream"],
#         margin=dict(l=30, r=5, t=30, b=5),
#         xaxis={"anchor": "x", "title": {"text": "Year"}},
#         yaxis={"anchor": "y", "title": {"text": "Total sales"}}
#     )
# ))

# TEMPLATE FOR A FIGURE WITH SUBPLOTS
#    fig = make_subplots(
#        rows=4, cols=2,
#        subplot_titles=(title_total, title_avg_cat, title_med_cat, title_avg_item, title_med_item, title_cnt)
#    )
#    # subplot 1 : sum of sales per year
#    fig.add_trace(
#        go.Bar(x=x, y=y_total, marker={"color": y_total, "colorscale": scale}),
#        row=1, col=1
#    )
#    # subplot 2 : average of the sum of sales in a catalogue per year
#    fig.add_trace(
#        go.Bar(x=x, y=y_avg_cat, marker={"color": y_avg_cat, "colorscale": scale}),
#        row=1, col=2
#    )
#    fig.update_layout(
#        paper_bgcolor=colors["cream"],
#        plot_bgcolor=colors["cream"],
#        margin=dict(l=5, r=5, t=30, b=30),
#        showlegend=False,
#        barmode="overlay"  # only affectd subplot6; other values: "stack", "group", relative"
#    )
#    fig["layout"]["xaxis"]["title"] = "Year"
#    fig["layout"]["yaxis"]["title"] = "Total sales"
#    fig["layout"]["xaxis2"]["title"] = "Year"
#    fig["layout"]["yaxis2"]["title"] = "Average sales per catalogue"

# https://plotly.com/python-api-reference/generated/plotly.colors.html
# https://plotly.com/python/reference/layout/coloraxis/