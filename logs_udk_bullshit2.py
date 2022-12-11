from collections import defaultdict

def same_guid_ids(pets: set[str], missing_pets: set[str]):
    if len(pets) != len(missing_pets):
        return False
    pets = {x[6:-6] for x in pets}
    missing_pets = {x[6:-6] for x in missing_pets}
    return pets == missing_pets

def missing_targets_f(data):
    return {y for x in data.values() for y in x}
    
def sort_by_target(data: dict[str, set[str]]):
    new: dict[str, set[str]]
    new = defaultdict(set)
    for guid, targets in data.items():
        for tguid in targets:
            new[tguid].add(guid)
    return new

def get_missing_targets(missing_pets, pets_data):
    # print('get_missing_targets call')
    missing = {
        guid: v
        for guid, v in missing_pets.items()
        if guid not in pets_data
    }
    # print('missing', missing)
    missing_targets = missing_targets_f(missing)
    # print('missing_targets', missing_targets)
    targets = sort_by_target(missing_pets)
    # print('targets', targets)
    targets = {
        tguid: attackers
        for tguid, attackers in targets.items()
        if tguid in missing_targets
    }
    return targets

class UDK_BULLSHIT:
    def __init__(self,
    logs: list[str],
    everything: dict[str, dict[str, str]],
    enc_data: dict[str, list],
    targets: dict[str, set[str]]
    ) -> None:
        self.logs = logs
        self.everything = everything
        self.enc_data = enc_data
        self.missing_targets = targets
        self.filter_loop()

    def get_boss_segments(self, tguid):
        target_name = self.everything[tguid]['name']
        return self.enc_data.get(target_name)

    def get_all_dks_in_segment(self, s, f):
        # 50526 = Wandering Plague
        logs_slice = self.logs[s:f]
        return {
            line.split(',', 3)[2]
            for line in logs_slice
            if '50526' in line and '0x20' in line and 'SPELL_DAMAGE' in line
        }

    def find_solo_dk(self, boss_data: list[tuple[int, int]]):
        for s, f in boss_data:
            dks = self.get_all_dks_in_segment(s, f)
            if len(dks) != 1:
                continue
            return dks.pop()

    def pet_owners(self, pets):
        d = {}
        for guid in pets:
            master = self.everything[guid].get('master_guid')
            if master:
                d[guid] = master
        return set(d), set(d.values())


    def filter_pets_by_combat(self):
        for tGUID, pets_attacking in self.missing_targets.items():
            if not pets_attacking:
                continue

            boss_segments = self.get_boss_segments(tGUID)
            if not boss_segments:
                continue

            if len(pets_attacking) == 1:
                dk_guid = self.find_solo_dk(boss_segments)
                if dk_guid:
                    pet_guid = list(pets_attacking)[0]
                    return pets_attacking, dk_guid, pet_guid
            
            _pets, masters = self.pet_owners(pets_attacking)
            remaining_pets = pets_attacking - _pets
            if len(remaining_pets) != 1:
                continue
            pet_guid = remaining_pets.pop()
            for s, f in boss_segments:
                dks = self.get_all_dks_in_segment(s, f) - masters
                if len(dks) == 1:
                    dk_guid = dks.pop()
                    return pets_attacking, dk_guid, pet_guid
        
    def update_dk_pet_owners(self, dk_guid, pet_guid):
        dk_name = self.everything[dk_guid]['name']
        p = {'name': 'Ghoul', 'master_name': dk_name, 'master_guid': dk_guid}
        guid_id = pet_guid[6:-6]

        for guid in self.everything:
            if guid_id not in guid:
                continue
            self.everything[guid] = p
            # print('Updated owner:', guid)
    
    def remove_parsed_pets(self, pets):
        for tguid, missing_pets in dict(self.missing_targets).items():
            if same_guid_ids(pets, missing_pets):
                del self.missing_targets[tguid]
    
    def do_filter(self):
        returned = self.filter_pets_by_combat()
        if returned:
            pets, dk_guid, pet_guid = returned
            self.update_dk_pet_owners(dk_guid, pet_guid)
            self.remove_parsed_pets(pets)

    def filter_loop(self):
        for n in range(1,6):
            print('filter_pets_by_combat Loop:', n)
            missing_targets_cached = dict(self.missing_targets)
            self.do_filter()
            if self.missing_targets == missing_targets_cached:
                break

