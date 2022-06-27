from os import abort
import constants
import logs_main

# use classes instead of dict

ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SWING_MISSED', 'SPELL_MISSED'}
ABSORB_FLAGS = {'SPELL_PERIODIC_MISSED', 'RANGE_MISSED', 'SPELL_MISSED'}
DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD', 'SWING_DAMAGE'}
AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH', 'SPELL_AURA_REMOVED'}
AURAS_NAME = {'Protection of Ancient Kings', 'Power Word: Shield', 'Divine Aegis', 'Sacred Shield', 'Hardened Skin', 'Anti-Magic Shell', 'Savage Defense'}
AURAS_ID = {'64413', '48066', '47753', '58597', '48707', '55233'}

SS = {'64413', '47753'}

def rrrrrr(logs, guid):
    for line in logs:
        if '0x06000000004C3CEB' in line:
            line = line.split(',')
            if line[4] == '0x06000000004C3CEB' and 'HEAL' in line[1] and line[2] == guid:
                return f"{line[0]} ++ {line[1]:<25} {line[3]:>20} {line[7]:>30}  {line[6]:>7}  {line[9]:>8}"

def zprint(m, timestamp, flag, source_name, arg1, arg2, arg3="", arg4="", arg5=""):
    print(f"{timestamp:<19}{flag:<25}{source_name:>20}{arg1:>30}{arg2:>8}{m:>4}{arg3:>8}{arg4:>8}{arg5:>8}")

def mmm(logs):
    zprint('T', 'TIMESTAMP', 'FLAG', 'SOURCE', 'SPELL', 'ID', 'VALUE', 'RES/OH', 'ABSORB')
    for line in logs:
        # if '0x060000000040F817' in line:
        if '0x06000000004C3CEB' in line:
            line = line.split(',')
            timestamp, flag, _, source_name, target_guid, _, *other = line
            if target_guid == '0x06000000004C3CEB':
                # if 'HEAL' in flag and other[3]!=other[4]:
                if 'HEAL' in flag:
                    zprint('++', timestamp, flag, source_name, other[1], other[0], other[3], other[4])
                elif flag in ABSORB_FLAGS:
                # elif 'ABSORB' in line:
                    zprint('00', timestamp, flag, source_name, other[1], other[0], '0', '0', line[-1])
                elif flag == 'SWING_MISSED':
                    zprint('--', timestamp, flag, source_name, 'MELEE', '-----', other[0])
                elif flag in DMG_FLAGS:
                    if other[8] != '0':
                        zprint('--', timestamp, flag, source_name, other[1], other[0], other[3], other[6], other[8])
                elif flag == 'SWING_DAMAGE':
                    if other[5] != '0':
                        zprint('--', timestamp, flag, source_name, 'MELEE', '-----', other[0], other[3], other[5])
                elif flag in AURA_FLAG and 'BUFF' in line:# and other[0] in AURAS_ID:
                    # if flag != 'SPELL_AURA_REMOVED' and other[0] in SS:
                    #     z = reversed(logs[:n])
                    #     print(rrrrrr(z, line[2]))
                    m = 'RR' if flag == 'SPELL_AURA_REMOVED' else 'OO'
                    zprint(m, timestamp, flag, source_name, other[1], other[0])


def rrrrrr(logs, source_guid, target_guid):
    for line in logs:
        if target_guid in line:
            line = line.split(',')
            if line[2] == source_guid and line[4] == target_guid and 'HEAL' in line[1]:
                return line[9]

AURAS_ID = {'64413', '48066', '47753', '58597', '55233'}
def gggggg(logs, target_guid):
    z = []
    for line in logs:
        if target_guid in line:
            line = line.split(',')
            if     (line[4] == target_guid
                and line[1] == 'SPELL_AURA_REMOVED'
                and line[6] in AURAS_ID):
                print(line[0], 'SPELL_AURA_REMOVED', line[3], line[7])
                z.append((line[7], line[2]))
    return z

FFF = {'Sacred Shield', 'Power Word: Shield', 'Anti-Magic Shell'}

def added_print(absorb, spell_name, source):
    print(f'ADDED: {absorb:>5} | {spell_name:>30} | {source}')

AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH'}
ABSORB_SPELL_IDS = {'58597', '48066', '48707', '6940'}
SHIELDS_SPELL_IDS = {'64413', '47753'}
SPELL_DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}


