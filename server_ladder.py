"""Local/self-hosted WebSocket backend for the PvE Ladder page.

The upstream frontend points at a separate production WebSocket service that is
not part of the public repository.  This service makes the Ladder useful when
self-hosting: it exposes processed reports from LogsDir as completed raid rows
and pushes newly processed reports to connected browsers.
"""

from __future__ import annotations

import asyncio
import bisect
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from c_path import Directories
from h_other import get_report_name_info

app = FastAPI(title="UwU Logs local ladder")

POLL_SECONDS = max(float(os.getenv("UWU_LADDER_POLL_SECONDS", "3")), 1.0)
DEFAULT_SIZE = int(os.getenv("UWU_LADDER_DEFAULT_SIZE", "25"))
DEFAULT_DIFFICULTY = 1 if os.getenv("UWU_LADDER_DEFAULT_MODE", "1") not in {"0", "normal", "Normal"} else 0
MAX_HISTORY = max(int(os.getenv("UWU_LADDER_MAX_HISTORY", "250")), 1)

CLASS_SPEC_INDEX = {
    "Death Knight": 0,
    "Druid": 4,
    "Hunter": 8,
    "Mage": 12,
    "Paladin": 16,
    "Priest": 20,
    "Rogue": 24,
    "Shaman": 28,
    "Warlock": 32,
    "Warrior": 36,
}


def _json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return default


def _report_timestamp(report_id: str) -> float:
    info = get_report_name_info(report_id)
    try:
        dt = datetime.strptime(f"{info['date']}--{info['time']}", "%y-%m-%d--%H-%M")
        return dt.replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        try:
            return (Directories.logs / report_id).stat().st_mtime
        except OSError:
            return datetime.now(tz=timezone.utc).timestamp()


def _duration_seconds(timestamps: list[int], segment) -> int:
    try:
        start, end = int(segment[0]), int(segment[1])
    except (IndexError, TypeError, ValueError):
        return 1

    if timestamps:
        # TIMESTAMP_DATA maps elapsed seconds -> approximate combat-log line.
        start_second = bisect.bisect_left(timestamps, start)
        end_second = bisect.bisect_left(timestamps, end)
        return max(end_second - start_second, 1)

    # A safe fallback when the timestamp cache has not been generated yet.
    return max((end - start) // 10, 1)


def _player_payload(report_dir: Path, author: str):
    players_by_guid = _json(report_dir / "PLAYERS_DATA.json", {})
    classes_by_guid = _json(report_dir / "CLASSES_DATA.json", {})

    if players_by_guid:
        player_names = list(players_by_guid.values())
        player_specs = [
            CLASS_SPEC_INDEX.get(classes_by_guid.get(guid), 12)
            for guid in players_by_guid
        ]
    else:
        player_names = [author or "Unknown"]
        player_specs = [12]

    # Guild/faction data is produced by the private live-ladder collector in
    # production and is not present in parsed combat logs.  Keep the protocol
    # valid locally, using Pug/Alliance as neutral fallbacks.
    guild_names = [""]
    player_guilds = [0 for _ in player_names]
    player_factions = [0 for _ in player_names] or [0]
    return player_names, guild_names, player_guilds, player_specs, player_factions


def report_events(report_dir: Path) -> list[dict]:
    if not report_dir.is_dir():
        return []

    report_id = report_dir.name
    info = get_report_name_info(report_id)
    encounters = _json(report_dir / "ENCOUNTER_DATA.json", {})
    if not isinstance(encounters, dict) or not encounters:
        return []

    timestamps = _json(report_dir / "TIMESTAMP_DATA.json", [])
    players, guilds, player_guilds, specs, factions = _player_payload(
        report_dir, info.get("author", "")
    )
    timestamp = _report_timestamp(report_id)
    server = info.get("server") or "Unknown"

    events = []
    for boss, segments in encounters.items():
        if not isinstance(segments, list) or not segments:
            continue
        last_segment = segments[-1]
        events.append({
            "type": "kill",
            "server": server,
            "timestamp": timestamp,
            "id": f"{report_id}--{boss}",
            "b": boss,
            "s": DEFAULT_SIZE,
            "m": DEFAULT_DIFFICULTY,
            "w": max(len(segments) - 1, 0),
            "t": _duration_seconds(timestamps, last_segment),
            "pn": players,
            "g": guilds,
            "pg": player_guilds,
            "ps": specs,
            "pf": factions,
        })
    return events


def ladder_snapshot() -> list[dict]:
    try:
        report_dirs = sorted(
            (p for p in Directories.logs.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except (FileNotFoundError, OSError):
        return []

    events: list[dict] = []
    for report_dir in report_dirs:
        events.extend(report_events(report_dir))
        if len(events) >= MAX_HISTORY:
            break
    return events[:MAX_HISTORY]


@app.get("/health")
def health():
    return {"status": "ok", "reports": len(ladder_snapshot())}


@app.websocket("/ws/ladder")
async def ladder_socket(websocket: WebSocket):
    await websocket.accept()
    known: set[str] = set()

    try:
        snapshot = ladder_snapshot()
        known.update(event["id"] for event in snapshot)
        # Always send a first frame (even []) so the frontend can mark the
        # socket as connected immediately.
        await websocket.send_json(snapshot)

        while True:
            await asyncio.sleep(POLL_SECONDS)
            current = ladder_snapshot()
            new_events = [event for event in current if event["id"] not in known]
            if not new_events:
                continue
            known.update(event["id"] for event in new_events)
            await websocket.send_json(new_events)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
