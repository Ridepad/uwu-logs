#!/usr/bin/env python3
"""Check that the local icon pack contains the class/spec icons UwU Logs uses."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from c_player_classes import CLASSES  # noqa: E402
from icon_assets import discover_icon_pack_root, iter_icon_roots, resolve_icon_file  # noqa: E402


def main() -> int:
    print("UwU Logs icon pack check")
    print("Search paths:")
    for root in iter_icon_roots():
        marker = "OK" if root.is_dir() else "--"
        print(f"  [{marker}] {root}")

    detected = discover_icon_pack_root()
    print(f"\nDetected pack: {detected or 'NONE'}")

    expected = sorted({icon for specs in CLASSES.values() for icon in specs.values()})
    missing = [name for name in expected if resolve_icon_file(f"{name}.jpg") is None]

    print(f"Expected class/spec icons: {len(expected)}")
    print(f"Found: {len(expected) - len(missing)}")
    print(f"Missing: {len(missing)}")

    if missing:
        print("\nMissing icon files:")
        for name in missing:
            print(f"  - {name}.jpg")
        return 1

    print("\nAll class/spec icons are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
