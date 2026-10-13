"""Remove todos os amigos do League of Legends usando a API local do Riot Client."""

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
    raise FileNotFoundError("lockfile não encontrado. Abra o Riot Client/League of Legends antes de executar.")


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
    parser.add_argument("--yes", action="store_true", help="confirma sem pedir APAGAR")
    args = parser.parse_args()

    game_input = input("Digite o caminho da pasta do League of Legends: ").strip().strip('"')
    game_dir = Path(game_input)
    if not game_dir.is_dir():
        print(f"Pasta não encontrada: {game_dir}", file=sys.stderr)
        return 1

    try:
        lockfile = find_lockfile(game_dir)
        base_url, password = read_lockfile(lockfile)
        lcu = Lcu(base_url, password)
        friends = lcu.request("GET", "/lol-chat/v1/friends") or []
    except (OSError, urllib.error.URLError, RuntimeError, ValueError) as exc:
        print(f"Erro ao conectar ao Riot Client: {exc}", file=sys.stderr)
        return 1

    if not isinstance(friends, list):
        print("Resposta inesperada ao consultar a lista de amigos.", file=sys.stderr)
        return 1

    backup = Path.cwd() / f"amigos_lol_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    backup.write_text(json.dumps(friends, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Amigos encontrados: {len(friends)}\nBackup salvo em: {backup}")
    if not friends:
        print("A lista já está vazia.")
        return 0
    if not args.yes and input("Digite APAGAR para remover todos os amigos: ") != "APAGAR":
        print("Cancelado; nenhum amigo foi removido.")
        return 0

    removed = 0
    for round_number in range(1, 21):
        current = lcu.request("GET", "/lol-chat/v1/friends") or []
        if not current:
            break
        print(f"Rodada {round_number}: {len(current)} amigo(s) restante(s).")
        progress = False
        for friend in current:
            friend_id = friend.get("id") if isinstance(friend, dict) else None
            if not friend_id:
                continue
            try:
                lcu.request("DELETE", f"/lol-chat/v1/friends/{friend_id}")
                removed += 1
                progress = True
                print(f"Removido: {friend.get('name', friend_id)}")
            except urllib.error.HTTPError as exc:
                print(f"Falha em {friend_id}: HTTP {exc.code}", file=sys.stderr)
        if not progress:
            break
        time.sleep(0.5)

    remaining = lcu.request("GET", "/lol-chat/v1/friends") or []
    print(f"Concluído: {removed} remoções processadas, {len(remaining)} amigo(s) restante(s).")
    return 0 if not remaining else 2


if __name__ == "__main__":
    raise SystemExit(main())
