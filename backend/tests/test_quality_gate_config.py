def test_update_quality_gate_config(client, repository):
    response = client.put(
        f"/api/repositories/{repository['id']}/quality-gate-config",
        json={
            "min_total_coverage": 85,
            "max_coverage_drop": 1.5,
            "min_changed_files_coverage": 80,
            "security_fail_on": ["critical"],
            "max_function_lines": 60,
            "max_complexity": 8,
            "fail_on_new_todo": False,
            "comment_on_github": True,
            "publish_github_status": False,
        },
    )

    assert response.status_code == 200
    config = response.json()
    assert config["min_total_coverage"] == 85
    assert config["max_coverage_drop"] == 1.5
    assert config["min_changed_files_coverage"] == 80
    assert config["security_fail_on"] == ["critical"]
    assert config["max_function_lines"] == 60
    assert config["max_complexity"] == 8
    assert config["fail_on_new_todo"] is False
    assert config["comment_on_github"] is True
    assert config["publish_github_status"] is False
