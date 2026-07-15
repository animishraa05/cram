"""Configuration loader for cram."""

import os
import threading
from pathlib import Path

_config_cache: dict[str, str] | None = None
_config_lock = threading.Lock()


def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "cram" / "config"


def load_config() -> dict[str, str]:
    global _config_cache
    with _config_lock:
        if _config_cache is not None:
            return dict(_config_cache)

    cfg: dict[str, str] = {}
    path = config_path()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                val = os.path.expandvars(os.path.expanduser(val))
                cfg[key.strip()] = val

    with _config_lock:
        _config_cache = cfg
    return dict(cfg)


def invalidate_cache() -> None:
    global _config_cache
    with _config_lock:
        _config_cache = None


def save_config(cfg: dict[str, str]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, val in sorted(cfg.items()):
        lines.append(f'{key}="{val}"')
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    invalidate_cache()


def get(key: str, default: str = "") -> str:
    return load_config().get(key, default)


def cards_file() -> Path:
    old_path = Path.home() / "cram" / "data" / "cards.json"
    new_path = (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        / "cram"
        / "cards.json"
    )
    explicit = get("CARDS_FILE", "")
    if explicit:
        return Path(explicit)
    if new_path.exists() or not old_path.exists():
        return new_path
    return old_path


def vault() -> Path:
    return Path(get("OBSIDIAN_VAULT", str(Path.home() / "blog" / "content")))


def problem_folder() -> str:
    return get("PROBLEM_FOLDER", "Private/Daily/Problems")


def desired_retention() -> float:
    try:
        val = float(get("DESIRED_RETENTION", "0.9"))
    except ValueError:
        val = 0.9
    return max(0.01, min(1.0, val))


def leetcode_username() -> str:
    return get("LEETCODE_USERNAME", "")


def theme_name() -> str:
    return get("THEME", "tokyonight")


def notify_enabled() -> bool:
    return get("NOTIFY_ENABLED", "true").lower() in ("true", "1", "yes")


def notify_interval() -> int:
    try:
        return max(60, int(get("NOTIFY_INTERVAL", "3600")))
    except ValueError:
        return 3600


def is_configured() -> bool:
    cfg_path = config_path()
    return cfg_path.exists() and vault().exists()


def editor_mode() -> str:
    mode = get("EDITOR_MODE", "external").lower().strip()
    return mode if mode in ("external", "embedded") else "external"
