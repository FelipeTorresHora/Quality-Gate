from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

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


def test_unmatched_changed_file_is_not_counted_as_zero():
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

    assert result.changed_files_coverage == 80.0
    assert result.changed_source_files == ["src/covered.py", "src/missing.py"]
    assert result.unmatched == ["src/missing.py"]


def test_changed_files_coverage_is_line_weighted():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageFile, CoverageReport

    report = CoverageReport(
        total_coverage=0,
        files={
            "src/a.py": CoverageFile(covered=9, total=10),
            "src/b.py": CoverageFile(covered=0, total=90),
        },
    )

    result = calculate_changed_files_coverage(
        report,
        [{"filename": "src/a.py"}, {"filename": "src/b.py"}],
        "python",
    )

    assert result.changed_files_coverage == 9.0


def test_all_changed_files_unmatched_returns_none():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageReport

    result = calculate_changed_files_coverage(
        CoverageReport(total_coverage=0, files={}),
        [{"filename": "src/only.py"}],
        "python",
    )

    assert result.changed_files_coverage is None
    assert result.unmatched == ["src/only.py"]


def test_normalize_path_preserves_leading_dot_directories():
    from app.services.gates.coverage_gate import _normalize_path

    assert _normalize_path(".github/workflows/ci.yml") == ".github/workflows/ci.yml"
    assert _normalize_path("./src/app.py") == "src/app.py"
    assert _normalize_path("src\\app.py") == "src/app.py"


def test_changed_file_matches_report_through_working_directory():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageFile, CoverageReport

    report = CoverageReport(
        total_coverage=100,
        files={"main.py": CoverageFile(covered=2, total=2)},
    )

    result = calculate_changed_files_coverage(
        report,
        [{"filename": "agent/main.py"}],
        "python",
        working_directory="agent",
    )

    assert result.changed_files_coverage == 100.0
    assert result.unmatched == []


def test_changed_file_matches_report_by_suffix_fallback():
    from app.services.gates.coverage_gate import calculate_changed_files_coverage
    from app.services.coverage_parsers.types import CoverageFile, CoverageReport

    report = CoverageReport(
        total_coverage=50,
        files={"repo/src/app.py": CoverageFile(covered=1, total=2)},
    )

    result = calculate_changed_files_coverage(
        report,
        [{"filename": "src/app.py"}],
        "python",
    )

    assert result.changed_files_coverage == 50.0
    assert result.unmatched == []


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


def test_base_coverage_skipped_when_no_drop_policy(monkeypatch, tmp_path):
    from app.services import analysis_evidence_workspace
    from app.services.gates import coverage_gate

    checkouts = []

    class FakeRunnerWorkspace:
        def __init__(self, analysis_run_id, repository_url):
            self.root = tmp_path / str(analysis_run_id)
            self.repo_path = self.root / "repo"
            self.command_metadata = []

        def __enter__(self):
            self.root.mkdir(parents=True, exist_ok=True)
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def checkout(self, revision):
            checkouts.append(revision)
            self.repo_path.mkdir(parents=True, exist_ok=True)

        def run(self, command, working_directory="."):
            report = self.repo_path / working_directory / "coverage.xml"
            report.write_text(
                """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="main.py">
          <lines>
            <line number="1" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
                encoding="utf-8",
            )
            return SimpleNamespace(timed_out=False, exit_code=0)

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        FakeRunnerWorkspace,
    )

    analysis_run = SimpleNamespace(
        id=uuid4(),
        head_sha="head-sha",
        pull_request_snapshot_json={"base_sha": "base-sha"},
        changed_files_snapshot_json=[{"filename": "main.py"}],
    )
    with analysis_evidence_workspace.GateExecutionEvidenceWorkspace(
        analysis_run=analysis_run,
        repository=SimpleNamespace(owner="o", name="r"),
        repository_token="t",
    ) as evidence_workspace:
        result = coverage_gate.run_coverage_gate(
            analysis_run=analysis_run,
            quality_config=SimpleNamespace(
                min_total_coverage=0,
                max_coverage_drop=None,
                min_changed_files_coverage=0,
            ),
            coverage_config=SimpleNamespace(
                language=SimpleNamespace(value="python"),
                install_command="",
                test_command="pytest",
                report_path="coverage.xml",
                report_format=SimpleNamespace(value="cobertura_xml"),
                working_directory=".",
            ),
            evidence_workspace=evidence_workspace,
        )

    assert checkouts == ["head-sha"]
    assert result.snapshot["status"] == "pass"


def test_coverage_gate_runs_commands_in_configured_working_directory(
    monkeypatch, tmp_path
):
    from app.services import analysis_evidence_workspace
    from app.services.gates import coverage_gate

    commands = []

    class FakeRunnerWorkspace:
        def __init__(self, analysis_run_id, repository_url):
            self.root = tmp_path / str(analysis_run_id)
            self.repo_path = self.root / "repo"
            self.command_metadata = []

        def __enter__(self):
            self.root.mkdir(parents=True, exist_ok=True)
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def checkout(self, revision):
            commands.append(("checkout", revision, "."))
            (self.repo_path / "docker-log-watcher-agent").mkdir(parents=True)

        def run(self, command, working_directory="."):
            commands.append(("run", command, working_directory))
            report = self.repo_path / working_directory / "coverage.xml"
            report.write_text(
                """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package>
      <classes>
        <class filename="main.py">
          <lines>
            <line number="1" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
                encoding="utf-8",
            )
            return SimpleNamespace(timed_out=False, exit_code=0)

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        FakeRunnerWorkspace,
    )

    analysis_run = SimpleNamespace(
        id=uuid4(),
        head_sha="head-sha",
        pull_request_snapshot_json={"base_sha": "base-sha"},
        changed_files_snapshot_json=[
            {"filename": "docker-log-watcher-agent/main.py"}
        ],
    )
    with analysis_evidence_workspace.GateExecutionEvidenceWorkspace(
        analysis_run=analysis_run,
        repository=SimpleNamespace(owner="FelipeTorresHora", name="nested-repo"),
        repository_token="token",
    ) as evidence_workspace:
        result = coverage_gate.run_coverage_gate(
            analysis_run=analysis_run,
            quality_config=SimpleNamespace(
                min_total_coverage=0,
                max_coverage_drop=100,
                min_changed_files_coverage=0,
            ),
            coverage_config=SimpleNamespace(
                language=SimpleNamespace(value="python"),
                install_command="pip install -r requirements.txt",
                test_command="pytest --cov=. --cov-report=xml:coverage.xml",
                report_path="coverage.xml",
                report_format=SimpleNamespace(value="cobertura_xml"),
                working_directory="docker-log-watcher-agent",
            ),
            evidence_workspace=evidence_workspace,
        )

    assert result.snapshot["status"] == "pass"
    assert (
        "run",
        "pip install -r requirements.txt",
        "docker-log-watcher-agent",
    ) in commands
    assert (
        "run",
        "pytest --cov=. --cov-report=xml:coverage.xml",
        "docker-log-watcher-agent",
    ) in commands
