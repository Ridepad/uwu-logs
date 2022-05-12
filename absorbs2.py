from constants import to_dt
import _main
from datetime import timedelta

DELTA = timedelta(seconds=1)

ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SWING_MISSED', 'SPELL_MISSED'}
ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SPELL_MISSED'}
DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_AURA_REMOVED'}
AURAS_NAME = {'Protection of Ancient Kings', 'Power Word: Shield', 'Divine Aegis', 'Sacred Shield', 'Hardened Skin', 'Anti-Magic Shell', 'Savage Defense'}
AURAS_ID = {'64413', '48066', '47753', '58597', '48707', '55233'}
HEALS = {'SPELL_HEAL', 'SPELL_PERIODIC_HEAL'}

SS = {'64413', '47753'}
AURAS_ID = {'64413', '48066', '47753', '58597'}
FFF = {'Sacred Shield', 'Power Word: Shield', 'Anti-Magic Shell'}
AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH'}
ABSORB_SPELL_IDS = {'58597', '48066', '48707', '6940', '71586'}
SHIELDS_SPELL_IDS = {'64413', '47753'}
SPELL_DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}

# Hardened Skin 6400

class FUCKINGBULLSHIT:
    def __init__(self, logs_slice: list, guid: str, char_class: str) -> None:
        self.logs = logs_slice
        self.guid = guid
        self.char_class = char_class
        self.is_dk = char_class == 'death-knight'
        self.is_pal = char_class == 'paladin'
        self.pws = []
        self.current_absorb = 0
        self.current_auras = {}
        self.absorbs = {}
        self.last_dmg = 0

    def zzprint(self, f, spell_name, source_guid, amount=""):
        name = LOGS.guid_to_name(source_guid)
        print(f'{f}: {spell_name:>30} | {name:>12} | {amount:>5}')

    def add_absorb(self, guid, spell_name, value):
        j = self.absorbs.setdefault(guid, {})
        j[spell_name] = j.get(spell_name, 0) + value
        self.zzprint('ADDED SHIELD', spell_name, guid, value)

    def top_shield_removed(self, guid, spell_name):
        self.current_auras[spell_name].pop(guid)
        if not self.current_auras[spell_name]:
            self.current_auras.pop(spell_name)
        self.zzprint('AURA REMOVED', spell_name, guid)

    def aura_applied(self, spell_name, source_guid):
        self.current_auras[spell_name] = {source_guid: True}
        self.zzprint('AURA APPLIED', spell_name, source_guid)

    def get_last_heal(self, n: int, timestamp: str, source_guid: str, target_guid: str):
        # check if same second
        st = to_dt(timestamp)
        for line in reversed(self.logs[:n]):
            if target_guid in line:
                line = line.split(',')
                if line[2] == source_guid and line[4] == target_guid and 'HEAL' in line[1]:
                    now = to_dt(line[0])
                    if st - now <= DELTA:
                        return int(line[9])
                    return 0

    def aura_applied_by_heal(self, last_heal, source_guid, spell_id, spell_name):
        s = (spell_id == "47753") + 1
        mult = 0.15 * s
        _shield = int(last_heal*mult)
        q = self.current_auras.setdefault(spell_name, {})
        n = q.get(source_guid, 0) + _shield
        n = min(n, 10000 * s)
        q[source_guid] = n
        self.zzprint('NEW   SHIELD', spell_name, source_guid, _shield)

    def calc_ams(self, target_guid):
        # check if less <50% hp = 30k max
        # make sure all absorb != ams
        spell_name = 'Anti-Magic Shell'
        ams = (self.new_absorb + self.last_dmg) // 4 * 3
        self.add_absorb(target_guid, spell_name, ams)
        self.new_absorb -= ams
        if self.current_absorb < 10:
            self.current_absorb = 0

    def calc_hos(self):
        spell_name = 'Hand of Sacrifice'
        source_guid = list(self.current_auras[spell_name])[0]
        hos = (self.new_absorb + self.last_dmg) * 0.3
        hos = int(hos)
        self.add_absorb(source_guid, spell_name, hos)
        self.new_absorb -= hos
        if self.new_absorb < 10:
            self.new_absorb = 0

    def calc_sure_shield(self, removed_auras, spell_name):
        if spell_name in removed_auras:
            source_guid = removed_auras.pop(spell_name)
            t = self.current_auras[spell_name].pop(source_guid)
            self.add_absorb(source_guid, spell_name, t)
            self.current_absorb -= t
        if self.current_absorb < 10:
            self.current_absorb = 0
                        
    def calc_moreshit(self, avg_pws, target_guid):
        # argent garbage
        # check if 
        c = (self.last_dmg + self.new_absorb)*.15
        print('========== WOTN I GUESS? ===========')
        print(self.current_absorb)
        print(c)
        print(avg_pws*0.9)
        # if avg_pws*0.9 < self.current_absorb - c < avg_pws*1.1:
        if self.is_dk and avg_pws*1.1 < self.current_absorb - c:
            print('========== WOTN CALCED ===========')
            spell_name = 'Will of the Necropolis'
            self.add_absorb(target_guid, spell_name, c)
            self.current_absorb = self.current_absorb - c
        
    def calc_else(self, removed_auras, target_guid):
        if len(removed_auras) == 1:
            spell_name, source_guid = removed_auras.popitem()
            self.current_auras[spell_name].pop(source_guid)
            l = len(self.pws) or 1
            avg_pws = sum(self.pws) / l
            print('AVG PWS:', avg_pws)
            if avg_pws and self.current_absorb > avg_pws * 1.2:
                self.calc_moreshit(avg_pws, target_guid)
            self.add_absorb(source_guid, spell_name, self.current_absorb)
            if spell_name == 'Power Word: Shield':
                self.pws.append(self.current_absorb)
                print('added', self.current_absorb)
            self.current_absorb = 0
        elif len(removed_auras) > 1:
            print("!!!!! len(removed_auras) > 1")
            print(removed_auras)

    def calc_new_absorb(self, flag, other):
        self.last_dmg = self.new_absorb = 0
        if 'ABSORB' in other:
            self.new_absorb = other[-1]
        elif flag in SPELL_DMG_FLAGS and other[8] != '0': 
            self.last_dmg, self.new_absorb = other[3], other[8]
        elif flag == 'SWING_DAMAGE' and other[5] != '0':
            self.last_dmg, self.new_absorb = other[0], other[5]
        self.last_dmg = int(self.last_dmg)
        self.new_absorb = int(self.new_absorb)
        self.full_new_absorb = int(self.new_absorb)

    def get_removed_auras(self, logs, filter_guid):
        removed_auras = []
        for line in logs:
            if filter_guid in line:
                timestamp, flag, source_guid, source_name, target_guid, _, *other = line.split(',')
                if (target_guid == filter_guid
                and flag == 'SPELL_AURA_REMOVED'
                and other[0] in AURAS_ID):
                    print(timestamp, 'SPELL_AURA_REMOVED', source_name, other[1])
                    removed_auras.append((other[1], source_guid))
        return removed_auras

    def deal_with_removed_auras(self, removed_auras, target_guid):
        print('REMOVED AURAS:', removed_auras)
        removed_auras = dict(removed_auras)
        for s in ['Divine Aegis', 'Protection of Ancient Kings']:
            self.calc_sure_shield(removed_auras, s)
        if self.current_absorb > 0 and removed_auras:
            self.calc_else(removed_auras, target_guid)
        self.current_auras = {k:v for k,v in self.current_auras.items() if v}

    def lookback(self, logs, target_guid):
        # 6/18 23:01:25.440,SPELL_HEAL,0x06000000003DC2AD,Canoobis,0xF1300079F0000D13,Mirror Image,54968,Glyph of Holy Light,0x2,4033,3433,0,nil
        # check if same second
        # 6/18 23:01:25.409,SPELL_DAMAGE,0x0600000000417AFF,Balkanretard,0xF130008FF5000CE8,Sindragosa,53739,Seal of Corruption,0x2,426,0,2,106,0,0,nil,nil,nil
        hp = 0
        for line in reversed(logs):
            if target_guid in line:
                line = line.split(',')
                if line[4] == target_guid:
                    flag = line[1]
                    if flag in HEALS:
                        hp += int(line[9])
                        if line[10] != "0":
                            hp -= int(line[10])
                            return hp
                    elif flag in SPELL_DMG_FLAGS:
                        hp -= int(line[9])
                    elif flag == 'SWING_DAMAGE':
                        hp -= int(line[6])
        print("=============== SHOULDNT REACH HERE ====================")
        return hp

    def wotn(self, guid):
        # maybe damageshield?
        # check back for heal dmg till overheal >0
        t = self.new_absorb + self.last_dmg
        wotn = t * .15
        
        if wotn <= self.new_absorb *1.01:
            spell_name = 'Will of the Necropolis'
            if self.new_absorb * 0.99 <= wotn:
                print('========== WOTN FOR SURE ===========')
                self.add_absorb(guid, spell_name, wotn)
                self.current_absorb = 0
                return
            elif 'Divine Aegis' not in self.current_auras or 'Protection of Ancient Kings' not in self.current_auras:
                print('========== WOTN FOR SURE ===========')
                self.add_absorb(guid, spell_name, wotn)
                self.current_absorb -= wotn
                if self.current_absorb < 10:
                    self.current_absorb = 0
                return
            print('========== MAYBE WOTN? ===========')

    def sd(self, flag: str, guid):
        # maybe damageshield?
        if self.new_absorb and flag.startswith("SPELL"):
            ttl_dmg = self.new_absorb + self.last_dmg
            sd = ttl_dmg * .45
            print('========== CALC SD? ===========')
            print(ttl_dmg)
            print(sd)
            if sd <= self.new_absorb * 1.01:
                if self.new_absorb * 0.99 <= sd or self.new_absorb > 20000:
                    print('========== SD FOR SURE ===========')
                    spell_name = 'Spell Deflection'
                    self.add_absorb(guid, spell_name, sd)
                    self.current_absorb -= sd
                    if self.current_absorb < 10:
                        self.current_absorb = 0
                print('========== MAYBE SD? ===========')

    def main_gen(self):
        line: str
        for n, line in enumerate(self.logs):
            if self.guid in line:
                line = line.split(',')
                if line[4] == self.guid:
                    yield n, line
    
    def main(self):  # sourcery no-metrics skip: merge-nested-ifs
        for n, line in self.main_gen():
            timestamp, flag, source_guid, _, target_guid, _, *other = line
            if self.is_dk and 'Anti-Magic Shell' in other and flag == 'SPELL_AURA_REMOVED':
                self.top_shield_removed(target_guid, other[1])
            elif 'Hand of Sacrifice' in other and flag == 'SPELL_AURA_REMOVED':
                self.top_shield_removed(source_guid, other[1])
            elif flag in AURA_FLAG and 'BUFF' in line:
                spell_id = other[0]
                if spell_id in ABSORB_SPELL_IDS:
                    self.aura_applied(other[1], source_guid)
                elif spell_id in SHIELDS_SPELL_IDS:
                    l_h = self.get_last_heal(n, timestamp, source_guid, target_guid)
                    self.aura_applied_by_heal(l_h, source_guid, spell_id, other[1])
            else:
                self.calc_new_absorb(flag, other)
                if self.new_absorb:
                    print(f'NEW ABSORB: {self.new_absorb:>6}   {timestamp} {flag:<20} {line[6:]}')
                    print(self.current_auras)
                    if self.is_dk and 'Anti-Magic Shell' in self.current_auras and 'SPELL' in flag:
                        self.calc_ams(target_guid)
                    if 'Hand of Sacrifice' in self.current_auras:
                        self.calc_hos()
                    self.current_absorb += self.new_absorb
                    if self.is_dk:
                        self.sd(flag, target_guid)

                    removed_auras = self.get_removed_auras(self.logs[n-20:n], target_guid)
                    if removed_auras:
                        self.deal_with_removed_auras(removed_auras, target_guid)
                    print(f'CURRENT ABS: {self.current_absorb:>6}')
                    if self.is_dk or self.is_pal:
                        hp = self.lookback(logs[:n+1], target_guid)
                        print(f'CURRENT  HP: {hp:>6}')
                        print('CURRENT DMG:', self.new_absorb + self.last_dmg)
                        if self.new_absorb + self.last_dmg > 30000 or not self.current_auras and hp < -20000:
                            self.wotn(target_guid)
                        if not self.current_auras and self.current_absorb > 0:
                            if flag == 'SPELL_DAMAGE':# and dk:
                                spell_name = 'Spell Deflection'
                                self.add_absorb(target_guid, spell_name, self.current_absorb)
                                self.current_absorb = 0
                    # if swing and dk = will of necro
                    print(self.current_auras)
                    print()

        return self.absorbs




name = '210618-Illusion'
name = '21-07-22--21-30--Inia'
# name = '210625-Illusion'
LOGS = _main.THE_LOGS(name)
logs = LOGS.get_logs()
enc_data = LOGS.get_enc_data()
class_data = LOGS.get_classes()
guids, players = LOGS.get_guids()
s,f = enc_data['the_lich_king'][-1]
# logs = logs[s-1500:s+(f-s)//2]
# logs = logs[s-1500:f]
# logs = logs[s:f]
filter_guid = '0x06000000004C3CEB'
filter_guid = '0x0600000000422CEB'
p = players[filter_guid]
char_class = class_data[p]
w = FUCKINGBULLSHIT(logs, filter_guid, char_class)
d = w.main()
for guid, spells in d.items():
    print(f'{guids[guid]["name"]:<12} {spells}')