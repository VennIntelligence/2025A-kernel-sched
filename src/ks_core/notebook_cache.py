"""Shared helpers for notebook cache builders and display."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from IPython.display import Image as NotebookImage
from IPython.display import display


def project_root(start: Path | None = None) -> Path:
    """Walk up from *start* to find the project root (directory containing pyproject.toml)."""
    root = (start or Path.cwd()).resolve()
    while not (root / "pyproject.toml").exists() and root != root.parent:
        root = root.parent
    if not (root / "pyproject.toml").exists():
        raise FileNotFoundError("Could not locate project root (pyproject.toml missing).")
    return root


def figure_path(output_dir: Path, name: str) -> Path:
    """Return the full path for a cached figure inside *output_dir*."""
    return output_dir / Path(name).name


def missing_artifacts(output_dir: Path, names: Iterable[str]) -> list[str]:
    """Return names of artifacts that are missing from *output_dir*."""
    return [name for name in names if not (output_dir / name).exists()]


def require_artifacts(
    output_dir: Path,
    names: Iterable[str],
    *,
    rebuild_command: str,
) -> None:
    """Raise FileNotFoundError if any required artifacts are missing."""
    missing = missing_artifacts(output_dir, names)
    if missing:
        raise FileNotFoundError(
            f"Cache incomplete in {output_dir}. Missing: {', '.join(missing)}\n"
            f"Run: {rebuild_command}"
        )


def write_manifest(
    output_dir: Path,
    *,
    version: int,
    artifacts: Iterable[str],
    rebuild_command: str,
    extra: dict | None = None,
) -> dict:
    """Write a cache_manifest.json to *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": version,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": list(artifacts),
        "rebuild_command": rebuild_command,
    }
    if extra:
        manifest.update(extra)
    path = output_dir / "cache_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_manifest(output_dir: Path) -> dict:
    """Load cache_manifest.json from *output_dir*, or return empty dict."""
    path = output_dir / "cache_manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def cache_is_complete(output_dir: Path, artifacts: Iterable[str]) -> bool:
    """Return True if all *artifacts* exist in *output_dir*."""
    return not missing_artifacts(output_dir, artifacts)


def clear_output_dir(output_dir: Path) -> None:
    """Remove stale generated cache artifacts inside one output directory."""
    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise NotADirectoryError(output_dir)
    for child in output_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def show_fig(
    output_dir: Path,
    name: str,
    *,
    rebuild_command: str | None = None,
) -> None:
    """Display a cached PNG via NotebookImage (retina). For use in notebook fragments."""
    path = figure_path(output_dir, name)
    if not path.exists():
        hint = rebuild_command or "uv run python scripts/build_XXX_cache.py"
        raise FileNotFoundError(f"Missing cached figure: {path}\nRun: {hint}")
    display(NotebookImage(filename=str(path), retina=True))
