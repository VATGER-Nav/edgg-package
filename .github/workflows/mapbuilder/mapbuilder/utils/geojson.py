from shapely.io import from_geojson


def load_geojson(filename):
    with open(filename, "rb") as f:
        return from_geojson(f.read())
