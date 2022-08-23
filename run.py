import argparse

from APP.app import app
from APP.utils.api_classes.client_server import ErrorLog


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test",
                        help="run a series of tests on the API.",
                        action="store_true")
    args = parser.parse_args()

    # run tests
    if args.test:
        # extra imports to run the tests
        from APP.test.api_test import run
        run()  # run tests

    # normal functionning
    else:
        ErrorLog.create_logger()
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(port=5000, debug=True)
