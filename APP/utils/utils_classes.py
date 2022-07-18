import re


# -------------------------------------------
# classes containing useful stuff for the app
# -------------------------------------------


class Match:
    """
    comparison and matching methods
    """
    @staticmethod
    def set_match_mode(req):
        """
        for katapi.py
        set the matching mode when req["name"], req["level"]=="itm"
        depending on whether req["sell_date"] and req["orig_date"] have been given by the user
        :param req:
        :return:
        """
        if "sell_date" in req.keys() and "orig_date" in req.keys():
            mode = 0
        elif "orig_date" in req.keys():
            mode = 1
        elif "sell_date" in req.keys():
            mode = 2
        else:
            mode = 3
        return mode

    @staticmethod
    def match_date(req_date: str, entry_date: str):
        """
        for routes_api.py
        check whether 2 dates are equal or a date is contained in a date range
        :param req_date: the date (or date range) supplied by user, with format \d{4}(-\d{4})?
        :param entry_date: the date in the catalogue entry (a json)
        :return: match, a bool indicating wether entry_date matches with req_date
        """
        if re.match(r"\d{4}-\d{4}", req_date):
            req_date = req_date.split("-")
            match = int(req_date[0]) < int(entry_date) < int(req_date[1])
        else:
            match = int(req_date) == int(entry_date)

        return match

    @staticmethod
    def match_cat(req_name: str, req_date, entry: dict):
        r"""
        for routes_api.py
        try to match a catalogue in export_catalog.json based on a name and a date or date range
        :param req_name: the name (AUC|LAC|LAV|RDA|OTH) provided by the user
        :param req_date: a date or date range matching \d{4}(-\d{4})?
        :param entry: the json entry we're comparing name and date with
        :return: match, a bool indicating wether the entry matches with req_name and req_date
        """
        match = False
        # if name and cat_type match,
        # extract a year from entry["sell_date"] and try to match the dates.
        # if they match, match is True. else false
        if "cat_type" in entry.keys() and entry["cat_type"] == req_name:
            if req_date is not None and "sell_date" in entry.keys():
                match = Match.match_date(req_date, re.match(r"\d{4}", entry["sell_date"])[0])
        return match

    @staticmethod
    def match_item(req: dict, entry: dict, mode: int):
        """
        for routes_api.py
        try to match a dict entry using a list of dict params
        :param req: the user request on which to perform the match
        :param entry: the json entry (from export_item.json) to try a match with
        :param mode: the mode (an indicator of the supplied query params)
        :return:
        """
        match = False  # whether the entry matches with req or not
        name = None
        sell_date = None
        orig_date = None
        if "author" in entry.keys() and entry["author"] is not None:
            name = entry["author"].lower()
        if "sell_date" in entry.keys() and entry["sell_date"] is not None and entry["sell_date"] != "none":
            try:
                sell_date = re.match(r"\d{4}", entry["sell_date"])[0]
            except TypeError:
                sell_date = None
        if "date" in entry.keys() and entry["date"] is not None and entry["date"] != "none":
            try:
                orig_date = re.match(r"\d{4}", entry["date"])[0]
            except TypeError:
                orig_date = None

        if Match.compare(req["name"], name) is True:
            if mode == 0 and sell_date is not None and orig_date is not None:
                if Match.match_date(req["sell_date"], sell_date) is True and \
                        Match.match_date(req["orig_date"], orig_date) is True:
                    match = True
            elif mode == 1 and orig_date is not None:
                if Match.match_date(req["orig_date"], orig_date) is True:
                    match = True
            elif mode == 2 and sell_date is not None:
                if Match.match_date(req["sell_date"], sell_date) is True:
                    match = True
            elif mode == 4:
                match = True

        return match

    @staticmethod
    def compare(input, compa):
        """
        for routes_api.py
        compare two strings to check if they're the same without punctuation and
        capitals
        :param input: input string
        :param compa: string to compare input with
        :return:
        """
        punct = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '-',
                 '+', '=', '{', '}', '[', ']', ':', ';', '"', "'", '|',
                 '<', '>', ',', '.', '?', '/', '~', '`']
        input = input.lower()
        compa = compa.lower()
        for p in punct:
            input = input.replace(p, "")
            compa = compa.replace(p, "")
        input = re.sub(r"\s+", " ", input)
        compa = re.sub(r"\s+", " ", compa)
        input = re.sub(r"(^\s|\s$)", "", input)
        compa = re.sub(r"(^\s|\s$)", "", compa)
        same = (input == compa)  # true if same, false if not
        return same


class ErrorHandlers:
    """
    error handlers
    """
    @staticmethod
    def error_maker(errors: list, invalid_params: list):
        """
        for routes_api.py
        build a custom json to return error messages

        return format: {"request parameter on which error happened": "error message"}
        :param errors:
        :param invalid_params: invalid research parameters
        :return:
        """
        status_code = 400
        error_log = {
            "__error_type__": "invalid parameters or parameters combination",
            "error_description": {}
        }  # output dictionnary
        error_messages = {
            "level": "you must specify a request level matching: ^(itm|cat_full|cat_stat)$",
            "format": "the format must match: (tei|json)",
            "id": r"invalid id. if level=itm, id must match CAT_\d+_e\d+_d\d+ ; if level=cat(_full|_stat), id must match CAT_\d+",
            "sell_date": r"the format must match: \d{4}(-\d{4})?",
            "orig_date": r"the format must match: \d{4}(-\d{4})?",
            "name+id": "you cannot provide both a name and an id",
            "no_name+id": "you must specify at least a name or an id",
            "cat_stat+name": "when level:cat_stat, name must match: ^(LAC|RDA|LAV|AUC|OTH)$",
            "id_invalid_params": f"invalid parameters with parameter id: {str(invalid_params)}",
            "cat_stat_invalid_params": f"invalid parameters for level=cat_stat: {str(invalid_params)}",
            "cat_full_invalid_params": f"invalid parameters for level=cat_full: {str(invalid_params)}",
            "cat_full_format": "the only valid format with level=cat_full is tei",
            "no_params": "no request parameters were provided"
        }

        # build a dictionnary of error messages
        for e in errors:
            error_log["error_description"][e] = error_messages[e]

        return error_log, status_code