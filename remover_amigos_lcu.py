"""Remove all League of Legends friends through the local Riot Client API."""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


def find_lockfile(game_dir: Path) -> Path:
    candidates = [
        game_dir / "lockfile",
        game_dir / "LeagueClient" / "lockfile",
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Riot Games" / "League of Legends" / "lockfile",
        Path(r"C:\Riot Games\League of Legends\lockfile"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("Lockfile not found. Open the Riot Client and League of Legends first.")


def read_lockfile(path: Path) -> tuple[str, str]:
    fields = path.read_text(encoding="utf-8").strip().split(":")
    if len(fields) != 5:
        raise RuntimeError(f"Formato inesperado do lockfile: {path}")
    _, _, port, password, protocol = fields
    return f"{protocol}://127.0.0.1:{port}", password


class Lcu:
    def __init__(self, base_url: str, password: str) -> None:
        token = base64.b64encode(f"riot:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}"}
        self.base_url = base_url
        self.context = ssl._create_unverified_context()

    def request(self, method: str, path: str):
        request = urllib.request.Request(self.base_url + path, method=method, headers=self.headers)
        with urllib.request.urlopen(request, context=self.context, timeout=10) as response:
            if response.status == 204:
                return None
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="confirm without asking for DELETE")
    args = parser.parse_args()

    game_input = input("Enter the League of Legends folder path: ").strip().strip('"')
    game_dir = Path(game_input)
    if not game_dir.is_dir():
        print(f"Folder not found: {game_dir}", file=sys.stderr)
        return 1

    try:
        lockfile = find_lockfile(game_dir)
        base_url, password = read_lockfile(lockfile)
        lcu = Lcu(base_url, password)
        friends = lcu.request("GET", "/lol-chat/v1/friends") or []
    except (OSError, urllib.error.URLError, RuntimeError, ValueError) as exc:
        print(f"Could not connect to the Riot Client: {exc}", file=sys.stderr)
        return 1

    if not isinstance(friends, list):
        print("Unexpected response while retrieving the friend list.", file=sys.stderr)
        return 1

    backup = Path.cwd() / f"amigos_lol_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.write_text(json.dumps(friends, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Friends found: {len(friends)}\nBackup saved to: {backup}")
    if not friends:
        print("The friend list is already empty.")
        return 0
    if not args.yes and input("Type DELETE to remove all friends: ") != "DELETE":
        print("Cancelled; no friends were removed.")
        return 0

    removed = 0
    for round_number in range(1, 21):
        current = lcu.request("GET", "/lol-chat/v1/friends") or []
        if not current:
            break
        print(f"Round {round_number}: {len(current)} friend(s) remaining.")
        progress = False
        for friend in current:
            friend_id = friend.get("id") if isinstance(friend, dict) else None
            if not friend_id:
                continue
            try:
                lcu.request("DELETE", f"/lol-chat/v1/friends/{friend_id}")
                removed += 1
                progress = True
                print(f"Removed: {friend.get('name', friend_id)}")
            except urllib.error.HTTPError as exc:
                print(f"Failed for {friend_id}: HTTP {exc.code}", file=sys.stderr)
        if not progress:
            break
        time.sleep(0.5)

    remaining = lcu.request("GET", "/lol-chat/v1/friends") or []
    print(f"Finished: {removed} removal(s) processed, {len(remaining)} friend(s) remaining.")
    return 0 if not remaining else 2


if __name__ == "__main__":
    raise SystemExit(main())