@constants.running_time
def main(logs):  # sourcery no-metrics
    absorb = 0
    THE_D = {}
    t = {}
    AURA_FLAG = {'SPELL_AURA_APPLIED', 'SPELL_AURA_REFRESH'}
    ABSORB_SPELL_IDS = {'58597', '48066', '48707', '6940'}
    SHIELDS_SPELL_IDS = {'64413', '47753'}
    SPELL_DMG_FLAGS = {'SPELL_PERIODIC_DAMAGE', 'SPELL_DAMAGE', 'RANGE_DAMAGE', 'DAMAGE_SHIELD'}

    for n, line in enumerate(logs):
        if '0x06000000004C3CEB' in line:
            line = line.split(',')
            timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line
            if target_guid == '0x06000000004C3CEB':
                if 'Anti-Magic Shell' in other and flag == 'SPELL_AURA_REMOVED':
                    spell_name = 'Anti-Magic Shell'
                    t[spell_name].pop(target_guid)
                    if not t[spell_name]:
                        t.pop(spell_name)
                    print(f'REMOVED: {spell_name:>20} FROM {target_name}')
                    print()
                elif 'Hand of Sacrifice' in other and flag == 'SPELL_AURA_REMOVED':
                    spell_name = 'Hand of Sacrifice'
                    t[spell_name].pop(source_guid)
                    if not t[spell_name]:
                        t.pop(spell_name)
                    print(f'REMOVED: {spell_name:>20} FROM {source_name}')
                    print()
                elif flag in AURA_FLAG and 'BUFF' in line:
                    spell_id = other[0]
                    if spell_id in ABSORB_SPELL_IDS:
                        t[other[1]] = {source_guid: True}
                    elif spell_id in SHIELDS_SPELL_IDS:
                        l_h = rrrrrr(reversed(logs[:n]), source_guid, target_guid)
                        q = t.setdefault(other[1], {}) #.setdefault(target_guid, {})
                        mult = 0.3 if spell_id == "47753" else 0.15
                        _shield = int(int(l_h)*mult)
                        q[source_guid] = q.get(source_guid, 0) + _shield
                        print(f'ADDED SHIELD: {_shield:>6}  {other[1]}')
                        print()
                else:
                    new_absorb = None
                    dmg = 0
                    if 'ABSORB' in other:
                        new_absorb = line[-1]
                    elif flag in SPELL_DMG_FLAGS and other[8] != '0': 
                        dmg, new_absorb = other[3], other[8]
                    elif flag == 'SWING_DAMAGE' and other[5] != '0':
                        dmg, new_absorb = other[0], other[5]
                    if new_absorb:
                        print(t)
                        new_absorb = int(new_absorb)
                        if 'Anti-Magic Shell' in t and 'SPELL' in flag:
                            spell_name = 'Anti-Magic Shell'
                            ams = (new_absorb + int(dmg)) // 4 * 3
                            new_absorb -= ams
                            j = THE_D.setdefault(target_guid, {})
                            j[spell_name] = j.get(spell_name, 0) + ams
                            added_print(ams, spell_name, target_guid)
                        if 'Hand of Sacrifice' in t:
                            spell_name = 'Hand of Sacrifice'
                            hos = (new_absorb + int(dmg)) // 10 * 3
                            new_absorb -= hos
                            j = THE_D.setdefault(source_guid, {})
                            j[spell_name] = j.get(spell_name, 0) + hos
                            added_print(hos, spell_name, source_guid)
                        absorb += new_absorb
                        print(f'NEW ABSORB: {absorb:>6}    {timestamp} {flag:<20} {line[6:]}')
                        removed_auras = gggggg(logs[n-20:n], target_guid)
                        print('REMOVED AURAS:', removed_auras)
                        removed_auras = dict(removed_auras)
                        if 'Divine Aegis' in removed_auras:
                            spell_name = 'Divine Aegis'
                            _src_guid = removed_auras.pop(spell_name)
                            try:
                                da = t[spell_name].pop(_src_guid)
                                j = THE_D.setdefault(_src_guid, {})
                                j[spell_name] = j.get(spell_name, 0) + da
                                added_print(da, spell_name, _src_guid)
                                absorb -= da
                            except KeyError:
                                print('==========================WTF==========================')
                        if 'Protection of Ancient Kings' in removed_auras:
                            spell_name = 'Protection of Ancient Kings'
                            _src_guid = removed_auras.pop(spell_name)
                            try:
                                poak = t[spell_name].pop(_src_guid)
                                j = THE_D.setdefault(_src_guid, {})
                                j[spell_name] = j.get(spell_name, 0) + poak
                                added_print(poak, spell_name, _src_guid)
                                absorb -= poak
                            except KeyError:
                                print('==========================WTF==========================')
                        if absorb > 0 and removed_auras:
                            if len(removed_auras) == 1:
                                spell_name, _src_guid = removed_auras.popitem()
                                t[spell_name].pop(_src_guid)
                                j = THE_D.setdefault(_src_guid, {})
                                j[spell_name] = j.get(spell_name, 0) + absorb
                                added_print(absorb, spell_name, _src_guid)
                                absorb = 0
                            elif len(removed_auras) > 1:
                                print("!!!!! len(removed_auras) > 1")
                                print(removed_auras)
                        t = {k:v for k,v in t.items() if v}
                        if not t and absorb > 0:
                            if flag == 'SPELL_DAMAGE':# and dk:
                                spell_name = 'Spell Deflection'
                                j = THE_D.setdefault(target_guid, {})
                                j[spell_name] = j.get(spell_name, 0) + absorb
                                added_print(absorb, spell_name, target_guid)
                                absorb = 0
                        print(t)
                        print()
                        # z = dict(t)
                        # t = {}
                        # for spell_name, sources in z.items():
                        #     for guid, v in sources.items():
                        #         if v:
                        #             t.setdefault(spell_name, {})[guid] = v

    return THE_D

