import re
from pathlib import Path


def parse_sectors(file_path: Path):
    pattern = r"^(\w{4})·([^·]*)·(\d{3})·(\d{3})\s*([NS])(\d{3})\.(\d{2}).(\d{2}).(\d{3}) ([EW])(\d{3})\.(\d{2}).(\d{2}).(\d{3}) ([NS])(\d{3})\.(\d{2}).(\d{2}).(\d{3}) ([EW])(\d{3})\.(\d{2}).(\d{2}).(\d{3})$"

    sectors = {}

    with file_path.open("r") as f:
        for line in f:
            match = re.search(pattern, line)

            if match:
                fir = match.group(1)
                sector = match.group(2)
                levelband = f"{match.group(3)}-{match.group(4)}"

                if fir not in sectors:
                    sectors[fir] = {}

                if sector not in sectors[fir]:
                    sectors[fir][sector] = {}

                if levelband not in sectors[fir][sector]:
                    sectors[fir][sector][levelband] = []

                sectors[fir][sector][levelband].append(match.group(5))

    return sectors
