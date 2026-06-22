from pathlib import Path

from app.services.coverage_parsers.types import (
    CoverageFile,
    CoverageReport,
    calculate_total,
)


def parse_go_coverprofile(path: str | Path) -> CoverageReport:
    totals: dict[str, tuple[int, int]] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("mode:"):
            continue
        location, statements, count = line.rsplit(" ", 2)
        filename = location.split(":", 1)[0]
        total = int(statements)
        covered = total if int(count) > 0 else 0
        current_covered, current_total = totals.get(filename, (0, 0))
        totals[filename] = (current_covered + covered, current_total + total)

    files = {
        filename: CoverageFile(covered=covered, total=total)
        for filename, (covered, total) in totals.items()
    }
    return CoverageReport(total_coverage=calculate_total(files), files=files)
