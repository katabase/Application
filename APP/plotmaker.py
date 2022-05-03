import plotly.graph_objs as go
import json
import re
import os

from .constantes import TEMPLATES, STATIC

# subplots permet de définir les subplots : les axes + la figure elle même
# dans l'exemple en dessous, on définit la figure et les axes comme des subplots
# The function returns a figure object and a tuple containing axes objects equal to
# nrows*ncols. Each axes object is accessible by its index
# ax.set() permet de définir les titres des colonnes
# ax.grid() permet d'avoir une grille en arrière plan

# il faut que j'arrive à exprimer le prix en fonction de l'année


# open the file json file
with open("APP/data/json/export_catalog.json", mode="r") as f:
    js = json.load(f)

# define the relative path for the output directory and font directory
outdir = os.path.join(TEMPLATES, "partials")
fontdir = os.path.join(STATIC, "fonts")


def plotter(avg=False):
    """
    if avg is False, we calculate the sum of sales for each year ;
    if pond is avg, we calculate revenue for each catalog
    :param avg:
    :return:
    """
    # prepare data for the x and y axis
    pricedict = {}  # dictionnary linking to a year the sum of its sales
    sort = {}  # dictionnary to sort pricedict by year
    x = []  # x axis of the plot : years
    y = []  # y axis of the plot: total of the sales in a year

    # create a dictionnary linking a year to the total sales of that year
    for c in js:
        if js[c]["total price"] != "unknown" and js[c]["currency"] == "FRF":
            date = re.findall(r"\d{4}", js[c]["date"])[0]
            if date not in list(pricedict.keys()):
                if avg is True:
                    avglist = [js[c]["total price"], 1]  # list linking to the total price, the total number of sales for that year
                    pricedict[date] = avglist
                else:
                    pricedict[date] = js[c]["total price"]
            else:
                if avg is True:
                    avglist[0] += js[c]["total price"]
                    avglist[1] += 1
                else:
                    pricedict[date] += js[c]["total price"]
    datelist = sorted(set(pricedict))  # sorted list of dates on which we have sale info
    # sort the price dictionnary
    for k in sorted(list(pricedict.keys())):
        sort[k] = pricedict[k]
    pricedict = sort

    # populate the x and y axis
    x = list(range(int(datelist[0]), int(datelist[-1])))  # every year between the extreme dates of datelist
    # loop through all the dates; if the date is a key in pricedict, it means that there
    # is a sale price associated with that year. in that case, add it to y; else,
    # 0 to y. in turn, y is populated with the price if it exist, with 0 if it doesn't
    for d in x:
        if str(d) in list(pricedict.keys()):
            if avg is True:
                sale = pricedict[str(d)][0] / pricedict[str(d)][1]
                y.append(sale)
            else:
                y.append(int(pricedict[str(d)]))
        else:
            y.append(0)

    # avant avec plotly
    if avg is True:
        title = "Moyenne du montant des ventes par catalogue et par an"
    else:
        title = "Somme des ventes par an"
    fig = go.Figure(
        data=[go.Bar(x=x, y=y)],
        layout=go.Layout(
            title=go.layout.Title(text=title),

        )
    )

    # enregistrement
    #dummy = BytesIO()  # create a dummy file-like object to store the plot and pass it to jinja
    with open(f"{outdir}/fig_idx.html", mode="w") as out:
        fig.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=300)
    return fig
    # avant avec matplotlib
    #fig, ax = plt.subplots()
    #ax.plot(x, y)
    #plt.stem(x, y)
    #plt.show()
