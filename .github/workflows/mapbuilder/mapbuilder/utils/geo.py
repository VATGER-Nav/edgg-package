from pygeodesy import ellipsoidalExact as geo_model

NM_IN_METERS = 1852


def fix(definition):
    return Fix(definition)


def brg(definition):
    return Brg(definition)


def coord2es(coord: geo_model.LatLon):
    return f"{coord.lat}:{coord.lon}"


def back_bearing(bearing: float) -> float:
    return bearing + 180 if bearing < 180 else bearing - 180


def adjust_bearing(bearing: float, change: float) -> float:
    """Adjusts bearing according to a change, positive values go clockwise."""
    new_bearing = (bearing + change) % 360
    return new_bearing if new_bearing >= 0 else new_bearing + 360


class Brg:
    def __init__(self, bearing):
        self.brg = bearing

    def invert(self) -> "Brg":
        return Brg(self.brg + 180 if self.brg < 180 else self.brg - 180)

    def adjust(self, change: float) -> "Brg":
        """Adjusts bearing according to a change, positive values go clockwise."""
        new_bearing = (self.brg + change) % 360
        return Brg(new_bearing if new_bearing >= 0 else new_bearing + 360)

    def __add__(self, other):
        return self.adjust(other)

    def __sub__(self, other):
        return self.adjust(-other)


def _brg(bearing: float | Brg) -> float:
    if isinstance(bearing, float | int):
        return bearing
    else:
        return bearing.brg


class Fix:
    def __init__(self, coords, lines=None):
        if lines is None:
            self.lines = []
        else:
            self.lines = lines.copy()

        if isinstance(coords, list | tuple):
            self.fix = geo_model.LatLon(coords[0], coords[1])
        elif isinstance(coords, geo_model.LatLon):
            self.fix = coords
        else:
            raise TypeError()

    def coords(self):
        return self.fix

    def es_coords(self):
        return coord2es(self.fix)

    def move_to(self, dist: float, bearing: float | Brg) -> "Fix":
        return Fix(self.fix.destination(dist * NM_IN_METERS, _brg(bearing)), self.lines)

    def move_to_fix(self, fix: "Fix") -> "Fix":
        return Fix(fix.fix, self.lines)

    def line_to(self, dist: float, bearing: float | Brg) -> "Fix":
        dest = self.fix.destination(dist * NM_IN_METERS, _brg(bearing))
        self.lines.append(f"LINE:{coord2es(self.fix)}:{coord2es(dest)}")
        return Fix(self.fix, self.lines)

    def line_to_fix(self, fix: "Fix") -> "Fix":
        self.lines.append(f"LINE:{coord2es(self.fix)}:{coord2es(fix.fix)}")
        return Fix(self.fix, self.lines)

    def line_move_to(self, dist: float, bearing: float | Brg) -> "Fix":
        dest = self.fix.destination(dist * NM_IN_METERS, _brg(bearing))
        self.lines.append(f"LINE:{coord2es(self.fix)}:{coord2es(dest)}")
        self.fix = dest
        return Fix(self.fix, self.lines)

    def line_move_to_fix(self, fix: "Fix") -> "Fix":
        self.lines.append(f"LINE:{coord2es(self.fix)}:{coord2es(fix.fix)}")
        self.fix = fix.fix
        return Fix(self.fix, self.lines)

    def __str__(self):
        return "\n".join(self.lines)

    def __copy__(self):
        return Fix(self.coords, self.lines)


class Line:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return ((self.a == other.a and self.b == other.b)
                or (self.a == other.b and self.b == other.a))

    def __str__(self):
        return f"LINE:{coord2es(self.a)}:{coord2es(self.b)}"
