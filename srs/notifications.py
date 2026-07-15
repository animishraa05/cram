"""Systemd user timer for hourly due card notifications."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

TIMER_unit = """\
[Unit]
Description=cram hourly due card notifications

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
"""

SERVICE_unit = """\
[Unit]
Description=cram notify due cards

[Service]
Type=oneshot
ExecStart={exec_path} notify
"""


def _systemd_dir() -> Path:
    return Path.home() / ".config" / "systemd" / "user"


def _find_exec() -> str:
    path = shutil.which("cram")
    if path:
        return path
    return "cram"


def setup_notifications() -> str:
    """Create and enable systemd user timer for hourly notifications.

    Returns a status message.
    """
    if not shutil.which("systemctl"):
        return "Error: systemctl not found. Systemd is required for background notifications."

    systemd_dir = _systemd_dir()
    systemd_dir.mkdir(parents=True, exist_ok=True)

    timer_path = systemd_dir / "cram-notify.timer"
    service_path = systemd_dir / "cram-notify.service"

    exec_path = _find_exec()
    service_content = SERVICE_unit.format(exec_path=exec_path)

    timer_path.write_text(TIMER_unit, encoding="utf-8")
    service_path.write_text(service_content, encoding="utf-8")

    run = ["systemctl", "--user"]
    try:
        subprocess.run(run + ["daemon-reload"], check=True, timeout=10)
        subprocess.run(run + ["enable", "cram-notify.timer"], check=True, timeout=10)
        subprocess.run(run + ["start", "cram-notify.timer"], check=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return f"Error enabling timer: {e}"

    return (
        "Hourly notifications enabled.\n"
        f"  Timer: {timer_path}\n"
        f"  Service: {service_path}\n"
        "  Notifications will fire every hour via dunst."
    )


def remove_notifications() -> str:
    """Stop and remove the systemd user timer.

    Returns a status message.
    """
    if not shutil.which("systemctl"):
        return "Error: systemctl not found."

    run = ["systemctl", "--user"]

    try:
        subprocess.run(run + ["stop", "cram-notify.timer"], check=False, timeout=10)
        subprocess.run(run + ["disable", "cram-notify.timer"], check=False, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    systemd_dir = _systemd_dir()
    timer_path = systemd_dir / "cram-notify.timer"
    service_path = systemd_dir / "cram-notify.service"

    removed = []
    for p in (timer_path, service_path):
        if p.exists():
            p.unlink()
            removed.append(str(p))

    try:
        subprocess.run(run + ["daemon-reload"], check=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    if removed:
        return f"Removed: {', '.join(removed)}\nHourly notifications disabled."
    return "No timer files found. Notifications already disabled."
