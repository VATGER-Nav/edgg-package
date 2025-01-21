from pathlib import Path

import xmltodict
from shapely import LinearRing, LineString, Point


class KMLParser:
    result: dict | None

    def __init__(self, file: Path, root: str | None):
        self.result = None
        self.root = root
        with file.open("rb") as f:
            self.xml_root = xmltodict.parse(f)

    @staticmethod
    def parse_pos_list(raw_geometry):
        parts = raw_geometry.split(" ")

        geometries = []

        for part in parts:
            raw_coord = part.split(",")
            geometries.append((float(raw_coord[1]), float(raw_coord[0])))

        return geometries

    def parse(self):
        result = {}
        self.parse_recursively(self.xml_root["kml"], result)
        self.result = result
        if self.root is not None and self.root in self.result:
            self.result = self.result[self.root]
        return self.result

    def parse_recursively(self, root, result):
        if "Document" in root:
            self.parse_recursively(root["Document"], result)

        if "Folder" in root:
            for folder in ensure_list(root["Folder"]):
                name = folder["name"]
                result[name] = {}
                self.parse_recursively(folder, result[name])

        if "Placemark" in root:
            for placemark in ensure_list(root["Placemark"]):
                if "LineString" in placemark:
                    geom = LineString(self.parse_pos_list(placemark["LineString"]["coordinates"]))
                elif "Polygon" in placemark:
                    geom = LinearRing(
                        self.parse_pos_list(
                            placemark["Polygon"]["outerBoundaryIs"]["LinearRing"]["coordinates"],
                        ),
                    )
                elif "Point" in placemark:
                    geom = Point(self.parse_pos_list(placemark["Point"]["coordinates"]))
                elif "MultiGeometry" in placemark:
                    if len(placemark["MultiGeometry"]) != 1:
                        msg = f"Placemark {placemark['name']}: in MultiGeometry only one type of Geometry is allowed"
                        raise ValueError(msg)
                    
                    geom = self.parse_multigeometry(placemark["MultiGeometry"])
                else:
                    msg = f"Placemark {placemark} unknown"
                    raise ValueError(msg)

                name = placemark["name"]
                if name not in result:
                    result[name] = [geom]
                else:
                    result[name].append(geom)
    
    def parse_multigeometry(self, root) -> list:
        geom = []

        if "LineString" in root:
            for linestring in ensure_list(root["LineString"]):
                geom.append(LineString(KMLParser.parse_pos_list(linestring["coordinates"])))
        elif "Polygon" in root:
            for polygon in ensure_list(root["Polygon"]):
                geom.append(LinearRing(
                    KMLParser.parse_pos_list(
                        polygon["outerBoundaryIs"]["LinearRing"]["coordinates"],
                    )
                ))
        elif "Point" in root:
            for point in ensure_list(root["Point"]):
                geom.append(Point(KMLParser.parse_pos_list(point["coordinates"])))
        else:
            msg = f"Geometry {root} unknown"
            raise ValueError(msg)
        
        return geom


def ensure_list(thing):
    if isinstance(thing, list):
        return thing
    else:
        return [thing]
