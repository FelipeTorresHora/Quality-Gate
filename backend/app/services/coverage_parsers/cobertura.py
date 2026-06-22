from pathlib import Path
from xml.etree import ElementTree

from app.services.coverage_parsers.types import (
    CoverageFile,
    CoverageReport,
    calculate_total,
)


def parse_cobertura_xml(path: str | Path) -> CoverageReport:
    root = ElementTree.parse(path).getroot()
    files: dict[str, CoverageFile] = {}

    for class_node in root.findall(".//class"):
        filename = class_node.attrib.get("filename")
        if not filename:
            continue
        total = 0
        covered = 0
        for line in class_node.findall(".//line"):
            total += 1
            if int(line.attrib.get("hits", "0")) > 0:
                covered += 1
        current = files.get(filename)
        if current is None:
            files[filename] = CoverageFile(covered=covered, total=total)
        else:
            files[filename] = CoverageFile(
                covered=current.covered + covered,
                total=current.total + total,
            )

    return CoverageReport(total_coverage=calculate_total(files), files=files)
