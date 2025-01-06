import re
from pathlib import Path

from pygeodesy import ellipsoidalExact as geo_model

from mapbuilder.utils.geo import Line
from mapbuilder.utils.legacy import parse_es_coords


def parse_sectors(file_path: Path):
    pattern = r"^(\w{4})·([^·]*)·(\d{3})·(\d{3})\s*(\S*) (\S*) (\S*) (\S*)$"

    sectors = {}

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            match = re.search(pattern, line.strip())

            if match:
                fir = match.group(1)
                sector = match.group(2)
                level_band = f"{match.group(3)}-{match.group(4)}"

                if fir not in sectors:
                    sectors[fir] = {}

                if sector not in sectors[fir]:
                    sectors[fir][sector] = {}

                if level_band not in sectors[fir][sector]:
                    sectors[fir][sector][level_band] = []

                sectors[fir][sector][level_band].append(
                    geo_model.LatLon(*parse_es_coords(match.group(5), match.group(6)))
                )

    return sectors


def sectors_to_lines(sectors: dict) -> dict:
    lines = {}
    for fir, fir_sectors in sectors.items():
        if fir not in lines:
            lines[fir] = {}

        for fir_sector, level_bands in fir_sectors.items():
            if fir_sector not in lines[fir]:
                lines[fir][fir_sector] = {}

            for level_band, fixes in level_bands.items():
                lines[fir][fir_sector][level_band] = []
                count = len(fixes)

                for idx, fix in enumerate(fixes):
                    if idx == count - 1:
                        lines[fir][fir_sector][level_band].append(Line(fix, fixes[0]))
                        break

                    lines[fir][fir_sector][level_band].append(Line(fix, fixes[idx + 1]))

    return lines
