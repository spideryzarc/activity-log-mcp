from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Activity Log")

DEFAULT_LOG_DIR = "activity-log"
LOG_FILENAME = "activity_log.json"
ARCHIVE_DIRNAME = "archive"
VALID_STATUS = {"in_progress", "success", "failure"}


def _resolve_base_dir(cwd: str | None) -> Path:
    if cwd:
        return Path(cwd).expanduser().resolve()
    return Path(os.getcwd()).resolve()


def _build_paths(cwd: str | None) -> tuple[Path, Path, Path]:
    base_dir = _resolve_base_dir(cwd)
    log_dir = base_dir / DEFAULT_LOG_DIR
    log_path = log_dir / LOG_FILENAME
    archive_dir = log_dir / ARCHIVE_DIRNAME
    return log_dir, log_path, archive_dir


def _backup_corrupt_file(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".bak")
    try:
        path.rename(backup_path)
    except OSError:
        pass


def _load_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return []

    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        _backup_corrupt_file(path)
        return []

    if isinstance(data, list):
        return data

    _backup_corrupt_file(path)
    return []


def _save_entries(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=4, ensure_ascii=False), encoding="utf-8")


def _validate_status(status: str) -> str | None:
    if status in VALID_STATUS:
        return None
    valid = ", ".join(sorted(VALID_STATUS))
    return f"Error: status must be one of [{valid}]."


def _month_key(date_value: str) -> str:
    if len(date_value) >= 7:
        return date_value[:7]
    return "unknown"


@mcp.resource("context://activity-log/manifesto")
def activity_log_manifesto() -> str:
    """Provides MCP usage guidance for activity logging workflows."""
    return (
        "Activity Log MCP keeps structured task history on local files.\\n"
        "Use log_activity for new entries, update_last_activity for refinements, "
        "dump_activity_log for introspection, and rotate_activity_log for maintenance."
    )


@mcp.tool()
def log_activity(
    objective: str,
    status: str,
    result: str | None = None,
    notes: str = "",
    changed_files: list[str] | None = None,
    cwd: str | None = None,
) -> str:
    """Appends a new activity entry to activity-log/activity_log.json."""
    if not objective:
        return "Error: objective is required."

    status_error = _validate_status(status)
    if status_error:
        return status_error

    _, log_path, _ = _build_paths(cwd)
    entries = _load_entries(log_path)

    entry = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "objective": objective,
        "result": result or "Pending",
        "changed_files": changed_files or [],
        "status": status,
        "notes": notes,
    }
    entries.append(entry)
    _save_entries(log_path, entries)

    return "Appended new entry."


@mcp.tool()
def update_last_activity(
    objective: str | None = None,
    status: str | None = None,
    result: str | None = None,
    notes: str = "",
    changed_files: list[str] | None = None,
    cwd: str | None = None,
) -> str:
    """Updates fields in the last activity entry using partial update semantics."""
    if status is not None:
        status_error = _validate_status(status)
        if status_error:
            return status_error

    _, log_path, _ = _build_paths(cwd)
    entries = _load_entries(log_path)

    if not entries:
        return "No entries to update."

    last_entry = entries[-1]
    changed = False

    if objective:
        last_entry["objective"] = objective
        changed = True
    if status:
        last_entry["status"] = status
        changed = True
    if result:
        last_entry["result"] = result
        changed = True
    if notes:
        last_entry["notes"] = notes
        changed = True
    if changed_files:
        last_entry["changed_files"] = changed_files
        changed = True

    if not changed:
        return "Success: No changes made to last entry."

    _save_entries(log_path, entries)
    return f"Updated last entry at index {len(entries) - 1}."


@mcp.tool()
def dump_activity_log(since: str | None = None, cwd: str | None = None) -> str:
    """Returns the activity log as a JSON string, optionally filtered by date >= since."""
    _, log_path, _ = _build_paths(cwd)
    entries = _load_entries(log_path)

    if not entries:
        return "[]"

    result_entries = entries
    if since:
        try:
            since_date = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            return f"Invalid date format for --since: {since}. Use YYYY-MM-DD."

        filtered_entries: list[dict] = []
        for entry in entries:
            date_value = entry.get("date")
            if not isinstance(date_value, str):
                continue
            try:
                entry_date = datetime.fromisoformat(date_value)
            except ValueError:
                continue
            if entry_date >= since_date:
                filtered_entries.append(entry)
        result_entries = filtered_entries

    return json.dumps(result_entries, indent=4, ensure_ascii=False)


@mcp.tool()
def rotate_activity_log(limit: int = 50, dry_run: bool = False, cwd: str | None = None) -> str:
    """Rotates oldest entries from the main log into monthly archive files."""
    if limit < 1:
        return "Error: limit must be >= 1."

    _, log_path, archive_dir = _build_paths(cwd)
    if not log_path.exists():
        return f"No activity log found at {log_path}"

    entries = _load_entries(log_path)
    total = len(entries)
    if total <= limit:
        return f"Log has {total} entries. Limit is {limit}. No rotation needed."

    overflow_count = total - limit
    to_archive = entries[:overflow_count]
    to_keep = entries[overflow_count:]

    grouped_archives: dict[str, list[dict]] = defaultdict(list)
    for entry in to_archive:
        month = _month_key(str(entry.get("date", "")))
        grouped_archives[month].append(entry)

    if dry_run:
        lines = [f"Rotating {overflow_count} entries. Keeping last {limit}.", "", "[DRY RUN] Would append to archives:"]
        for month, month_entries in grouped_archives.items():
            lines.append(f"  - activity_log_{month}.json: {len(month_entries)} entries")
        lines.append("")
        lines.append(f"[DRY RUN] Would update {DEFAULT_LOG_DIR}/{LOG_FILENAME} to contain {len(to_keep)} entries.")
        return "\\n".join(lines)

    for month, month_entries in grouped_archives.items():
        archive_path = archive_dir / f"activity_log_{month}.json"
        archive_entries = _load_entries(archive_path)
        archive_entries.extend(month_entries)
        _save_entries(archive_path, archive_entries)

    _save_entries(log_path, to_keep)
    return f"Rotated {overflow_count} entries. Main log now has {len(to_keep)} entries."
