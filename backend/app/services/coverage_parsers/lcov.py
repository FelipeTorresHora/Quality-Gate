from pathlib import Path

from app.services.coverage_parsers.types import (
    CoverageFile,
    CoverageReport,
    calculate_total,
)


def parse_lcov(path: str | Path) -> CoverageReport:
    files: dict[str, CoverageFile] = {}
    current_file: str | None = None
    current_total = 0
    current_covered = 0
    current_uncovered: set[int] = set()

    def flush() -> None:
        nonlocal current_file, current_total, current_covered, current_uncovered
        if current_file is None:
            return
        files[current_file] = CoverageFile(
            covered=current_covered,
            total=current_total,
            uncovered_lines=sorted(current_uncovered),
        )
        current_file = None
        current_total = 0
        current_covered = 0
        current_uncovered = set()

    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("SF:"):
            flush()
            current_file = line[3:]
        elif line.startswith("DA:"):
            current_total += 1
            line_number, hits = line[3:].split(",", 1)
            hit_count = int(hits.split(",", 1)[0])
            number = int(line_number)
            if hit_count > 0:
                current_covered += 1
                current_uncovered.discard(number)
            else:
                current_uncovered.add(number)
        elif line.startswith("LF:"):
            current_total = int(line[3:])
        elif line.startswith("LH:"):
            current_covered = int(line[3:])
        elif line == "end_of_record":
            flush()
    flush()

    return CoverageReport(total_coverage=calculate_total(files), files=files)
