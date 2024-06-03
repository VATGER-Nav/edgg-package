
from pathlib import Path

import logging
import os

class RAWParser:
    result: dict | None

    def __init__(self, file: Path):
        self.result = None
        self.file = file
        
    def parse(self):
        result = {}
        self.parse_recursively(self.file, result)
        self.result = result
        #logging.debug(result)
        return self.result

    def parse_recursively(self, root, result):
        for dirname in os.listdir(root):
            #logging.debug(f"1: {root / dirname}")
            if os.path.isfile(root / dirname):
                filepath = root / dirname
                with (root / dirname).open(
                    encoding="iso-8859-1",
                ) as f:
                    result[Path(*filepath.parts[1:]).as_posix()] = f.read()
            elif os.path.isdir(root / dirname):
                #logging.debug(f"2: {dirname}")
                self.parse_recursively(root / dirname, result)