from pathlib import Path

from app.models.enums import FindingCategory


def test_parse_cobertura_xml_coverage(tmp_path):
    from app.services.coverage_parsers.cobertura import parse_cobertura_xml

    report = tmp_path / "coverage.xml"
    report.write_text(
        """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="src/app.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    result = parse_cobertura_xml(report)

    assert result.total_coverage == 50
    assert result.files["src/app.py"].covered == 1
    assert result.files["src/app.py"].total == 2


def test_parse_lcov_coverage(tmp_path):
    from app.services.coverage_parsers.lcov import parse_lcov

    report = tmp_path / "lcov.info"
    report.write_text(
        "\n".join(
            [
                "TN:",
                "SF:src/app.ts",
                "DA:1,1",
                "DA:2,0",
                "LF:2",
                "LH:1",
                "end_of_record",
            ]
        ),
        encoding="utf-8",
    )

    result = parse_lcov(report)

    assert result.total_coverage == 50
    assert result.files["src/app.ts"].covered == 1
    assert result.files["src/app.ts"].total == 2


def test_parse_go_coverprofile(tmp_path):
    from app.services.coverage_parsers.go_coverprofile import parse_go_coverprofile

    report = tmp_path / "coverage.out"
    report.write_text(
        "\n".join(
            [
                "mode: set",
                "github.com/acme/app/main.go:1.1,2.1 1 1",
                "github.com/acme/app/main.go:3.1,4.1 1 0",
            ]
        ),
        encoding="utf-8",
    )

    result = parse_go_coverprofile(report)

    assert result.total_coverage == 50
    assert result.files["github.com/acme/app/main.go"].covered == 1
    assert result.files["github.com/acme/app/main.go"].total == 2


def test_changed_file_missing_from_report_counts_as_zero():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageFile, CoverageReport

    report = CoverageReport(
        total_coverage=90,
        files={"src/covered.py": CoverageFile(covered=8, total=10)},
    )

    result = calculate_changed_files_coverage(
        report,
        [{"filename": "src/covered.py"}, {"filename": "src/missing.py"}],
        "python",
    )

    assert result.changed_files_coverage == 40
    assert result.changed_source_files == ["src/covered.py", "src/missing.py"]


def test_no_changed_source_files_disables_changed_files_rule():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageReport

    result = calculate_changed_files_coverage(
        CoverageReport(total_coverage=90, files={}),
        [{"filename": "README.md"}],
        "python",
    )

    assert result.changed_files_coverage is None
    assert result.changed_source_files == []


def test_coverage_policy_creates_blocking_findings():
    from app.services.gates.coverage_gate import apply_coverage_policy

    snapshot, findings = apply_coverage_policy(
        language="python",
        report_format="cobertura_xml",
        base_sha="base",
        head_sha="head",
        base_coverage=90,
        pr_coverage=75,
        changed_files_coverage=60,
        changed_source_files=["src/app.py"],
        quality_config={
            "min_total_coverage": 80,
            "max_coverage_drop": 5,
            "min_changed_files_coverage": 75,
        },
        command_metadata=[],
    )

    assert snapshot["status"] == "fail"
    assert len(snapshot["blocking_reasons"]) == 3
    assert [finding.category for finding in findings] == [
        FindingCategory.COVERAGE,
        FindingCategory.COVERAGE,
        FindingCategory.COVERAGE,
    ]
    assert all(finding.blocking for finding in findings)
