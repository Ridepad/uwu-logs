"""Resolve WoW icon assets from common self-host icon-pack layouts.

Browser URLs stay stable as ``/static/icons/<name>.jpg``.  The downloaded icon
pack is sometimes copied with its own ``static/icons`` folders still inside
it, producing ``static/icons/static/icons/*.jpg``.  This module resolves both
the canonical and the accidentally nested layouts without moving thousands
of files on disk.
"""

from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = PROJECT_ROOT / "static"

# Prefer the canonical layout first, then common extraction/copy layouts.
ICON_ROOT_CANDIDATES = (
    STATIC_ROOT / "icons",
    STATIC_ROOT / "icons" / "static" / "icons",
    STATIC_ROOT / "icons" / "icons",
    STATIC_ROOT / "static" / "icons",
    PROJECT_ROOT / "icons",
    PROJECT_ROOT / "icons" / "static" / "icons",
)

_ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_ICON_CACHE: dict[str, Path] = {}


def iter_icon_roots() -> Iterable[Path]:
    """Yield unique icon roots in lookup priority order."""
    seen: set[Path] = set()
    for root in ICON_ROOT_CANDIDATES:
        root = root.resolve(strict=False)
        if root not in seen:
            seen.add(root)
            yield root


def _safe_filename(filename: str) -> str | None:
    """Accept only one image filename; never permit path traversal."""
    if not isinstance(filename, str) or not filename:
        return None
    if "/" in filename or "\\" in filename or filename in {".", ".."}:
        return None
    if Path(filename).suffix.lower() not in _ALLOWED_SUFFIXES:
        return None
    return filename


def resolve_icon_file(filename: str) -> Path | None:
    """Return the first matching icon across supported pack layouts."""
    filename = _safe_filename(filename)
    if filename is None:
        return None

    cached = _ICON_CACHE.get(filename)
    if cached is not None and cached.is_file():
        return cached

    for root in iter_icon_roots():
        candidate = root / filename
        if candidate.is_file():
            _ICON_CACHE[filename] = candidate
            return candidate

    return None


def discover_icon_pack_root() -> Path | None:
    """Return the first candidate directory that currently contains JPGs."""
    for root in iter_icon_roots():
        if not root.is_dir():
            continue
        try:
            if next(root.glob("*.jpg"), None) is not None:
                return root
        except OSError:
            continue
    return None