class FUCKINGBULLSHIT:
    def __init__(self, logs_slice, guid) -> None:
        self.logs = logs_slice
        self.guid = guid
        self.current_absorb = 0
        self.buffs = {}
        self.absorbs = {}
        self.current_auras = ['REMOVED', 'APPLIED']

    def zzprint(self, is_applied, spell_name, source, amount=""):
        print(f'AURA {self.current_auras[is_applied]}: {spell_name:>20} FROM {source:>12}{amount:>6}\n')

    def ams_removed(self, target_guid):
        spell_name = 'Anti-Magic Shell'
        self.buffs[spell_name].pop(target_guid)
        if not self.buffs[spell_name]:
            self.buffs.pop(spell_name)
        self.zzprint(False, spell_name, target_guid)

    def hos_removed(self, source_guid):
        spell_name = 'Hand of Sacrifice'
        self.buffs[spell_name].pop(source_guid)
        if not self.buffs[spell_name]:
            self.buffs.pop(spell_name)
        self.zzprint(False, spell_name, source_guid)

    def aura_applied(self, spell_name, source_guid):
        self.buffs[spell_name] = {source_guid: True}

    def aura_applied_by_heal(self, n, source_guid, target_guid, spell_id, spell_name):
        l_h = rrrrrr(reversed(self.logs[:n]), source_guid, target_guid)
        mult = 0.3 if spell_id == "47753" else 0.15
        _shield = int(int(l_h)*mult)
        q = self.buffs.setdefault(spell_name, {})
        q[source_guid] = q.get(source_guid, 0) + _shield
        self.zzprint(False, spell_name, source_guid)
        print(f'ADDED SHIELD: {_shield:>6}  {spell_name}')
        print()

    def add_absorb(self, guid, spell_name, value):
        j = self.absorbs.setdefault(guid, {})
        j[spell_name] = j.get(spell_name, 0) + value
        added_print(value, spell_name, guid)


    def calc_ams(self, target_guid):
        spell_name = 'Anti-Magic Shell'
        ams = (self.new_absorb + self.last_dmg) // 4 * 3
        self.add_absorb(target_guid, spell_name, ams)
        self.new_absorb -= ams

    def calc_hos(self, source_guid):
        spell_name = 'Hand of Sacrifice'
        hos = (self.new_absorb + self.last_dmg) // 10 * 3
        self.add_absorb(source_guid, spell_name, hos)
        self.new_absorb -= hos

    def calc_da(self, removed_auras):
        spell_name = 'Divine Aegis'
        source_guid = removed_auras.pop(spell_name)
        try:
            da = self.current_auras[spell_name].pop(source_guid)
            self.add_absorb(source_guid, spell_name, da)
            self.current_absorb -= da
        except KeyError:
            print('==========================WTF==========================')
                        

    def calc_poak(self, removed_auras):
        spell_name = 'Protection of Ancient Kings'
        source_guid = removed_auras.pop(spell_name)
        try:
            poak = self.current_auras[spell_name].pop(source_guid)
            self.add_absorb(source_guid, spell_name, poak)
            self.current_absorb -= poak
        except KeyError:
            print('==========================WTF==========================')
                        

    def calc_else(self, removed_auras):
        if len(removed_auras) == 1:
            spell_name, source_guid = removed_auras.popitem()
            self.current_auras[spell_name].pop(source_guid)
            self.add_absorb(source_guid, spell_name, self.current_absorb)
            self.current_absorb = 0
        elif len(removed_auras) > 1:
            print("!!!!! len(removed_auras) > 1")
            print(removed_auras)

    def calc_new_absorb(self, flag, other):
        self.new_absorb = self.last_dmg = 0
        if 'ABSORB' in other:
            self.new_absorb = other[-1]
        elif flag in SPELL_DMG_FLAGS and other[8] != '0': 
            self.last_dmg, self.new_absorb = other[3], other[8]
        elif flag == 'SWING_DAMAGE' and other[5] != '0':
            self.last_dmg, self.new_absorb = other[0], other[5]
        self.last_dmg = int(self.last_dmg)
        self.new_absorb = int(self.new_absorb)

    def get_removed_auras(self, logs, filter_guid):
        removed_auras = []
        for line in logs:
            if filter_guid in line:
                timestamp, flag, source_guid, source_name, target_guid, _, spell_id, spell_name, *_ = line.split(',')
                if (target_guid == filter_guid
                and flag == 'SPELL_AURA_REMOVED'
                and spell_id in AURAS_ID):
                    print(timestamp, 'SPELL_AURA_REMOVED', source_name, spell_name)
                    removed_auras.append((spell_name, source_guid))
        return removed_auras

    def main(self):
        for n, line in enumerate(self.logs):
            if '0x06000000004C3CEB' in line:
                line = line.split(',')
                timestamp, flag, source_guid, source_name, target_guid, target_name, *other = line
                if target_guid == '0x06000000004C3CEB':
                    if 'Anti-Magic Shell' in other and flag == 'SPELL_AURA_REMOVED':
                        self.ams_removed()
                    elif 'Hand of Sacrifice' in other and flag == 'SPELL_AURA_REMOVED':
                        self.hos_removed()
                # tab this
                elif flag in AURA_FLAG and 'BUFF' in line:
                    spell_id = other[0]
                    if spell_id in ABSORB_SPELL_IDS:
                        self.aura_applied(other[1], source_guid)
                    elif spell_id in SHIELDS_SPELL_IDS:
                        self.aura_applied_by_heal(n, source_guid, target_guid, spell_id, other[1])
                else:
                    # self.absorbs
                    self.calc_new_absorb()
                    if self.new_absorb:
                        print(self.absorbs)
                        if 'Anti-Magic Shell' in self.current_auras and 'SPELL' in flag:
                            self.calc_ams()
                        if 'Hand of Sacrifice' in self.current_auras:
                            self.calc_hos()
                        self.current_absorb += self.new_absorb
                        print(f'NEW ABSORB: {self.current_absorb:>6}    {timestamp} {flag:<20} {line[6:]}')
                        removed_auras = self.get_removed_auras(self.logs[n-20:n], target_guid)
                        print('REMOVED AURAS:', removed_auras)
                        removed_auras = dict(removed_auras)
                        if 'Divine Aegis' in removed_auras:
                            self.calc_da(removed_auras)
                        if 'Protection of Ancient Kings' in removed_auras:
                            self.calc_poak(removed_auras)
                        if self.current_absorb > 0 and removed_auras:
                            self.calc_else(removed_auras)
                        self.current_auras = {k:v for k,v in self.current_auras.items() if v}
                        if not self.current_auras and self.current_absorb > 0:
                            if flag == 'SPELL_DAMAGE':# and dk:
                                spell_name = 'Spell Deflection'
                                self.add_absorb(target_guid, spell_name, self.current_absorb)
                                self.current_absorb = 0
                        print(self.current_auras)
                        print()

        return self.absorbs

name = '210618-Illusion'
LOGS = logs_main.THE_LOGS(name)
logs = LOGS.get_logs()
enc_data = LOGS.get_enc_data()
guids, players = LOGS.get_guids()
s,f = enc_data['sindragosa'][-1]
logs = logs[s-1500:s+(f-s)]
d = main(logs)
for guid, spells in d.items():
    print(f'{guids[guid]["name"]:<12} {spells}')