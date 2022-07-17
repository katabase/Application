from flask import Flask
from os.path import join
from glob import glob
import atexit
import os

from .utils.constantes import TEMPLATES, STATIC


# configure the app
app = Flask(
    "Katabase",
    template_folder=TEMPLATES,
    static_folder=STATIC
)


# delete the files created during the session when the app is exited
def cleaner():
    """
    function to delete the figures created when using the app
    :return: None
    """
    figs = glob.glob(join(TEMPLATES, "partials", "fig_*.html"))
    for f in figs:
        os.remove(f)
    return None


atexit.register(cleaner)


# import the routes
from .routes.routes_generic import *
from .routes.routes_api import *
