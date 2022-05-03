from flask import Flask
import os

from .constantes import TEMPLATES, STATIC


app = Flask(
    "Application",
    template_folder=TEMPLATES,
    static_folder=STATIC
)


from . import path  # import the routes
