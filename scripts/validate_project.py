"""Validate the platform-neutral audiobook workflow example project."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    project = load_json(root / "project.json")
    require(project.get("project_id"), "project_id is required")
    require(project.get("chapters"), "at least one chapter is required")

    script = load_json(root / project["chapters"][0]["script"])
    segments = script.get("segments", [])
    require(segments, "script must contain segments")
    segment_ids = [segment.get("segment_id") for segment in segments]
    require(all(segment_ids), "every script segment needs segment_id")
    require(len(segment_ids) == len(set(segment_ids)), "segment_id values must be unique")

    alignment = load_json(root / "examples/chapter-01.alignment.json")
    for item in alignment.get("items", []):
        require(item.get("segment_id") in segment_ids, f"unknown alignment segment_id: {item.get('segment_id')}")
        require(item.get("end", 0) > item.get("start", 0), f"invalid alignment range: {item.get('segment_id')}")

    cues = load_json(root / "examples/chapter-01.cues.json")
    assets = load_json(root / "library/audio-assets.json")
    asset_ids = {asset.get("asset_id") for asset in assets.get("assets", [])}
    for cue in cues.get("cues", []):
        require(cue.get("segment_id") in segment_ids, f"unknown cue segment_id: {cue.get('segment_id')}")
        require(cue.get("asset_id") in asset_ids, f"unknown cue asset_id: {cue.get('asset_id')}")

    print(f"OK: {project['project_id']} ({len(segment_ids)} segments validated)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
