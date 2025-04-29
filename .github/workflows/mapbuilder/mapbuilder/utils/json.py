from json import load


def load_json(filename):
    with open(filename, "r") as f:
        return load(f)
