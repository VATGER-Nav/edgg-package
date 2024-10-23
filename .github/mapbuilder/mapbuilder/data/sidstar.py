import re
from pathlib import Path


def parse_sidstar(file_path: Path) -> dict:
    pattern = r"^(SID|STAR):(\w{4}):(\d\d\w?):(\w+):(.*?)(?:$|\s?;)"

    procs = {"SID": {}, "STAR": {}}
    in_section = False

    with file_path.open("r", encoding="iso-8859-1") as f:
        for raw_line in f:
            line = raw_line.strip()
            if line.startswith(";"):
                continue

            if line == "[SIDSSTARS]":
                in_section = True
                continue

            if not in_section:
                continue

            # Next section
            if line.startswith("["):
                break

            match = re.search(pattern, line)

            if match:
                ptype = match.group(1)
                ad = match.group(2)
                rwy = match.group(3)
                proc = match.group(4)
                wpts = match.group(5)

                if ad not in procs[ptype]:
                    procs[ptype][ad] = {}

                if rwy not in procs[ptype][ad]:
                    procs[ptype][ad][rwy] = {}

                procs[ptype][ad][rwy][proc] = wpts.split(" ")

    return procs
