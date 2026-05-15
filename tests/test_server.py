import json
from pathlib import Path

from activity_log_mcp import server


def _read_log(cwd: Path) -> list[dict]:
    path = cwd / "activity-log" / "activity_log.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_log_activity_appends_and_creates_directory(tmp_path: Path):
    result = server.log_activity(
        objective="Refactor endpoint",
        status="success",
        result="Refactored endpoint logic",
        changed_files=[str(tmp_path / "app.py")],
        cwd=str(tmp_path),
    )

    assert result == "Appended new entry."
    entries = _read_log(tmp_path)
    assert len(entries) == 1
    assert entries[0]["objective"] == "Refactor endpoint"
    assert entries[0]["status"] == "success"


def test_log_activity_defaults_result_to_pending(tmp_path: Path):
    server.log_activity(objective="Run lint", status="in_progress", cwd=str(tmp_path))
    entries = _read_log(tmp_path)
    assert entries[0]["result"] == "Pending"


def test_log_activity_validates_status(tmp_path: Path):
    result = server.log_activity(objective="Task", status="done", cwd=str(tmp_path))
    assert "Error: status must be one of" in result


def test_update_last_activity_partial_update(tmp_path: Path):
    server.log_activity(objective="Initial objective", status="in_progress", cwd=str(tmp_path))
    result = server.update_last_activity(result="Finished implementation", status="success", cwd=str(tmp_path))

    assert result == "Updated last entry at index 0."
    entries = _read_log(tmp_path)
    assert entries[0]["objective"] == "Initial objective"
    assert entries[0]["result"] == "Finished implementation"
    assert entries[0]["status"] == "success"


def test_update_last_activity_handles_empty_log(tmp_path: Path):
    result = server.update_last_activity(status="success", cwd=str(tmp_path))
    assert result == "No entries to update."


def test_dump_activity_log_with_since_filter_and_malformed_date(tmp_path: Path):
    log_dir = tmp_path / "activity-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "activity_log.json"
    log_path.write_text(
        json.dumps(
            [
                {"date": "2026-05-10T09:00:00", "objective": "A", "result": "A", "changed_files": [], "status": "success", "notes": ""},
                {"date": "bad-date", "objective": "B", "result": "B", "changed_files": [], "status": "success", "notes": ""},
                {"date": "2026-05-16T10:00:00", "objective": "C", "result": "C", "changed_files": [], "status": "success", "notes": ""},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    dumped = server.dump_activity_log(since="2026-05-15", cwd=str(tmp_path))
    data = json.loads(dumped)
    assert len(data) == 1
    assert data[0]["objective"] == "C"


def test_dump_activity_log_validates_since_format(tmp_path: Path):
    result = server.dump_activity_log(since="15-05-2026", cwd=str(tmp_path))
    assert result == "[]"


def test_dump_activity_log_validates_since_format_with_existing_data(tmp_path: Path):
    server.log_activity(objective="Task", status="success", cwd=str(tmp_path))
    result = server.dump_activity_log(since="15-05-2026", cwd=str(tmp_path))
    assert "Invalid date format for --since" in result


def test_corrupt_json_is_backed_up_on_write(tmp_path: Path):
    log_dir = tmp_path / "activity-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "activity_log.json"
    log_path.write_text("{invalid json", encoding="utf-8")

    server.log_activity(objective="Recover", status="success", cwd=str(tmp_path))

    backup_path = log_dir / "activity_log.json.bak"
    assert backup_path.exists()
    entries = _read_log(tmp_path)
    assert len(entries) == 1
    assert entries[0]["objective"] == "Recover"


def test_rotate_activity_log_dry_run_does_not_mutate(tmp_path: Path):
    for idx in range(3):
        server.log_activity(objective=f"Task {idx}", status="success", cwd=str(tmp_path))

    before = _read_log(tmp_path)
    result = server.rotate_activity_log(limit=2, dry_run=True, cwd=str(tmp_path))
    after = _read_log(tmp_path)

    assert "[DRY RUN]" in result
    assert before == after


def test_rotate_activity_log_archives_and_keeps_limit(tmp_path: Path):
    log_dir = tmp_path / "activity-log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "activity_log.json"
    log_path.write_text(
        json.dumps(
            [
                {"date": "2026-04-01T00:00:00", "objective": "A1", "result": "A1", "changed_files": [], "status": "success", "notes": ""},
                {"date": "2026-04-02T00:00:00", "objective": "A2", "result": "A2", "changed_files": [], "status": "success", "notes": ""},
                {"date": "2026-05-01T00:00:00", "objective": "B1", "result": "B1", "changed_files": [], "status": "success", "notes": ""},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = server.rotate_activity_log(limit=1, cwd=str(tmp_path))
    assert "Rotated 2 entries" in result

    main_log = _read_log(tmp_path)
    assert len(main_log) == 1
    assert main_log[0]["objective"] == "B1"

    archive = json.loads((tmp_path / "activity-log" / "archive" / "activity_log_2026-04.json").read_text(encoding="utf-8"))
    assert len(archive) == 2


def test_rotate_activity_log_without_file(tmp_path: Path):
    result = server.rotate_activity_log(cwd=str(tmp_path))
    assert "No activity log found" in result
