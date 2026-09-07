from datetime import datetime, timedelta
from pathlib import Path
import argparse
from zipfile import ZipFile, ZIP_STORED

parser = argparse.ArgumentParser(description='Generate a synthetic WotLK 3.3.5 combat log that exercises UwU Logs reports.')
parser.add_argument('--output-dir', default='test-data', help='Directory where the .txt and .zip are written (default: test-data)')
args = parser.parse_args()
OUT = Path(args.output_dir).resolve()
OUT.mkdir(parents=True, exist_ok=True)
RAW = OUT / 'WoWCombatLog-comprehensive-test.txt'
ZIP = OUT / 'uwu-comprehensive-test-combatlog.zip'

start = datetime(2026, 9, 7, 5, 0, 0)
seq_ms = 0
lines = []

PLAYER_FLAG = '0x511'
BOSS_FLAG = '0x10a48'
PET_FLAG = '0x1114'
NIL = '0x0000000000000000'
NIL_FLAG = '0x80000000'

players = {
    'dk':      ('0x0700000000ABC001', 'Testdk'),
    'druid':   ('0x0700000000ABC002', 'Testdruid'),
    'hunter':  ('0x0700000000ABC003', 'Testhunter'),
    'mage':    ('0x0700000000ABC004', 'Testmage'),
    'paladin': ('0x0700000000ABC005', 'Testpaladin'),
    'priest':  ('0x0700000000ABC006', 'Testpriest'),
    'rogue':   ('0x0700000000ABC007', 'Testrogue'),
    'shaman':  ('0x0700000000ABC008', 'Testshaman'),
    'warlock': ('0x0700000000ABC009', 'Testlock'),
    'warrior': ('0x0700000000ABC00A', 'Testwarrior'),
}
pet = ('0xF1400046ED000001', 'Testwolf')

bosses = [
    ('008F04', 'Lord Marrowgar'),
    ('008FF7', 'Lady Deathwhisper'),
    ('0093B5', 'Deathbringer Saurfang'),
]

# spells: role -> (spell id, name, school, event type)
main_spells = {
    'dk':      (51735, 'Ebon Plague', '0x20', 'SPELL_DAMAGE'),
    'druid':   (48468, 'Insect Swarm', '0x8', 'SPELL_PERIODIC_DAMAGE'),
    'hunter':  (53209, 'Chimera Shot', '0x1', 'RANGE_DAMAGE'),
    'mage':    (12654, 'Ignite', '0x4', 'SPELL_PERIODIC_DAMAGE'),
    'paladin': (35395, 'Crusader Strike', '0x1', 'SPELL_DAMAGE'),
    'priest':  (48089, 'Circle of Healing', '0x2', 'SPELL_HEAL'),
    'rogue':   (48638, 'Sinister Strike', '0x1', 'SPELL_DAMAGE'),
    'shaman':  (53390, 'Tidal Waves', '0x8', 'SPELL_AURA_APPLIED'),
    'warlock': (47843, 'Unstable Affliction', '0x20', 'SPELL_PERIODIC_DAMAGE'),
    'warrior': (23894, 'Bloodthirst', '0x1', 'SPELL_DAMAGE'),
}

# Extra well-known class spells make class detection and spell pages richer.
extra_damage = {
    'dk':      (49909, 'Icy Touch', '0x10'),
    'druid':   (48465, 'Starfire', '0x40'),
    'hunter':  (49050, 'Aimed Shot', '0x1'),
    'mage':    (42833, 'Fireball', '0x4'),
    'paladin': (54172, 'Divine Storm', '0x2'),
    'priest':  (58381, 'Mind Flay', '0x20'),
    'rogue':   (48668, 'Eviscerate', '0x1'),
    'shaman':  (49233, 'Flame Shock', '0x4'),
    'warlock': (47809, 'Shadow Bolt', '0x20'),
    'warrior': (47450, 'Heroic Strike', '0x1'),
}


def ts(dt):
    return f'{dt.month}/{dt.day} {dt:%H:%M:%S}.{dt.microsecond // 1000:03d}'


def emit(event, src, dst, payload='', advance=80):
    global seq_ms
    dt = start + timedelta(milliseconds=seq_ms)
    seq_ms += advance
    sguid, sname, sflag = src
    dguid, dname, dflag = dst
    suffix = f',{payload}' if payload else ''
    lines.append(f'{ts(dt)}  {event},{sguid},"{sname}",{sflag},{dguid},"{dname}",{dflag}{suffix}')


def player(role):
    g,n = players[role]
    return g,n,PLAYER_FLAG


def boss(gid, name):
    return f'0xF130{gid}000001', name, BOSS_FLAG


def damage(event, src, dst, sid, name, school, amount, overkill=0, crit=False):
    # WotLK 3.3.5 spell/range/periodic damage payload.
    payload = f'{sid},"{name}",{school},{amount},{overkill},{int(school,16)},0,0,0,{1 if crit else "nil"},nil,nil'
    emit(event, src, dst, payload)


