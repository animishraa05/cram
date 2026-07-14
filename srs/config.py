"""Configuration loader for cram."""

import os
from pathlib import Path

_config_cache: dict[str, str] | None = None


def config_path() -> Path:
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "cram"
        / "config"
    )


def load_config() -> dict[str, str]:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    cfg: dict[str, str] = {}
    path = config_path()
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                val = os.path.expandvars(os.path.expanduser(val))
                cfg[key.strip()] = val

    _config_cache = cfg
    return cfg


def invalidate_cache() -> None:
    global _config_cache
    _config_cache = None


def save_config(cfg: dict[str, str]) -> None:
    global _config_cache
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key, val in sorted(cfg.items()):
        lines.append(f'{key}="{val}"')
    path.write_text("\n".join(lines) + "\n")
    _config_cache = None


def get(key: str, default: str = "") -> str:
    return load_config().get(key, default)


def cards_file() -> Path:
    return Path(get("CARDS_FILE", str(Path.home() / "cram" / "data" / "cards.json")))


def vault() -> Path:
    return Path(get("OBSIDIAN_VAULT", str(Path.home() / "blog" / "content")))


def problem_folder() -> str:
    return get("PROBLEM_FOLDER", "Private/Daily/Problems")


def desired_retention() -> float:
    try:
        return float(get("DESIRED_RETENTION", "0.9"))
    except ValueError:
        return 0.9


def leetcode_username() -> str:
    return get("LEETCODE_USERNAME", "")


def theme_name() -> str:
    return get("THEME", "tokyonight")


def is_configured() -> bool:
    cfg_path = config_path()
    return cfg_path.exists() and vault().exists()
