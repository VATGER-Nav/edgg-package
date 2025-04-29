from itertools import chain
from pathlib import Path

import numpy as np
import shapely
import shapely.ops
from jinja2 import Environment, FileSystemLoader
from more_itertools import unique_everseen
from shapely import Geometry, Polygon

from mapbuilder.data.aixm2 import AIXMFeature
from mapbuilder.utils.ad import render_cl, render_runways
from mapbuilder.utils.ecl import draw_ecl_dashes, draw_loc_tick, draw_marker_ticks
from mapbuilder.utils.geo import brg, fix
from mapbuilder.utils.sidstar import render_sid


class JinjaHandler:
    def __init__(self, data, config):
        self.data = data
        self.config = config

    def handle(self, item: Path) -> str:
        file_loader = FileSystemLoader(item.parent)
        jinja_env = Environment(loader=file_loader)
        jinja_env.globals.update(
            data=self.data,
            runways=self.config["runways"],
            combine=combine,
            geoms=geoms,
            concat=concat,
            ecl_dashes=draw_ecl_dashes,
            marker_ticks=draw_marker_ticks,
            loc_tick=draw_loc_tick,
            render_sid=render_sid,
            fix=fix,
            brg=brg,
            render_runways=render_runways,
            render_cl=render_cl,
            render_sectorlines=render_sectorlines,
            sector_sub=sector_sub,
            sector_and=sector_and,
        )
        jinja_env.filters.update(
            geoms=geoms,
            simplify=simplify,
            to_line=to_line,
            to_coordline=to_coordline,
            to_coordtype=to_coordtype,
            to_poly=to_poly,
            join_segments=join_segments,
            filter_smaller_than=filter_smaller_than,
            envelope=envelope,
            to_text=to_text,
            to_text_buffer=to_text_buffer,
            to_symbol=to_symbol,
        )

        return jinja_env.get_template(item.name).render()


def geoms(features: list[AIXMFeature] | AIXMFeature) -> list[Geometry]:
    """Extracts the geometries from the given (list of) feature(s)"""
    if isinstance(features, list):
        result = [geometry for instance in features for geometry in instance.geometries]
    else:
        result = features.geometries

    return result


def combine(geometries: list[Geometry]) -> Geometry:
    combined = shapely.ops.unary_union([Polygon(geo) for geo in geometries])
    # combined = shapely.ops.unary_union(geometries)
    #   return combined.exterior
    return shapely.buffer(combined, 0.00000000000001)


def concat(base: dict, keys: list[str]) -> list:
    """
    Concatenates the given keys from a given base dict to a flat list
    :param base: Common base dict for the keys
    :param keys: keys to concatenate
    :return: Flat list of concatenated values
    """
    result = []

    for key in keys:
        result.extend(base.get(key, []))

    return result


def to_text_buffer(geometry, label: str, color: str, adapt_to_length=True):
    point = geometry[0] if isinstance(geometry, list) else geometry

    if point is None:
        return ""

    lines = []
    distance = 0.00008
    labeltext, _, _ = label.partition("#")
    if adapt_to_length:
        distance += 0.00001 * len(labeltext)
    buffer = shapely.buffer(point, distance).envelope.boundary

    _render_polygon(lines, [buffer], color, False)

    return "\n".join(lines)


def to_text(geometry, label: str):
    point = geometry[0] if isinstance(geometry, list) else geometry

    if point is None:
        return ""

    labeltext, _, _ = label.partition("#")
    return f"TEXT:{coord2es(point.coords[0])}:{labeltext}"


def to_symbol(geometry, symbol):
    point = geometry[0] if isinstance(geometry, list) else geometry

    if point is None:
        return ""

    return f"SYMBOL:{symbol}:{coord2es(point.coords[0])}"


