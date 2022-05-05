from flask import Flask
from fnmatch import filter
import atexit
import glob
import os

from .constantes import TEMPLATES, STATIC


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
    figs = glob.glob(os.path.join(TEMPLATES, "partials", "fig_*"))
    print(figs)
    for f in figs:
        os.remove(f)
    return None


atexit.register(cleaner)


# import the routes
from .routes import *
