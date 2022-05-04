from plotly.subplots import make_subplots
from plotly.colors import make_colorscale
import plotly.graph_objs as go
from statistics import median, mean
import json
import re
import os

from .constantes import TEMPLATES

# subplots permet de définir les subplots : les axes + la figure elle même
# dans l'exemple en dessous, on définit la figure et les axes comme des subplots
# The function returns a figure object and a tuple containing axes objects equal to
# nrows*ncols. Each axes object is accessible by its index
# ax.set() permet de définir les titres des colonnes
# ax.grid() permet d'avoir une grille en arrière plan

# il faut que j'arrive à exprimer le prix en fonction de l'année


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
    # PREPARE THE DATA
    x = []  # x axis of the plot : years
    y_total = []  # first y axis of the plot: total of the sales in a year
    y_avg_cat = []  # y axis of the plot: average sales per catalog in a year
    y_med_cat = []  # y axis of the plot: median catalogue sales in a year
    y_avg_item = []  # y axis of the plot: average item price per year
    y_med_item = []  # y axis of the plot: median item price per year
    pdict_total = {}  # dictionary linking to a year the sum of its sales (p = price)
    pdict_avg_cat = {}  # dictionary linking to a year the average sales for a whole catalogue
    pdict_med_cat = {}  # dictionary linking to a year the median sales for a whole catalogue
    pdict_avg_item = {}  # dictionary linking to a year the average item price
    pdict_med_item = {}  # dictionary linking to a year the median item price
    sort_total = {}  # "sort" dictionaries below are used to sort the above dicts by year
    sort_avg_cat = {}
    sort_avg_cat = {}
    sort_med_cat = {}
    sort_avg_item = {}
    sort_med_item = {}

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
        if js_item[i]["sell_date"] is not None \
                and "currency" in js_item[i] \
                and js_item[i]["currency"] == "FRF":
            date = re.findall(r"\d{4}", js_item[i]["sell_date"])[0]  # year of the sale

            if date not in (pdict_avg_item.keys()) and js_item[i]["price"] is not None:
                pdict_avg_item[date] = [js_item[i]["price"]]
            elif date in (pdict_avg_item.keys()) and js_item[i]["price"] is not None:
                pdict_avg_item[date].append(js_item[i]["price"])

            if date not in (pdict_med_item.keys()) and js_item[i]["price"] is not None:
                pdict_med_item[date] = [js_item[i]["price"]]
            elif date not in (pdict_med_item.keys()) and js_item[i]["price"] is not None:
                pdict_med_item[date].append(js_item[i]["price"])

    print("2 DONE")

    # TOTAL OF ITEMS WITH NO PRICE
    #     elif "total price" not in js[c]:
    #         noprice += js[c]["item count"]
    # print("##############")
    # print(nprice)

    # finalise the data creation ; for some reason, the dicts built using js_cat are not of the same
    # length as those made using js_item ; in turn, we need to loop over the two kinds of dicts separately
    datelist = sorted(set(pdict_total.keys()))  # sorted list of dates on which we have sale info
    # calculate average and median item price for every year
    """for k, v in pdict_med_item.items():
        pdict_med_item[k] = median(k)
        pdict_avg_item[k] = mean(k)
    # calculate every year's median total catalogue price
    for k, v in pdict_med_cat.items():
        pdict_med_cat[k] = median(v)"""
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

    print("3 DONE")

    # BUILD THE X AND Y AXIS
    # ----------------------
    x = list(range(int(datelist[0])-1, int(datelist[-1])+1))  # years between the extremes of datelist (included)
    # loop through all the dates; if the date is a key in the price dictionnaries, it means that there
    # is a sale price associated with that year. in that case, add it to y_total and y_avg_cat; else,
    # 0 to y_total and y_avg_cat. in turn, the y axis are populated with the prices if they exist, with 0 if they don't
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

    print("4 DONE")

    # CREATE A PLOT
    # -------------
    title_total = "Total sales per year (in french francs)"
    title_avg = "Average sales per catalog and per year (in french francs)"
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(title_total, title_avg)
    )
    # subplot 1
    fig.add_trace(
        go.Bar(x=x, y=y_total, marker={"color": y_total, "colorscale": scale}),
        row=1, col=1
    )
    # subplot 2
    fig.add_trace(
        go.Bar(x=x, y=y_avg_cat, marker={"color": y_avg_cat, "colorscale": scale}),
        row=1, col=2
    )
    # subplot 3
    fig.add_trace(
        go.Bar(x=x, y=y_med_cat, marker={"color": y_med_cat, "colorscale": scale}),
        row=2, col=1
    )
    # subplot 4
    fig.add_trace(
        go.Bar(x=x, y=y_avg_item, marker={"color": y_avg_item, "colorscale": scale}),
        row=2, col=2
    )
    # subplot 5
    fig.add_trace(
        go.Bar(x=x, y=y_med_item, marker={"color": y_med_item, "colorscale": scale}),
        row=3, col=1
    )
    fig.update_layout(
        paper_bgcolor=colors["cream"],
        plot_bgcolor=colors["cream"],
        margin=dict(l=5, r=5, t=30, b=30),
        showlegend=False
    )
    fig["layout"]["xaxis"]["title"] = "Year"
    fig["layout"]["yaxis"]["title"] = "Total sales"
    fig["layout"]["xaxis2"]["title"] = "Year"
    fig["layout"]["yaxis2"]["title"] = "Average sales per catalogue"
    fig["layout"]["xaxis3"]["title"] = "Year"
    fig["layout"]["yaxis3"]["title"] = "Median sales per catalogue"
    fig["layout"]["xaxis4"]["title"] = "Year"
    fig["layout"]["yaxis4"]["title"] = "Average item price"
    fig["layout"]["xaxis5"]["title"] = "Year"
    fig["layout"]["yaxis5"]["title"] = "Median item price"

    print("5 DONE")

    # saving the file ; the file will be called in an iframe using a url_for
    with open(f"{outdir}/fig_idx.html", mode="w") as out:
        fig.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height="100%")
    return fig

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

# https://plotly.com/python-api-reference/generated/plotly.colors.html
# https://plotly.com/python/reference/layout/coloraxis/