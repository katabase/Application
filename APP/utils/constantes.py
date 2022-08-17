import os

UTILS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__))))  # current directory
ROOT = os.path.abspath(os.path.join(UTILS, os.pardir))  # root directory: APP
TEST = os.path.abspath(os.path.join(ROOT, "test"))  # test directory
TEMPLATES = os.path.join(ROOT, "templates")  # templates directory
STATIC = os.path.join(ROOT, "static")  # statics directory
DATA = os.path.join(ROOT, "data")  # data directory
