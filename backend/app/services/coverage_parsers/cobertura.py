from pathlib import Path
from xml.etree import ElementTree

from app.services.coverage_parsers.types import (
    CoverageFile,
    CoverageReport,
    calculate_total,
)


def parse_cobertura_xml(path: str | Path) -> CoverageReport:
    root = ElementTree.parse(path).getroot()
    covered_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    uncovered: dict[str, set[int]] = {}
    covered_lines: dict[str, set[int]] = {}

    for class_node in root.findall(".//class"):
        filename = class_node.attrib.get("filename")
        if not filename:
            continue
        covered_counts.setdefault(filename, 0)
        total_counts.setdefault(filename, 0)
        uncovered.setdefault(filename, set())
        covered_lines.setdefault(filename, set())
        for line in class_node.findall(".//line"):
            total_counts[filename] += 1
            hits = int(line.attrib.get("hits", "0"))
            number = int(line.attrib.get("number", "0"))
            if hits > 0:
                covered_counts[filename] += 1
                if number > 0:
                    covered_lines[filename].add(number)
                    uncovered[filename].discard(number)
            elif number > 0 and number not in covered_lines[filename]:
                uncovered[filename].add(number)

    files = {
        filename: CoverageFile(
            covered=covered_counts[filename],
            total=total_counts[filename],
            uncovered_lines=sorted(uncovered[filename]),
        )
        for filename in total_counts
    }
    return CoverageReport(total_coverage=calculate_total(files), files=files)
