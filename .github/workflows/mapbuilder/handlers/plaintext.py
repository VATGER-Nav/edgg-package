from pathlib import Path


class PlainTextHandler:
    def handle(self, item: Path) -> str:
        with item.open(encoding="iso-8859-1") as input:
            return input.read()
