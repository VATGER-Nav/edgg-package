import fiona


def load_geopackage(filename, layers) -> dict:
    return {layer: list(fiona.open(filename, layer=layer)) for layer in layers}
