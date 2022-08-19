# UwU Logs

<https://uwu-logs.xyz/> WotLK logs parser.

## Showcase

### Top

<https://uwu-logs.xyz/top>

![Showcase top](https://raw.githubusercontent.com/Ridepad/uwu-logs/main/showcase/top.png)

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

### Main

- friendly fire: Bloodbolt Splash, ucm, vortex
- self harm: ucm, Chilled to the Bone
- deaths
- dmg taken
- site side logs parser - filter forms - guid spell etc

### Each fight unique summary

- spirit explosion - triggered by
- beast dmg
- portal stacks
- valk grabs + necrotic + defile targets

### Other

- mobile version - hide everything in dropdown
- 1st footer for mobile with back button to report - report name - expand button
- 2nd footer for mobile with back button to encoutner - encounter - expand button - search button

- comparison  - +- dmg hits crits - chose same class from past = open logs' players+classes

- blood mark as dk heal
- if attribute error in report class prevent dublicates

- buffs before combat
- fix unlogical buff duration max 30 sec? last combat log entry? filter out long spells - ff hmark
- buff uptime - remove abnormal long buffs
- if buff not in long_buffs check top50% avg of this buff

- if valk fast life siphon = warlock
- check the best dps can get = if all hits = crits

- add summary stats like max hit done max hit taken max absorb max grabs
- graphs?
- finish absorbs KEKW
- 1 tick total - all targets dmg from 1 hurricane tick or typhoon

- check if Valkyr in logs or check if slice crosses enc_data[boss]

- boss = hp > avg hp of all units
- if target dmgtaken > other targets = boss