def swing_damage(src, dst, amount, overkill=0):
    payload = f'{amount},{overkill},1,0,0,0,nil,nil,nil'
    emit('SWING_DAMAGE', src, dst, payload)


def spell_miss(event, src, dst, sid, name, school, miss='MISS'):
    emit(event, src, dst, f'{sid},"{name}",{school},{miss}')


def cast(src, dst, sid, name, school='0x1', event='SPELL_CAST_SUCCESS'):
    emit(event, src, dst, f'{sid},"{name}",{school}')


def heal(src, dst, sid, name, school, amount, overheal=0, crit=False, periodic=False):
    event = 'SPELL_PERIODIC_HEAL' if periodic else 'SPELL_HEAL'
    # amount, overheal, absorbed, critical
    emit(event, src, dst, f'{sid},"{name}",{school},{amount},{overheal},0,{1 if crit else "nil"}')


def aura(event, src, dst, sid, name, school='0x1', aura_type='BUFF', amount=None):
    payload = f'{sid},"{name}",{school},{aura_type}'
    if amount is not None:
        payload += f',{amount}'
    emit(event, src, dst, payload)


def energize(src, dst, sid, name, school, amount, power_type):
    emit('SPELL_ENERGIZE', src, dst, f'{sid},"{name}",{school},{amount},{power_type}')


def interrupt(src, dst, sid, name, school, extra_sid, extra_name, extra_school):
    emit('SPELL_INTERRUPT', src, dst, f'{sid},"{name}",{school},{extra_sid},"{extra_name}",{extra_school}')


def dispel(src, dst, sid, name, school, extra_sid, extra_name, extra_school, aura_type='DEBUFF'):
    emit('SPELL_DISPEL', src, dst, f'{sid},"{name}",{school},{extra_sid},"{extra_name}",{extra_school},{aura_type}')


def unit_died(dst):
    emit('UNIT_DIED', (NIL, 'nil', NIL_FLAG), dst)


def resurrect(src, dst, sid=2006, name='Resurrection', school='0x2'):
    emit('SPELL_RESURRECT', src, dst, f'{sid},"{name}",{school}')


# Upload author / realm inference line. The normalizer intentionally removes this later.
emit('SPELL_CAST_FAILED', player('mage'), (NIL, 'nil', NIL_FLAG), '42833,"Fireball",0x4,"Not yet recovered"', advance=120)

# Pre-combat consumables and external buffs. These make the consumables/auras pages useful.
for role in players:
    cast(player(role), player(role), 53908, 'Potion of Speed', '0x1')
    aura('SPELL_AURA_APPLIED', player(role), player(role), 53908, 'Potion of Speed', '0x1', 'BUFF')

cast(player('shaman'), player('shaman'), 2825, 'Bloodlust', '0x8')
for role in players:
    aura('SPELL_AURA_APPLIED', player('shaman'), player(role), 2825, 'Bloodlust', '0x8', 'BUFF')
aura('SPELL_AURA_APPLIED', player('mage'), player('warlock'), 54646, 'Focus Magic', '0x40', 'BUFF')
aura('SPELL_AURA_APPLIED', player('rogue'), player('hunter'), 57933, 'Tricks of the Trade', '0x1', 'BUFF')
aura('SPELL_AURA_APPLIED', player('priest'), player('warrior'), 48066, 'Power Word: Shield', '0x2', 'BUFF')
aura('SPELL_AURA_APPLIED', player('paladin'), player('warrior'), 58597, 'Sacred Shield', '0x2', 'BUFF')

# Hunter permanent pet association.
cast(player('hunter'), (pet[0], pet[1], PET_FLAG), 883, 'Call Pet', '0x1', event='SPELL_SUMMON')

