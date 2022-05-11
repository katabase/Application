import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))  # root directory: APP
TEMPLATES = os.path.join(ROOT, "templates")  # templates directory
STATIC = os.path.join(ROOT, "static")  # statics directory
DATA = os.path.join(ROOT, "data")  # data directory
