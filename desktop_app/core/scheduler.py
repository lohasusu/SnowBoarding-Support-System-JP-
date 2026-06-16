"""Wrap Windows Task Scheduler (schtasks.exe) for headless scheduled runs.

Each scheduled task runs:
    {executable_path} --headless --task {ski|flight}
The exe reads its config from %APPDATA%/SnowTripDesktop/config.json so the
GUI-set params stay in sync.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from desktop_app.core.paths import is_frozen, executable_path


@dataclass
class TaskInfo:
    name: str
    next_run: str
    status: str
    schedule: str


def _build_run_command(task_type: str) -> str:
    """Compose the schtasks /TR string.

    Frozen: "C:\\path\\snowtrip.exe" --headless --task ski
    Source: "python.exe" "D:\\path\\desktop_app\\main.py" --headless --task ski
    """
    if is_frozen():
        return f'"{executable_path()}" --headless --task {task_type}'
    # Source mode — used during development testing
    py = sys.executable
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{py}" "{main_py}" --headless --task {task_type}'


def create_task(task_name: str, task_type: str, frequency: str, time_hhmm: str,
                days: str = "MON,TUE,WED,THU,FRI,SAT,SUN") -> tuple[bool, str]:
    """Create or replace a Windows scheduled task.

    Args:
        task_name : display name (will be prefixed with "SnowTrip\\")
        task_type : "ski" or "flight"
        frequency : "DAILY" | "WEEKLY" | "ONCE"
        time_hhmm : "HH:MM" 24h
        days      : comma-separated MON,TUE,... (only for WEEKLY)
    Returns: (ok, message)
    """
    if task_type not in ("ski", "flight"):
        return False, f"task_type 必須是 ski 或 flight，收到 {task_type!r}"
    if frequency not in ("DAILY", "WEEKLY", "ONCE"):
        return False, f"frequency 必須是 DAILY/WEEKLY/ONCE，收到 {frequency!r}"
    if not (len(time_hhmm) == 5 and time_hhmm[2] == ":" and
            time_hhmm[:2].isdigit() and time_hhmm[3:].isdigit()):
        return False, f"time 必須是 HH:MM 格式，收到 {time_hhmm!r}"

    full_name = f"SnowTrip\\{task_name}"
    cmd = [
        "schtasks", "/Create",
        "/TN", full_name,
        "/TR", _build_run_command(task_type),
        "/SC", frequency,
        "/ST", time_hhmm,
        "/F",  # force overwrite if exists
    ]
    if frequency == "WEEKLY":
        cmd.extend(["/D", days])

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="cp950", errors="replace")
    except FileNotFoundError:
        return False, "schtasks.exe 不存在 — 此功能僅限 Windows"
    if r.returncode != 0:
        return False, f"schtasks 失敗 (exit={r.returncode}): {r.stderr or r.stdout}"
    return True, f"已建立排程任務: {full_name}\n下次執行: {time_hhmm} ({frequency})"


def delete_task(task_name: str) -> tuple[bool, str]:
    full_name = f"SnowTrip\\{task_name}"
    try:
        r = subprocess.run(
            ["schtasks", "/Delete", "/TN", full_name, "/F"],
            capture_output=True, text=True, encoding="cp950", errors="replace",
        )
    except FileNotFoundError:
        return False, "schtasks.exe 不存在"
    if r.returncode != 0:
        return False, f"刪除失敗: {r.stderr or r.stdout}"
    return True, f"已刪除排程: {full_name}"


def list_tasks() -> list[TaskInfo]:
    """List existing SnowTrip tasks via schtasks /Query."""
    try:
        r = subprocess.run(
            ["schtasks", "/Query", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, encoding="cp950", errors="replace",
        )
    except FileNotFoundError:
        return []
    out: list[TaskInfo] = []
    for line in r.stdout.splitlines():
        # CSV without header: "TaskName","Next Run Time","Status"
        parts = [c.strip('"') for c in line.split(",")]
        if len(parts) >= 3 and "SnowTrip" in parts[0]:
            out.append(TaskInfo(
                name=parts[0].split("\\")[-1],
                next_run=parts[1] if len(parts) > 1 else "",
                status=parts[2] if len(parts) > 2 else "",
                schedule=parts[0],
            ))
    return out
