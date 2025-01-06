from itertools import chain
from pathlib import Path

import numpy as np
import shapely
import shapely.ops
from jinja2 import Environment, FileSystemLoader
from more_itertools import unique_everseen
from shapely import MultiLineString, Geometry, Polygon

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
        )
        jinja_env.filters.update(
            geoms=geoms,
            simplify=simplify,
            to_line=to_line,
            to_coordline=to_coordline,
            to_poly=to_poly,
            join_segments=join_segments,
            filter_smaller_than=filter_smaller_than,
            envelope=envelope,
            to_text=to_text,
            to_text_buffer=to_text_buffer,
            to_symbol=to_symbol,
            to_multipoly=to_multipoly,
            to_multiline=to_multiline,
            to_multicoordline=to_multicoordline,
            to_multisymbol=to_multisymbol,
            to_multitext=to_multitext,
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

    _render_polygon(lines, [buffer], color)

    return "\n".join(lines)


def to_text(geometry, label: str):
    point = geometry[0] if isinstance(geometry, list) else geometry

    if point is None:
        return ""

    labeltext, _, _ = label.partition("#")
    return f"TEXT:{coord2es(point.coords[0])}:{labeltext}"

def to_multitext(geometries, label: str):
    lines = []
    labeltext, _, _ = label.partition("#")

    for geometry in geometries:
        for point in geometry:
            if point is None:
                lines.append("")
                continue

            lines.append(f"TEXT:{coord2es(point.coords[0])}:{labeltext}")

    return "\n".join(lines)


def to_symbol(geometry, symbol):
    point = geometry[0] if isinstance(geometry, list) else geometry

    if point is None:
        return ""

    return f"SYMBOL:{symbol}:{coord2es(point.coords[0])}"

def to_multisymbol(geometries, symbol):
    lines = []

    for geometry in geometries:
        for point in geometry:
            if point is None:
                lines.append("")
                continue

            lines.append(f"SYMBOL:{symbol}:{coord2es(point.coords[0])}")

    return "\n".join(lines)


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


def to_multiline(geometries, designator: str):
    lines = [f"// {designator}"] if designator else []

    for geometry in geometries:
        if isinstance(geometry, MultiLineString):
            _render_linestring(lines, _get_geoms(geometry))
            continue

        for linestring in geometry:
            _render_linestring(lines, _get_geoms(linestring))

    return "\n".join(lines)


def to_coordline(geometries, designator: str):
    lines = [f"// {designator}"] if designator else []

    _render_coords(lines, _get_geoms(geometries))

    lines.extend(("COORDLINE", ""))
    return "\n".join(lines)


def to_multicoordline(geometries, designator: str):
    lines = [f"// {designator}"] if designator else []

    for geometry in geometries:
        if isinstance(geometry, MultiLineString):
            _render_linestring(lines, _get_geoms(geometry))
            lines.extend(("COORDLINE", ""))
            continue

        for linestring in geometry:
            _render_coords(lines, _get_geoms(linestring))

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

    _render_polygon(lines, _get_geoms(geometries), color)

    if coordpoly:
        lines.extend((f"COORDPOLY:{coordpoly}", ""))

    return "\n".join(lines)

def to_multipoly(geometries, designator: str, color: str | None = None, coordpoly=False):
    lines = [f"// {designator}"] if designator else []

    for geometry in geometries:
        for polygon in geometry:
            _render_polygon(lines, _get_geoms(polygon), color)

            if coordpoly:
                lines.append(f"COORDPOLY:{coordpoly}")

    return "\n".join(lines)


def _render_polygon(lines, polygons, color=None):
    for polygon in polygons:
        if color is not None:
            lines.append(f"COLOR:{color}")
        else:
            lines.append("")

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


def join_segments(geometries):
    if isinstance(geometries, list):
        return [shapely.ops.linemerge(_get_geoms(geometry)) for geometry in geometries]
    else:
        return shapely.ops.linemerge(_get_geoms(geometries))


def coord2es(coord):
    return f"{coord[0]}:{coord[1]}"


def render_sectorlines(*lines):
    unique_lines = list(unique_everseen(chain(*lines)))
    return "\n".join(map(str, unique_lines))
