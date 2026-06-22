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

    def flush() -> None:
        nonlocal current_file, current_total, current_covered
        if current_file is None:
            return
        files[current_file] = CoverageFile(
            covered=current_covered,
            total=current_total,
        )
        current_file = None
        current_total = 0
        current_covered = 0

    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("SF:"):
            flush()
            current_file = line[3:]
        elif line.startswith("DA:"):
            current_total += 1
            _, hits = line[3:].split(",", 1)
            if int(hits.split(",", 1)[0]) > 0:
                current_covered += 1
        elif line.startswith("LF:"):
            current_total = int(line[3:])
        elif line.startswith("LH:"):
            current_covered = int(line[3:])
        elif line == "end_of_record":
            flush()
    flush()

    return CoverageReport(total_coverage=calculate_total(files), files=files)
