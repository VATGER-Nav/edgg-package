from mapbuilder.utils.geo import Brg, Fix, back_bearing


def extrapolate_rwy(rwy_info, count: int, dist: float = 1) -> list[Fix]:
    """Extrapolates count points from the runway threshold, each spaced dist nautical miles apart
    from each other."""
    thr = Fix(rwy_info["thr"])
    points = [thr]
    brg = back_bearing(rwy_info["bearing"])

    for step in range(0, count):
        points.append(thr.move_to(dist=(step + 1) * dist, bearing=brg))

    return points


def draw_ecl_dashes(rwy_info, count: int, dist: float = 1, start_blank: bool = True):
    points = extrapolate_rwy(rwy_info, count, dist)

    lines = []
    draw = not start_blank
    for idx in range(0, len(points)):
        if draw and idx + 1 < len(points):
            lines.append(f"LINE:{points[idx].es_coords()}:{points[idx + 1].es_coords()}")

        draw = not draw

    return "\n".join(lines)


def draw_loc_tick(rwy_info, gap: float, length: float):
    brg = Brg(rwy_info["bearing"]) + 90
    return str(Fix(rwy_info["loc"]).move_to(gap, brg).line_to(length, brg))


def draw_marker_ticks(rwy_info, at: list, gap: float, length: float):
    lines = []
    brg = Brg(rwy_info["bearing"]).invert()
    tick_brg = brg + 90
    for dist in at:
        base = Fix(rwy_info["thr"]).move_to(dist, brg)

        lines.extend((
            str(base.move_to(gap, tick_brg).line_to(length, tick_brg)),
            str(base.move_to(-gap, tick_brg).line_to(-length, tick_brg)),
        ))

    return "\n".join(lines)
