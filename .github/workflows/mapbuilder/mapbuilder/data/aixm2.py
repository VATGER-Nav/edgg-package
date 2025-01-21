from dataclasses import dataclass, field

from lxml import etree
from shapely import Geometry, LinearRing, LineString

AIXM_NAMESPACES = {
    "gss": "http://www.isotc211.org/2005/gss",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "message": "http://www.aixm.aero/schema/5.1.1/message",
    "gsr": "http://www.isotc211.org/2005/gsr",
    "gco": "http://www.isotc211.org/2005/gco",
    "gml": "http://www.opengis.net/gml/3.2",
    "gmd": "http://www.isotc211.org/2005/gmd",
    "aixm": "http://www.aixm.aero/schema/5.1.1",
    "xlink": "http://www.w3.org/1999/xlink",
    "gts": "http://www.isotc211.org/2005/gts",
    "gmx": "http://www.isotc211.org/2005/gmx",
}

AIXM_POLY_FEATURES = [
    "TaxiwayElement",
    "RunwayElement",
    "RunwayBlastPad",
    "RunwayProtectArea",
    "ApronElement",
    "DeicingArea",
    "VerticalStructure",
    "WorkArea",
    "RunwayMarking",
    "TaxiHoldingPositionMarking",
]

AIXM_LINE_FEATURES = ["GuidanceLine", "GuidanceLineMarking", "TaxiwayMarking"]


@dataclass
class AIXMFeature:
    """A feature extracted from AIXM data"""

    id: str
    feature: str
    geometries: list[Geometry]
    geometry_type: str
    type: str | None = field(default=None)
    name: str | None = field(default=None)
    style: str | None = field(default=None)
    color: str | None = field(default=None)
    designator: str | None = field(default=None)
    apron: str | None = field(default=None)
    taxiway: str | None = field(default=None)
    marked_taxiway: str | None = field(default=None)
    marking_location: str | None = field(default=None)
    marked_guidance_line: str | None = field(default=None)


@dataclass
class AIXMApron:
    id: str
    name: str
    abandoned: bool
    surface: str | None = field(default=None)


@dataclass
class AIXMTaxiway:
    id: str
    designator: str
    abandoned: bool
    type: str | None = field(default=None)
    width: float | None = field(default=None)
    surface: str | None = field(default=None)


def _ns(ns: str, name: str) -> str:
    return f"{{{AIXM_NAMESPACES[ns]}}}{name}"


AIXM_POLY_TAGS = [_ns("aixm", ft) for ft in AIXM_POLY_FEATURES]
AIXM_LINE_TAGS = [_ns("aixm", ft) for ft in AIXM_LINE_FEATURES]
AIXM_TAGS = [*AIXM_POLY_TAGS, *AIXM_LINE_TAGS]
APRON_TAG = _ns("aixm", "Apron")
TAXIWAY_TAG = _ns("aixm", "Taxiway")


def parse_pos_list(raw_geometry):
    """Parses geometries into lat/lon pairs"""
    geometry_parts = iter(raw_geometry.split(" "))

    geometry = []

    for geo in geometry_parts:
        x = float(geo)
        y = float(next(geometry_parts))
        geometry.append((x, y))

    return geometry


def resolve_links(dataset):
    """Resolves apron and taxiway links"""

    for _, apron_element in dataset["ApronElement"].items():
        apron_name = dataset["_Apron"][apron_element.apron].name

        if apron_name not in dataset["ApronElementByApron"]:
            dataset["ApronElementByApron"][apron_name] = [apron_element]
        else:
            dataset["ApronElementByApron"][apron_name].append(apron_element)

    for _, line in dataset["GuidanceLine"].items():
        twy_designator = line.designator

        if twy_designator not in dataset["GuidanceLineByDesig"]:
            dataset["GuidanceLineByDesig"][twy_designator] = [line]
        else:
            dataset["GuidanceLineByDesig"][twy_designator].append(line)

    for _, structure in dataset["VerticalStructure"].items():
        structure_name = structure.name

        if structure_name not in dataset["VerticalStructureByName"]:
            dataset["VerticalStructureByName"][structure_name] = [structure]
        else:
            dataset["VerticalStructureByName"][structure_name].append(structure)

    if "TaxiwayMarking" in dataset:
        for _, marking in dataset["TaxiwayMarking"].items():
            twy_desig = dataset["_Taxiway"][marking.marked_taxiway].designator

            if twy_desig not in dataset["TaxiwayMarkingByDesig"]:
                dataset["TaxiwayMarkingByDesig"][twy_desig] = [marking]
            else:
                dataset["TaxiwayMarkingByDesig"][twy_desig].append(marking)


