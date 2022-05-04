import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.colors import make_colorscale
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
    js = json.load(f)
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
    sort_total = {}  # dictionary to sort pricedict_total by year
    sort_avg = {}  # dictionary to sort pricedict_avg by year
    pricedict_avg = {}  # dictionnary linking to a year the average sales per catalogue
    pricedict_total = {}  # dictionnary linking to a year the sum of its sales
    x = []  # x axis of the plot : years
    y_total = []  # first y axis of the plot: total of the sales in a year
    y_avg = []  # y axis of the plot: average sales per catalog in a year

    # create a two dictionnaries:
    # - pricedict_total takes years as keys and the total of sales as values
    # - pricedict_avg takes years as keys and as values a list containing the total
    #   of sales as the first item and the number of sales as second item ; from that
    #   list it is possible to build a dictionnary of average sales per year
    for c in js:  # iterate over every catalogue item
        if js[c]["total price"] != "unknown" and js[c]["currency"] == "FRF":
            date = re.findall(r"\d{4}", js[c]["date"])[0]  # year of the sale
            # if it is the first time a date is encountered, add it to the dictionnaries
            if date not in list(pricedict_avg.keys()) and date not in list(pricedict_total.keys()):
                pricedict_avg[date] = [js[c]["total price"], 1]
                pricedict_total[date] = js[c]["total price"]
            else:
                pricedict_avg[date][0] += js[c]["total price"]
                pricedict_avg[date][1] += 1
                pricedict_total[date] += js[c]["total price"]
    datelist = sorted(set(pricedict_total.keys()))  # sorted list of dates on which we have sale info
    # sort the price dictionnaries
    for k in sorted(list(pricedict_total.keys())):
        sort_total[k] = pricedict_total[k]
        sort_avg[k] = pricedict_avg[k]
    pricedict_total = sort_total
    pricedict_avg = sort_avg

    # delete the last years if there's no price info in them

    # BUILD THE X AND Y AXIS
    x = list(range(int(datelist[0]), int(datelist[-1])))  # every year between the extreme dates of datelist
    # loop through all the dates; if the date is a key in the price dictionnaries, it means that there
    # is a sale price associated with that year. in that case, add it to y_total and y_avg; else,
    # 0 to y_total and y_avg. in turn, the y axis are populated with the prices if they exist, with 0 if they don't
    for d in x:
        if str(d) in list(pricedict_total.keys()):
            sale = pricedict_avg[str(d)][0] / pricedict_avg[str(d)][1]
            y_avg.append(sale)
            y_total.append(int(pricedict_total[str(d)]))
        else:
            y_total.append(0)
            y_avg.append(0)

    # CREATE A PLOT
    title_total = "Total sales per year (in french francs)"
    title_avg = "Average sales per catalog and per year (in french francs)"
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(title_total, title_avg)
    )
    fig.add_trace(
        go.Bar(x=x, y=y_total, marker={"color": y_total, "colorscale": scale}),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=x, y=y_avg, marker={"color": y_avg, "colorscale": scale}),
        row=1, col=2
    )
    fig.update_layout(
        paper_bgcolor=colors["cream"],
        plot_bgcolor=colors["cream"],
        margin=dict(l=5, r=5, t=30, b=30),
        showlegend=False
    )
    fig["layout"]["xaxis"]["title"] = "Year"
    fig["layout"]["yaxis2"]["title"] = "Average sales per catalogue"
    fig["layout"]["yaxis"]["title"] = "Total sales"
    fig["layout"]["xaxis2"]["title"] = "Year"

    # enregistrement
    with open(f"{outdir}/fig_idx.html", mode="w") as out:
        fig.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=300)
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