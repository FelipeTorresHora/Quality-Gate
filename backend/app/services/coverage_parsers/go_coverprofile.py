from pathlib import Path

from app.services.coverage_parsers.types import (
    CoverageFile,
    CoverageReport,
    calculate_total,
)


def _span_lines(location: str) -> tuple[str, list[int]]:
    filename, _, span = location.rpartition(":")
    if not filename or "," not in span:
        return location.split(":", 1)[0], []
    start, end = span.split(",", 1)
    start_line = int(start.split(".", 1)[0])
    end_line = int(end.split(".", 1)[0])
    if end_line < start_line:
        start_line, end_line = end_line, start_line
    return filename, list(range(start_line, end_line + 1))


def parse_go_coverprofile(path: str | Path) -> CoverageReport:
    totals: dict[str, tuple[int, int]] = {}
    uncovered: dict[str, set[int]] = {}
    covered_lines: dict[str, set[int]] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("mode:"):
            continue
        location, statements, count = line.rsplit(" ", 2)
        filename, span_lines = _span_lines(location)
        total = int(statements)
        hit_count = int(count)
        covered = total if hit_count > 0 else 0
        current_covered, current_total = totals.get(filename, (0, 0))
        totals[filename] = (current_covered + covered, current_total + total)
        uncovered.setdefault(filename, set())
        covered_lines.setdefault(filename, set())
        if hit_count > 0:
            covered_lines[filename].update(span_lines)
            uncovered[filename].difference_update(span_lines)
        else:
            for number in span_lines:
                if number not in covered_lines[filename]:
                    uncovered[filename].add(number)

    files = {
        filename: CoverageFile(
            covered=covered,
            total=total,
            uncovered_lines=sorted(uncovered.get(filename, set())),
        )
        for filename, (covered, total) in totals.items()
    }
    return CoverageReport(total_coverage=calculate_total(files), files=files)
