import re
from pathlib import Path

from mapbuilder.utils import geo
from mapbuilder.utils.legacy import parse_es_coords


def parse_airport(file_path: Path) -> dict:
    """Parses Runway information from the SCT"""
    pattern = r"^(\w{4})\s+(\d{3}\.\d{3})\s+(\S+)\s+(\S+)\s+(\w)$"

    ads = {}
    in_section = False

    with file_path.open("r", encoding="iso-8859-1") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line.startswith(";"):
                continue

            if line == "[AIRPORT]":
                in_section = True
                continue

            if not in_section:
                continue

            # Next section
            if line.startswith("["):
                break

            match = re.search(pattern, line)

            if match:
                ads[match.group(1)] = geo.Fix(
                    parse_es_coords(match.group(3), match.group(4))
                )

    return ads


def parse_runway(file_path: Path) -> dict:
    """Parses Runway information from the SCT"""
    pattern = r"^(\d{2}[LRC]?)\s+(\d{2}[LRC]?)\s+(\d{3})\s+(\d{3})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\w{4})$"

    ads = parse_airport(file_path)
    runways = {}
    in_section = False

    with file_path.open("r", encoding="iso-8859-1") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line.startswith(";"):
                continue

            if line == "[RUNWAY]":
                in_section = True
                continue

            if not in_section:
                continue

            # Next section
            if line.startswith("["):
                break

            match = re.search(pattern, line)

            if match:
                rwy1 = match.group(1)
                rwy2 = match.group(2)
                rwystr = f"{rwy1}-{rwy2}"
                icao = match.group(9)
                thr1 = geo.Fix(parse_es_coords(match.group(5), match.group(6)))
                thr2 = geo.Fix(parse_es_coords(match.group(7), match.group(8)))

                if icao not in runways:
                    runways[icao] = {}

                runways[icao][rwystr] = {
                    "rwy1": rwy1,
                    "rwy2": rwy2,
                    "brg1": int(match.group(3)),
                    "brg2": int(match.group(4)),
                    "thr1": thr1,
                    "thr2": thr2,
                    "center": ads[icao],
                }

    return runways
