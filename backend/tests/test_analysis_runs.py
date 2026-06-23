def test_create_mock_analysis_run_from_scenario(client, repository):
    response = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={
            "scenario": "security_fail",
            "pr_number": 42,
            "head_sha": "abc123",
        },
    )

    assert response.status_code == 201
    run = response.json()
    assert run["id"]
    assert run["repository_id"] == repository["id"]
    assert run["pr_number"] == 42
    assert run["head_sha"] == "abc123"
    assert run["status"] == "completed"
    assert run["decision"] == "fail"
    assert run["score"] == 62
    assert run["ai_review_json"] == {}
    assert run["trigger_source"] == "mock"
    assert run["error_message"] is None
    assert run["pull_request_snapshot_json"] == {}
    assert run["changed_files_snapshot_json"] == []
    assert run["diff_truncated"] is False
    assert run["security_result_json"]["status"] == "fail"
    assert "AI Quality Gate" in run["final_report_markdown"]
    assert len(run["findings"]) == 1
    assert run["findings"][0]["category"] == "security"
    assert run["findings"][0]["severity"] == "high"
    assert run["findings"][0]["blocking"] is True


def test_list_analysis_runs_for_repository(client, repository):
    created = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 7, "head_sha": "def456"},
    ).json()

    response = client.get(f"/api/repositories/{repository['id']}/analysis-runs")

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == created["id"]
    assert runs[0]["decision"] == "pass"
    assert runs[0]["trigger_source"] == "mock"
    assert "findings" not in runs[0]


def test_get_analysis_run_detail(client, repository):
    created = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "coverage_fail", "pr_number": 8, "head_sha": "abc789"},
    ).json()

    response = client.get(f"/api/analysis-runs/{created['id']}")

    assert response.status_code == 200
    run = response.json()
    assert run["id"] == created["id"]
    assert run["decision"] == "fail"
    assert run["ai_review_json"] == {}
    assert run["coverage_result_json"]["status"] == "fail"
    assert run["findings"][0]["category"] == "coverage"
