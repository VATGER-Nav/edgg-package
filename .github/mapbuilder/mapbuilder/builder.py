import logging
from datetime import UTC, datetime
from pathlib import Path

from .cache import Cache
from .data.aixm2 import parse_aixm
from .data.kml import KMLParser
from .data.rwy import parse_runway
from .data.sectors import parse_sectors, sectors_to_lines
from .data.sidstar import parse_sidstar
from .dfs import aixm
from .handlers.jinja import JinjaHandler
from .handlers.plaintext import PlainTextHandler

SUFFIXES = [".txt", ".jinja"]


class Builder:
    def __init__(self, source_dir, target_dir, cache_dir, config):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.cache = Cache(cache_dir)
        self.config = config

        self.data = {}
        self.dfs_datasets = None
        for data_source in config["data"]:
            data_source_type = config["data"][data_source]["type"]
            if data_source_type == "aixm":
                logging.debug(f"Loading AIXM source {data_source}...")
                self.data[data_source] = self.__load_aixm(
                    data_source, config["data"][data_source]["source"]
                )
            elif data_source_type == "kml":
                logging.debug(f"Loading KML source {data_source}...")
                data_root = None
                if "root" in config["data"][data_source]:
                    data_root = config["data"][data_source]["root"]
                parser = KMLParser(
                    source_dir / config["data"][data_source]["source"], data_root
                )
                self.data[data_source] = parser.parse()
            elif data_source_type == "raw":
                logging.debug(f"Loading raw source {data_source}...")
                with (source_dir / config["data"][data_source]["source"]).open(
                        encoding="iso-8859-1",
                ) as f:
                    self.data[data_source] = f.read()
            elif data_source_type == "ese":
                logging.debug(f"Loading ESE source {data_source}...")
                self.data[data_source] = {
                    "SIDSTAR": parse_sidstar(
                        source_dir / config["data"][data_source]["source"]
                    ),
                }
            elif data_source_type == "sct":
                logging.debug(f"Loading SCT source {data_source}...")
                self.data[data_source] = {
                    "RUNWAY": parse_runway(
                        source_dir / config["data"][data_source]["source"]
                    ),
                }
            elif data_source_type == "sectors":
                logging.debug(f"Loading sectors source {data_source}...")
                fixes = parse_sectors(source_dir / config["data"][data_source]["source"])
                self.data[data_source] = {
                    "fixes": fixes,
                    "lines": sectors_to_lines(fixes),
                }
            else:
                logging.error(f"Unknown data source type for data source {data_source}")

        self.jinja_handler = JinjaHandler(self.data, self.config)

    def __load_aixm(self, name: str, src: str):
        if src.startswith("aixm:dfs"):
            _, _, amdt, leaf = src.split(":")
            amdt_id = int(amdt)

            if self.dfs_datasets is None:
                self.dfs_datasets = aixm.get_dfs_aixm_datasets(self.cache)

            url = aixm.get_dfs_aixm_url(self.dfs_datasets[amdt_id], amdt_id, leaf)
            if url is None:
                logging.error(f"Cannot get AIXM source URL for dataset {name}")
                return {}
            return parse_aixm(self.cache.get(f"aixm-{name}", url, 96))
        if src.startswith("http"):
            return parse_aixm(self.cache.get(f"aixm-{name}", src, 96))
        else:
            return parse_aixm(self.source_dir / src)

    def build(self):
        for profile in self.config["profiles"]:
            self.build_profile(profile)

    def __best_item(self, profile_id, item):
        """Looks for the best file for an item."""
        profile_candidates = [
            profile_id,
            *self.config["profiles"][profile_id]["aliases"],
        ]

        for candidate in profile_candidates:
            for suffix in SUFFIXES:
                candidate_file = item / f"{candidate}{suffix}"
                if candidate_file.is_file():
                    return candidate_file

        return None

    def __handle_item(self, item):
        if item.suffix == ".txt":
            return PlainTextHandler().handle(item)
        elif item.suffix == ".jinja":
            return self.jinja_handler.handle(item)
        else:
            logging.warning(f"No handler for file type {item.suffix} known. Skipping.")
            return None

    def build_profile(self, profile_id: str):
        logging.info(f"Building profile {profile_id}...")

        for map_data in self.config["profiles"][profile_id]["maps"]:
            self.build_profile_map(profile_id, map_data)

    def build_profile_map(self, profile_id: str, map_data: dict):
        map_id = map_data["map"]
        target_file = map_data["target"]
        maps_root = self.source_dir / "maps" / map_id

        if not maps_root.is_dir():
            logging.error("No map directory. Bailing out.")
            return

        header = f"// {map_id} {profile_id}\n// Auto-generated by mapbuilder. Do not edit manually."

        if map_data.get("timestamp"):
            header = header + f"\n// Generation time: {datetime.now(tz=UTC)}"

        profile_contents = [header]

        self.build_visitor(profile_id, maps_root, profile_contents)

        profile_content = "\n\n".join(profile_contents)

        with (self.target_dir / Path(target_file)).open(
                mode="w",
                encoding="iso-8859-1",
        ) as tgt_file:
            tgt_file.write(profile_content)

        logging.info(f"Built {map_id}.")

    def build_visitor(self, profile_id, rootdir, profile_contents):
        # Possibly inefficient, but we do not have a large number of files (hopefully)
        for item in sorted(rootdir.iterdir()):
            logging.debug(f"Processing item {item}")

            # if regular subdirectory
            if item.is_dir() and item.suffix != ".d":
                self.build_visitor(profile_id, item, profile_contents)
            else:
                # if per-profile content
                if item.is_dir() and item.suffix == ".d":
                    best_item = self.__best_item(profile_id, item)

                    if best_item:
                        item = best_item

                content = self.__handle_item(item)
                if content:
                    profile_contents.append(content)
