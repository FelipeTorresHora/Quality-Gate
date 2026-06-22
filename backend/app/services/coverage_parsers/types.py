from dataclasses import dataclass


@dataclass
class CoverageFile:
    covered: int
    total: int

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0
        return round((self.covered / self.total) * 100, 2)


@dataclass
class CoverageReport:
    total_coverage: float
    files: dict[str, CoverageFile]


def calculate_total(files: dict[str, CoverageFile]) -> float:
    total = sum(file.total for file in files.values())
    if total == 0:
        return 0
    covered = sum(file.covered for file in files.values())
    return round((covered / total) * 100, 2)
