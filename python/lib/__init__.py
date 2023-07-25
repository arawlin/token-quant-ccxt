import json


def log_object(o, label=""):
    prefix = label + " " if label else ""
    print(prefix + json.dumps(o, indent=4))
