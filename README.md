# UwU Logs

<https://uwu-logs.xyz/>

UwU Logs is a World of Warcraft combat log parser.

Supports any Wrath of the Lich King (3.3.5) server.

❤️ Inspired by World of Logs, LegacyPlayers and Warcraft Logs.

## Self hosting

- Install packages from `requirements.txt`

- Run `python Z_SERVER.py` OR `gunicorn3 Z_SERVER:SERVER -D --port 5000`

- Visit <http://localhost:5000/>

#### Optional
##### File uploads

- Run `python api_upload.py` OR `uvicorn api_upload:app --port 5010`

##### Download spells/classes icons pack

- [Google Drive download](https://drive.google.com/file/d/17DyiCJts01CkFIkd0-G1dVAypIlxd0pP)

- Extract to root folder.

## Showcase

### Top

<https://uwu-logs.xyz/top>

![Showcase top](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/static/thumb.png)

### PvE Statistics

<https://uwu-logs.xyz/top_stats>

![Showcase PvE statistics](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/pve_stats.png)

### Player total and per target spell info

![Showcase player spell info](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/spell_info.png)

### Damage to targets + useful

![Showcase useful](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/useful.png)

### Player comparison

![Showcase comparison](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/compare.png)

### Spell search and overall info

![Showcase spell search](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/spells.png)

### Consumables

![Showcase consumables](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/consume.png)

## TODO

- friendly fire: Bloodbolt Splash, ucm, vortex
- self harm: ucm, Chilled to the Bone
- site side logs parser - filter forms - guid spell etc

- portal stacks
- valk grabs + necrotic + defile targets

- fix unlogical buff duration max 30 sec? last combat log entry? filter out long spells - ff hmark
- if buff not in long_buffs check top50% avg of this buff

- add summary stats like max hit done max hit taken max absorb max grabs
- 1 tick total - all targets dmg from 1 hurricane tick or typhoon
