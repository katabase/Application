from plotly.colors import make_colorscale
import plotly.graph_objs as go
from statistics import median, mean, quantiles
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


def plotter():
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

    print("1 DONE")

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

    print("2 DONE")

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
    # create data for the box charts: group pdict_ls_item values per 5 year range + calculate quantiles for each range
    group_ls_item = sorter(pdict_ls_item)  # dictionary mapping to a 5 year range the prices for that range
    for k, v in pdict_ls_item.items():
        quart_ls_item[k] = quantiles(v)
    print(quart_ls_item)


    print("3 DONE")

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
        if str(d) in list(group_ls_item.keys()):
            y_q1_gpitem.append(group_ls_item[d][0])
            y_q3_gpitem.append(group_ls_item[d][2])
            y_med_gpitem.append(group_ls_item[d][1])
        else:
            y_q1_gpitem.append(0)
            y_q3_gpitem.append(0)
            y_med_gpitem.append(0)



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
    title_qnt = "Price of an item (every 5 year)"
    layout = {
        "paper_bgcolor": colors["cream"],
        "plot_bgcolor": colors["cream"],
        "margin": dict(l=5, r=5, t=30, b=30),
        "showlegend": False,
        "xaxis": {"anchor": "x", "title": {"text": "Year"}},
        "barmode": "overlay"  # only affects plot 6
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
    # figure 7 : 1 box chart per 5 year range
    layout["yaxis"] = {"anchor": "x", "title": {"text": "Quantiles of an item's price"}}
    layout["title"] = title_qnt
    fig7 = go.Figure(
        data=[go.Box(x=x, q1=y_q1_gpitem, median=y_med_gpitem, q3=y_q3_gpitem)],
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
    with open(f"{outdir}/fig_idx7.html", mode="w") as out:
        fig7.write_html(file=out, full_html=False, include_plotlyjs="cdn", default_width="100%", default_height=275)

    print("6 DONE")

    # return
    return None


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