def parse_aixm(xml_file):
    result = {
        "_Apron": {},
        "ApronElementByApron": {},
        "GuidanceLineByDesig": {},
        "VerticalStructureByName": {},
        "TaxiwayMarkingByDesig": {},
        "_Taxiway": {},
    }
    context = etree.iterparse(xml_file)

    for _action, elem in context:
        if elem.tag == APRON_TAG:
            apn_id = elem.findtext("gml:identifier", namespaces=AIXM_NAMESPACES)
            result["_Apron"][apn_id] = AIXMApron(
                id=apn_id,
                name=elem.findtext(".//aixm:name", namespaces=AIXM_NAMESPACES),
                surface=elem.findtext(".//aixm:composition", namespaces=AIXM_NAMESPACES),
                abandoned=elem.findtext(".//aixm:abandoned", namespaces=AIXM_NAMESPACES) == "YES",
            )

            elem.clear()
        elif elem.tag == TAXIWAY_TAG:
            twy_id = elem.findtext("gml:identifier", namespaces=AIXM_NAMESPACES)
            result["_Taxiway"][twy_id] = AIXMTaxiway(
                id=twy_id,
                designator=elem.findtext(".//aixm:designator", namespaces=AIXM_NAMESPACES),
                type=elem.findtext(".//aixm:type", namespaces=AIXM_NAMESPACES),
                width=elem.findtext(".//aixm:width", namespaces=AIXM_NAMESPACES),
                surface=elem.findtext(".//aixm:composition", namespaces=AIXM_NAMESPACES),
                abandoned=elem.findtext(".//aixm:abandoned", namespaces=AIXM_NAMESPACES) == "YES",
            )

            elem.clear()
        elif elem.tag in AIXM_TAGS:
            feature_type = elem.tag.split("}")[1]
            feature_id = elem.findtext("gml:identifier", namespaces=AIXM_NAMESPACES)
            is_poly = elem.tag in AIXM_POLY_TAGS

            feature = AIXMFeature(
                id=feature_id,
                feature=feature_type,
                type=elem.findtext(".//aixm:type", namespaces=AIXM_NAMESPACES),
                name=elem.findtext(".//aixm:name", namespaces=AIXM_NAMESPACES),
                designator=elem.findtext(".//aixm:designator", namespaces=AIXM_NAMESPACES),
                color=elem.findtext(".//aixm:colour", namespaces=AIXM_NAMESPACES),
                style=elem.findtext(".//aixm:style", namespaces=AIXM_NAMESPACES),
                marking_location=elem.findtext(
                    ".//aixm:markingLocation",
                    namespaces=AIXM_NAMESPACES,
                ),
                geometries=[],
                geometry_type="poly" if is_poly else "line",
            )

            if feature_type == "ApronElement":
                apron_link = elem.find(".//aixm:associatedApron", namespaces=AIXM_NAMESPACES)
                if apron_link is not None:
                    feature.apron = apron_link.attrib[_ns("xlink", "href")].replace("urn:uuid:", "")

            if feature_type == "TaxiwayMarking":
                twy_link = elem.find(".//aixm:markedTaxiway", namespaces=AIXM_NAMESPACES)
                if twy_link is not None:
                    feature.marked_taxiway = twy_link.attrib[_ns("xlink", "href")].replace(
                        "urn:uuid:",
                        "",
                    )

            if feature_type == "TaxiwayElement":
                twy_link = elem.find(".//aixm:associatedTaxiway", namespaces=AIXM_NAMESPACES)
                if twy_link is not None:
                    feature.taxiway = twy_link.attrib[_ns("xlink", "href")].replace("urn:uuid:", "")

            if feature_type == "GuidanceLineMarking":
                twy_link = elem.find(".//aixm:markedGuidanceLine", namespaces=AIXM_NAMESPACES)
                if twy_link is not None:
                    feature.marked_guidance_line = twy_link.attrib[_ns("xlink", "href")].replace(
                        "urn:uuid:",
                        "",
                    )

            for poslist_element in elem.findall(".//gml:posList", namespaces=AIXM_NAMESPACES):
                poslist = parse_pos_list(poslist_element.text)

                if is_poly and len(poslist) > 2:
                    feature.geometries.append(LinearRing(poslist))
                else:
                    feature.geometries.append(LineString(poslist))

            if feature_type not in result:
                result[feature_type] = {feature_id: feature}
            else:
                result[feature_type][feature_id] = feature

            elem.clear()

    resolve_links(result)
    return result
