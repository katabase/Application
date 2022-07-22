from APP.app import app
from APP.utils.utils_classes import ErrorLog

if __name__ == "__main__":
    ErrorLog.create_logger()
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(port=5000, debug=True)