for fight_i, (boss_id, boss_name) in enumerate(bosses):
    b = boss(boss_id, boss_name)

    # Explicit spec/class-identifying events at the start of every fight.
    for role, (sid, sname, school, etype) in main_spells.items():
        src = player(role)
        if etype == 'SPELL_HEAL':
            heal(src, player('warrior'), sid, sname, school, 6500, 500)
        elif etype == 'SPELL_AURA_APPLIED':
            aura('SPELL_AURA_APPLIED', src, src, sid, sname, school, 'BUFF')
        elif etype == 'RANGE_DAMAGE':
            damage('RANGE_DAMAGE', src, b, sid, sname, school, 4200)
        else:
            damage(etype, src, b, sid, sname, school, 3900)

    # Boss debuffs and raid buffs for aura tabs.
    aura('SPELL_AURA_APPLIED', b, player('warrior'), 69065 + fight_i, f'Test Boss Debuff {fight_i+1}', '0x20', 'DEBUFF')
    aura('SPELL_AURA_APPLIED_DOSE', b, player('warrior'), 69065 + fight_i, f'Test Boss Debuff {fight_i+1}', '0x20', 'DEBUFF', 2)

    for i in range(155):
        # Ten classes contribute damage; enough relevant lines for boss-fight detection.
        for idx, role in enumerate(players):
            src = player(role)
            sid, sname, school = extra_damage[role]
            amount = 2500 + idx * 180 + (i % 17) * 37
            crit = (i + idx) % 7 == 0
            if role == 'hunter':
                damage('RANGE_DAMAGE', src, b, sid, sname, school, amount, crit=crit)
            elif role in {'druid', 'mage', 'warlock'} and i % 3 == 0:
                damage('SPELL_PERIODIC_DAMAGE', src, b, sid, sname, school, amount // 2, crit=crit)
            else:
                damage('SPELL_DAMAGE', src, b, sid, sname, school, amount, crit=crit)

        # Pet damage rolls into hunter ownership when pet resolution succeeds.
        if i % 2 == 0:
            damage('SPELL_DAMAGE', (pet[0], pet[1], PET_FLAG), b, 52472, 'Bite', '0x1', 900 + (i % 11) * 13)

        # Tank incoming damage + misses for TAKEN and death-history pages.
        swing_damage(b, player('warrior'), 2600 + (i % 19) * 31)
        if i % 4 == 0:
            damage('SPELL_DAMAGE', b, player('warrior'), 69055 + fight_i, f'Test Boss Strike {fight_i+1}', '0x1', 3500 + i * 2)
        if i % 7 == 0:
            spell_miss('SPELL_MISSED', b, player('warrior'), 69055 + fight_i, f'Test Boss Strike {fight_i+1}', '0x1', 'DODGE')

        # Healing, overhealing and HoTs.
        heal(player('priest'), player('warrior'), 48071, 'Flash Heal', '0x2', 5200, 600, crit=(i % 6 == 0))
        heal(player('shaman'), player('warrior'), 49276, 'Lesser Healing Wave', '0x8', 4700, 300, crit=(i % 5 == 0))
        if i % 3 == 0:
            heal(player('druid'), player('warrior'), 48441, 'Rejuvenation', '0x8', 1800, 100, periodic=True)

        # Resource generation for POWERS (mana/rage/energy/runic).
        if i % 8 == 0:
            energize(player('shaman'), player('shaman'), 16190, 'Mana Tide', '0x8', 800, 0)
            energize(player('warrior'), player('warrior'), 29842, 'Second Wind', '0x1', 10, 1)
            energize(player('rogue'), player('rogue'), 35546, 'Combat Potency', '0x1', 15, 3)
            energize(player('dk'), player('dk'), 49088, 'Bladed Armor Test', '0x1', 12, 6)

        # Timeline extras.
        if i % 25 == 0:
            cast(player('mage'), b, 2139, 'Counterspell', '0x40')
            interrupt(player('mage'), b, 2139, 'Counterspell', '0x40', 69070 + fight_i, 'Test Boss Cast', '0x20')
            dispel(player('priest'), player('warrior'), 988, 'Dispel Magic', '0x2', 69065 + fight_i, f'Test Boss Debuff {fight_i+1}', '0x20')

        # Exercise aura refresh/dose/remove handling.
        if i == 60:
            aura('SPELL_AURA_REFRESH', player('warlock'), b, 47843, 'Unstable Affliction', '0x20', 'DEBUFF')
        if i == 90:
            aura('SPELL_AURA_REMOVED_DOSE', b, player('warrior'), 69065 + fight_i, f'Test Boss Debuff {fight_i+1}', '0x20', 'DEBUFF', 1)

        # One real player death + resurrection during Deathwhisper.
        if fight_i == 1 and i == 105:
            damage('SPELL_DAMAGE', b, player('rogue'), 69099, 'Synthetic Fatal Strike', '0x1', 16000, overkill=4000)
            unit_died(player('rogue'))
        if fight_i == 1 and i == 112:
            resurrect(player('priest'), player('rogue'))

        # Environmental damage parser coverage.
        if fight_i == 2 and i == 80:
            emit('ENVIRONMENTAL_DAMAGE', (NIL, 'nil', NIL_FLAG), player('mage'), 'FALLING,1750,0,1,0,0,0,nil,nil,nil')

    aura('SPELL_AURA_REMOVED', b, player('warrior'), 69065 + fight_i, f'Test Boss Debuff {fight_i+1}', '0x20', 'DEBUFF')
    # Finish boss with overkill and explicit UNIT_DIED.
    damage('SPELL_DAMAGE', player('mage'), b, 42833, 'Fireball', '0x4', 12000, overkill=2500, crit=True)
    unit_died(b)

    # Next boss starts quickly enough to remain in the same uploaded report slice.
    seq_ms += 12_000

# Remove long-lived buffs at report end.
for role in players:
    aura('SPELL_AURA_REMOVED', player('shaman'), player(role), 2825, 'Bloodlust', '0x8', 'BUFF')

text = '\n'.join(lines) + '\n'
RAW.write_text(text, encoding='utf-8')
with ZipFile(ZIP, 'w', compression=ZIP_STORED) as zf:
    zf.write(RAW, arcname='WoWCombatLog.txt')

print(RAW)
print(ZIP)
print('lines=', len(lines))
print('raw_bytes=', RAW.stat().st_size)
print('zip_bytes=', ZIP.stat().st_size)