def _get_geoms(thing):
    """Extracts the geometries from either an AIXMFeature or geometry object"""
    if isinstance(thing, list):
        if len(thing) == 0:
            return []

        if isinstance(thing[0], AIXMFeature):
            return [geometry for instance in thing for geometry in instance.geometries]
        else:
            return thing
    elif isinstance(thing, AIXMFeature):
        return thing.geometries
    elif isinstance(thing, shapely.MultiLineString):
        return thing.geoms
    elif isinstance(thing, shapely.LineString | shapely.LinearRing):
        return [thing]
    elif isinstance(thing, shapely.Polygon):
        return [thing.exterior]
    elif isinstance(thing, shapely.geometry.base.GeometrySequence | np.ndarray):
        return thing
    else:
        return []


def to_line(geometries, designator: str):
    lines = [f"// {designator}"] if designator else []

    _render_linestring(lines, _get_geoms(geometries))

    return "\n".join(lines)


def to_coordline(geometries, designator: str):
    lines = [f"// {designator}"] if designator else []

    _render_coords(lines, _get_geoms(geometries))

    lines.extend(("COORDLINE", ""))
    return "\n".join(lines)


def filter_smaller_than(geometries, threshold):
    geo = _get_geoms(geometries)
    if isinstance(geo, list):
        return list(filter(lambda geometry: geometry.envelope.area >= threshold, geo))


def envelope(geometries):
    return shapely.envelope(geometries)


def to_poly(geometries, designator: str, color: str | None = None, coordpoly=False):
    lines = [f"// {designator}"] if designator else []

    _render_polygon(lines, _get_geoms(geometries), color, coordpoly)

    if coordpoly:
        lines.extend((f"COORDPOLY:{coordpoly}", ""))

    return "\n".join(lines)


def _render_polygon(lines, polygons, color=None, coordpoly=False):
    if not coordpoly and color is not None:
        lines.append(f"COLOR:{color}")
    else:
        lines.append("")

    for polygon in polygons:
        if coordpoly:
            if color is not None:
                lines.append(f"COLOR:{color}")
            else:
                lines.append("")
        else:
            lines.append("COORDTYPE:OTHER:REGION")
        for point in polygon.coords:
            lines.append(f"COORD:{coord2es((point[0], point[1]))}")


def _render_coords(lines, linestring):
    for geometry in linestring:
        for point in geometry.coords:
            lines.append(f"COORD:{point[0]}:{point[1]}")

        lines.append("")


def _render_linestring(lines, linestring):
    for geometry in linestring:
        count = len(geometry.coords)

        for idx, point in enumerate(geometry.coords):
            if idx == count - 1:
                break

            lines.append(
                f"LINE:{coord2es((point[0], point[1]))}"
                f":{coord2es((geometry.coords[idx + 1][0], geometry.coords[idx + 1][1]))}",
            )
        lines.append("")


def simplify(geometries, tolerance):
    geo = _get_geoms(geometries)
    if isinstance(geo, list):
        return [shapely.simplify(geometry, tolerance) for geometry in geo]
    else:
        return shapely.simplify(geo, tolerance)


def join_segments(lines):
    return shapely.ops.linemerge(_get_geoms(lines))


def coord2es(coord):
    return f"{coord[0]}:{coord[1]}"


def render_sectorlines(*lines):
    unique_lines = list(unique_everseen(chain(*lines)))
    return "\n".join(map(str, unique_lines))


def sector_sub(a, b):
    return [item for item in a if item not in b]


def sector_and(a, b):
    return [item for item in a if item in b]

def to_coordtype(geometries, designator: str, color: str | None = None, areatype: str = "OTHER", drawtype: str = "REGION", hatchtype: str | None = None ):
    lines = [f"// {designator}"] if designator else []

    if color:
        lines.append(f"COLOR:{color}")

    for geometry in _get_geoms(geometries):
        if hatchtype is None:
            lines.append(f"COORDTYPE:{areatype}:{drawtype}")
        else:
            lines.append(f"COORDTYPE:{areatype}:{drawtype}:{hatchtype}")

        for point in geometry.coords:
            lines.append(f"COORD:{coord2es((point[0], point[1]))}")
    
    return "\n".join(lines)