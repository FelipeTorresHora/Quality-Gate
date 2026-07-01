from app.models.enums import FindingCategory


def test_new_todo_detection_uses_added_diff_lines_only():
    from app.services.gates.technical_debt_gate import detect_new_todos

    findings = detect_new_todos(
        [
            {
                "filename": "src/app.py",
                "patch": "\n".join(
                    [
                        "@@ -1,2 +1,3 @@",
                        " existing code",
                        "-# TODO old removed",
                        "+# TODO new work",
                    ]
                ),
            }
        ],
        language="python",
        fail_on_new_todo=True,
    )

    assert len(findings) == 1
    assert findings[0].category == FindingCategory.TECHNICAL_DEBT
    assert findings[0].file_path == "src/app.py"
    assert findings[0].blocking is True


def test_old_todo_marker_does_not_block():
    from app.services.gates.technical_debt_gate import detect_new_todos

    findings = detect_new_todos(
        [{"filename": "src/app.py", "patch": " # TODO already existed"}],
        language="python",
        fail_on_new_todo=True,
    )

    assert findings == []


def test_missing_diff_evidence_returns_operational_error():
    from app.services.gates.technical_debt_gate import validate_diff_evidence

    result = validate_diff_evidence([], None)

    assert result["status"] == "error"
    assert "Pull Request diff evidence is required" in result["error_message"]


def test_python_function_length_and_complexity_findings(tmp_path):
    from app.services.gates.technical_debt_gate import analyze_python_file

    source = tmp_path / "app.py"
    source.write_text(
        "\n".join(
            [
                "def complicated(value):",
                "    if value:",
                "        if value > 1:",
                "            return 1",
                "    return 0",
            ]
        ),
        encoding="utf-8",
    )

    findings = analyze_python_file(
        source,
        display_path="src/app.py",
        max_function_lines=3,
        max_complexity=2,
    )

    assert {finding.title for finding in findings} == {
        "Function exceeds line limit",
        "Function complexity exceeds limit",
    }


def test_javascript_function_length_finding(tmp_path):
    from app.services.gates.technical_debt_gate import analyze_brace_language_file

    source = tmp_path / "app.ts"
    source.write_text(
        "\n".join(
            [
                "function run() {",
                "  const a = 1;",
                "  const b = 2;",
                "  return a + b;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = analyze_brace_language_file(
        source,
        display_path="src/app.ts",
        max_function_lines=3,
        language="typescript",
    )

    assert len(findings) == 1
    assert findings[0].title == "Function exceeds line limit"


def test_brace_language_long_function_finding_is_non_blocking(tmp_path):
    from app.services.gates.technical_debt_gate import analyze_brace_language_file

    source = tmp_path / "app.ts"
    source.write_text(
        "\n".join(
            [
                "function run() {",
                "  const a = 1;",
                "  const b = 2;",
                "  return a + b;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    findings = analyze_brace_language_file(
        source,
        display_path="src/app.ts",
        max_function_lines=3,
        language="typescript",
    )

    assert findings
    assert all(finding.blocking is False for finding in findings)
