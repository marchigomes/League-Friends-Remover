# League of Legends Friend Remover

A small Windows utility that removes all League of Legends friends through the local Riot Client API.

## Features

- Prompts for the League of Legends installation folder.
- Automatically locates the Riot Client `lockfile`.
- Creates a JSON backup before removing anything.
- Requires an explicit `DELETE` confirmation.
- Can be distributed as a standalone Windows `.exe` file.

## Usage

1. Open the Riot Client and League of Legends.
2. Run `dist\RemoverAmigosLoL.exe`.
3. Enter the game folder, for example `C:\Riot Games\League of Legends`.
4. Review the number of friends and the backup path.
5. Type `DELETE` to confirm the operation.

The backup is saved in the same directory where the program is executed. Friend removal is destructive, so keep the backup if you may need the previous list.

## Build from source

Requires Python 3.10 or newer and Windows PowerShell. Run `./build.ps1`. The executable is generated at `dist\RemoverAmigosLoL.exe`.

## Suggested GitHub description

> Windows utility to remove League of Legends friends through the local Riot Client API, with automatic backups and a standalone executable.

## Disclaimer

This project is an independent utility and is not affiliated with or endorsed by Riot Games. Use it at your own risk and review the generated backup before confirming deletion.
