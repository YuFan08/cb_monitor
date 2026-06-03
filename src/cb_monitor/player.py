"""Windows mpv integration."""

from __future__ import annotations

import subprocess

from cb_monitor.errors import PlayerLaunchError
from cb_monitor.models import StreamVariant


def launch_mpv(mpv_path: str, variant: StreamVariant) -> None:
    """Launch mpv with the selected stream URL."""
    command = [mpv_path, variant.url]
    try:
        subprocess.Popen(command, close_fds=True)
    except FileNotFoundError as exc:
        msg = f"未找到 mpv: {mpv_path}。请检查系统变量或 CB_MPV_PATH。"
        raise PlayerLaunchError(msg) from exc
    except OSError as exc:
        msg = f"mpv 启动失败: {exc.strerror or exc}"
        raise PlayerLaunchError(msg) from exc
