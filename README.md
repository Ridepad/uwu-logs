# UwU Logs

<https://uwu-logs.xyz/>

UwU Logs is a World of Warcraft combat log parser.

Supports any Wrath of the Lich King (3.3.5) server.

❤️ Inspired by World of Logs, LegacyPlayers and Warcraft Logs.

## Self hosting

### Docker Compose (recommended)

Docker runs the four Python services plus an Nginx reverse proxy, so the whole
application is available from a single local URL.

```bash
cp .env.example .env
docker compose up -d --build
```

Open <http://localhost:8080/>.

Useful commands:

```bash
# Follow all logs
docker compose logs -f

# Check container/health status
docker compose ps

# Rebuild from scratch when dependencies change
docker compose build --no-cache
docker compose up -d

# Stop the stack
docker compose down
```

The source tree is bind-mounted at `/app`, which means local code changes and
generated log/database/upload data are shared with all services and survive
container recreation. The public port can be changed with `UWU_HTTP_PORT` in
`.env`.

The upload service intentionally stays at one Uvicorn worker because its chunk
and progress state is held in process memory. For the main service, increase
`UWU_MAIN_THREADS` before increasing `UWU_MAIN_WORKERS`, because opened reports
are also cached in process memory.

If Docker Desktop itself does not have enough RAM/CPU, increase the Docker
Desktop VM resources in Docker Desktop settings. Compose can limit container
resources, but it cannot increase the memory assigned to the Docker engine.

### Python directly

- Install packages from `requirements.txt`

- Run `python Z_SERVER.py` OR `gunicorn3 Z_SERVER:SERVER --port 5000 -D`

- Visit <http://localhost:5000/>

#### Optional
##### Top

- Run `python server_top.py` OR `uvicorn server_top:app --port 5020 --proxy-headers`

##### File uploads

- Run `python server_upload.py` OR `uvicorn server_upload:app --port 5010 --proxy-headers`

##### Download spells/classes icons pack

- [Google Drive download](https://drive.google.com/file/d/17DyiCJts01CkFIkd0-G1dVAypIlxd0pP)
- Preferred layout: `static/icons/*.jpg`.
- UwU Logs also accepts packs nested as `static/icons/static/icons/*.jpg`, so a large pack already copied that way does not need to be moved.
- Verify the installed pack with `python scripts/check_icon_pack.py`.

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

### Comprehensive local smoke-test log

Generate a synthetic WotLK 3.3.5 archive that exercises all ten classes plus
multiple bosses, damage/healing, auras, casts, misses, powers, pet ownership,
a death/resurrection, interrupts/dispels and environmental damage:

```bash
python scripts/generate_comprehensive_test_log.py
```

Upload `test-data/uwu-comprehensive-test-combatlog.zip` from `/upload`.

### Local Ladder WebSocket

The upstream `static/ladder.js` expects a separate production WebSocket on
port `8765`, but that WebSocket server is not included in the public
repository. The Docker self-host setup provides `server_ladder.py` instead and
proxies it through the same site origin at `/ws/ladder`.

The local Ladder reads processed reports from `LogsDir`, sends them as completed
encounters when a browser connects, and polls for newly processed reports. This
makes `/ladder` useful without an external private service.

Optional `.env` settings:

```env
UWU_LADDER_DEFAULT_SIZE=25
UWU_LADDER_DEFAULT_MODE=1
UWU_LADDER_MAX_HISTORY=250
UWU_LADDER_POLL_SECONDS=3
```

After applying the patch, rebuild/start the new service with:

```bash
docker compose up -d --build ladder nginx
```
