from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_BASE_DIR = Path(__file__).resolve().parent


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def get_active_project_name() -> str:
    env = os.getenv("ACTIVE_PROJECT")
    if env:
        return env
    platform_cfg = _load_yaml(_BASE_DIR / "config.yaml")
    return platform_cfg["active_project"]


def get_project_dir(name: str | None = None) -> Path:
    return _BASE_DIR / "projects" / (name or get_active_project_name())


def list_projects() -> list[str]:
    """Liste les noms de tous les projets disponibles (dossiers avec config.yaml)."""
    projects_dir = _BASE_DIR / "projects"
    if not projects_dir.exists():
        return []
    return sorted(
        d.name for d in projects_dir.iterdir()
        if d.is_dir() and (d / "config.yaml").exists()
    )


def load_project_config(name: str | None = None) -> dict[str, Any]:
    path = get_project_dir(name) / "config.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"Config introuvable pour le projet '{name or get_active_project_name()}': {path}"
        )
    return _load_yaml(path)
