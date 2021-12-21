import yaml

_config = None


def load_config(file):
    global _config
    with open(file) as file:
        _config = yaml.load(file, Loader=yaml.FullLoader)


def get_config():
    return _config
