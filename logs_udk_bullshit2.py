from typing import Dict, List, Set
import constants

def checkdks(logs: List[str]):
    # 50526 = Wandering Plague
    return {
        line.split(',')[2]
        for line in logs
        if '50526' in line and '0x20' in line and 'SPELL_' in line
    }

def same_guid_ids(pets: Set[str], missing_pets: Set[str]):
    if len(pets) != len(missing_pets):
        return False
    pets = {x[6:12] for x in pets}
    missing_pets = {x[6:12] for x in missing_pets}
    return pets == missing_pets

def missing_targets_f(data):
    return {y for x in data.values() for y in x}
    
def sort_by_target(data: Dict[str, Set[str]]):
    new: Dict[str, Set[str]] = {}
    for guid, targets in data.items():
        for tguid in targets:
            new.setdefault(tguid, set()).add(guid)
    return new


class UDK_BULLSHIT:
    def __init__(self, logs, everything, enc_data, pets_data, unholy_DK_pets) -> None:
        self.logs = logs
        self.everything = everything
        self.enc_data = enc_data
        self.pets_data = pets_data
        self.unholy_DK_pets = unholy_DK_pets
        #self.missing_targets: Dict[str, Set[str]] = missing_targets

    def pet_owners(self, pets) -> Dict[str, str]:
        d = {}
        for guid in pets:
            master = self.everything[guid].get('master_guid')
            if master:
                d[guid] = master
        return d

    def get_boss_data(self, tguid):
        target_name = self.everything[tguid]['name']
        return self.enc_data.get(target_name)

    def find_solo_dk(self, boss_data):
        for s, f in boss_data:
            logs_slice = self.logs[s:f]
            dks = checkdks(logs_slice)
            if len(dks) != 1:
                continue
            return dks.pop()
        
    def update_dk_pet_owners(self, dk_guid, pet_guid):
        dk_name = self.everything[dk_guid]['name']
        p = {'name': 'Ghoul', 'master_name': dk_name, 'master_guid': dk_guid}
        guid_id = pet_guid[6:12]

        for guid in self.everything:
            if guid_id not in guid:
                continue
            self.everything[guid] = p
            # print('Updated owner:', guid)
    
    def remove_parsed_pets(self, pets):
        for tguid, missing_pets in dict(self.missing_targets).items():
            if same_guid_ids(pets, missing_pets):
                del self.missing_targets[tguid]

    def filter_pets_by_combat(self):
        for tguid, pets in self.missing_targets.items():
            if not pets:
                continue

            boss_data = self.get_boss_data(tguid)
            if not boss_data:
                continue

            if len(pets) == 1:
                dk_guid = self.find_solo_dk(boss_data)
                if not dk_guid:
                    continue
                pet_guid = list(pets)[0]
                self.update_dk_pet_owners(dk_guid, pet_guid)
                self.remove_parsed_pets(pets)
                return
            
            owners = self.pet_owners(pets)
            remaining_pets = pets - set(owners)
            if len(remaining_pets) != 1:
                continue
            for s, f in boss_data:
                logs_slice = self.logs[s:f]
                dks = checkdks(logs_slice) - set(owners.values())
                if len(dks) != 1:
                    continue
                dk_guid = dks.pop()
                pet_guid = remaining_pets.pop()
                self.update_dk_pet_owners(dk_guid, pet_guid)
                self.remove_parsed_pets(pets)
                return


    def missing_dk_pets(self):
        return {
            guid: v
            for guid, v in self.unholy_DK_pets.items()
            if guid not in self.pets_data
        }

    def get_missing_targets(self):
        missing = self.missing_dk_pets()
        missing_targets = missing_targets_f(missing)
        targets = sort_by_target(self.unholy_DK_pets)
        targets = {
            tguid: attackers
            for tguid, attackers in targets.items()
            if tguid in missing_targets and self.get_boss_data(tguid)
        }
        # return targets
        self.missing_targets = targets