FELHUNTER_SPELLS = {
    '19647': 'Spell Lock',
    '19658': 'Devour Magic Effect',
    '48011': 'Devour Magic',
    '54053': 'Shadow Bite',
    '54425': 'Improved Felhunter',
    '57567': 'Fel Intelligence'
}

class PET_BULLSHIT_AFFLI:
    def __init__(self,
        logs: list[str],
        everything: dict[str, dict[str, str]],
        enc_data: dict[str, list],
        targets: dict[str, set[str]]
    ) -> None:
        self.logs = logs
        self.everything = everything
        self.enc_data = enc_data
        self.missing_targets = targets
        self.filter_loop()

    def get_boss_segments(self, tguid):
        target_name = self.everything[tguid]['name']
        return self.enc_data.get(target_name)

    def get_all_owners_in_segment(self, s, f):
        # 54053,"Shadow Bite     
        # 11/19 19:39:01.278  SPELL_DAMAGE,0xF140044FA2000009,"Phuudhum",0x1112,0xF1500087EC0000E9,"Gormok the Impaler",0x10a48,54053,"Shadow Bite",0x20,945,0,32,105,0,0,nil,nil,nil
        logs_slice = self.logs[s:f]
        return {
            line.split(',', 3)[2]
            for line in logs_slice
            if '54053' in line and '0x20' in line and 'SPELL_DAMAGE' in line
        }

    def find_solo_owner(self, boss_data: list[tuple[int, int]]):
        for s, f in boss_data:
            owners = self.get_all_owners_in_segment(s, f)
            if len(owners) != 1:
                continue
            return owners.pop()

    def pet_owners(self, pets):
        d = {}
        for guid in pets:
            master = self.everything[guid].get('master_guid')
            if master:
                d[guid] = master
        return set(d), set(d.values())


    def filter_pets_by_combat(self):
        for tGUID, pets_attacking in self.missing_targets.items():
            if not pets_attacking:
                continue

            boss_segments = self.get_boss_segments(tGUID)
            if not boss_segments:
                continue

            if len(pets_attacking) == 1:
                owner_guid = self.find_solo_owner(boss_segments)
                if owner_guid:
                    pet_guid = list(pets_attacking)[0]
                    return pets_attacking, owner_guid, pet_guid
            
            _pets, masters = self.pet_owners(pets_attacking)
            remaining_pets = pets_attacking - _pets
            if len(remaining_pets) != 1:
                continue
            pet_guid = remaining_pets.pop()
            for s, f in boss_segments:
                owners = self.get_all_owners_in_segment(s, f) - masters
                if len(owners) == 1:
                    owner_guid = owners.pop()
                    return pets_attacking, owner_guid, pet_guid
        
    def update_pet_owners(self, owner_guid, pet_guid):
        owner_name = self.everything[owner_guid]['name']
        p = {'name': 'Felhunter', 'master_name': owner_name, 'master_guid': owner_guid}
        guid_id = pet_guid[6:-6]

        for guid in self.everything:
            if guid_id not in guid:
                continue
            self.everything[guid] = p
    
    def remove_parsed_pets(self, pets):
        for tguid, missing_pets in dict(self.missing_targets).items():
            if same_guid_ids(pets, missing_pets):
                del self.missing_targets[tguid]
    
    def do_filter(self):
        returned = self.filter_pets_by_combat()
        if returned:
            pets, owner_guid, pet_guid = returned
            self.update_pet_owners(owner_guid, pet_guid)
            self.remove_parsed_pets(pets)

    def filter_loop(self):
        for n in range(1,6):
            print('filter_pets_by_combat Loop:', n)
            missing_targets_cached = dict(self.missing_targets)
            self.do_filter()
            if self.missing_targets == missing_targets_cached:
                break
