import logging
import re
import shutil
import tempfile
import time
import zipfile
from io import BytesIO
from pathlib import Path
from urllib import request


class Cache:
    """A rather primitive caching mechanism for resources from the interwebs.
    Unzips zipfiles (hello DFS)."""

    def __init__(self, cache_location: Path) -> None:
        self.cache_location = cache_location

        if not cache_location.exists():
            cache_location.mkdir()

    def get(self, item: str, url: str, ttl: int = 24) -> Path:
        cache_path = self.__path(item)
        if cache_path.exists():
            mtime = cache_path.stat().st_mtime
            if mtime < time.time() - ttl * 3600:
                self.fetch(url, cache_path)
        else:
            self.fetch(url, cache_path)

        return cache_path

    def fetch(self, url: str, target_file: Path):
        logging.debug(f"Fetching {url}...")
        if target_file.exists():
            target_file.unlink()

        with request.urlopen(url) as response:
            content = BytesIO(response.read())

        if zipfile.is_zipfile(content):
            logging.debug("Unzipping...")
            with zipfile.ZipFile(content, "r") as zip_file:
                file_list = zip_file.namelist()
                if len(file_list) != 1:
                    raise ValueError("The ZIP file does not contain one file.")  # noqa

                with tempfile.TemporaryDirectory() as tempdir:
                    logging.debug(f"Extracting {file_list[0]} to temporary dir {tempdir}")
                    zip_file.extract(file_list[0], tempdir)
                    shutil.move(Path(tempdir) / file_list[0], target_file)
        else:
            with target_file.open("wb") as f:
                f.write(content.getbuffer())

    def __path(self, item: str) -> Path:
        """Returns the path name for a given item in the cache."""
        return self.cache_location / re.sub(r'[\\/:\*\?"<>\|]', "", item)
