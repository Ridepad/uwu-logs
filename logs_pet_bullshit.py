from collections import defaultdict
from c_bosses import convert_to_fight_name

SPELLS = {
    "Felhunter": {
        '19647': 'Spell Lock',
        '19658': 'Devour Magic Effect',
        '48011': 'Devour Magic',
        '54053': 'Shadow Bite',
        '54425': 'Improved Felhunter',
        '57567': 'Fel Intelligence'
    },
    "Ghoul": {
        '47468': 'Claw',
        '47481': 'Gnaw',
        '47482': 'Leap'
    }
}

def sdjfsiodjfsdiojfio(owners1, owners2, pets1, pets2):
    owners_diff = owners1 - owners2
    print()
    print(owners_diff)
    if len(owners_diff) == 1:
        pets_diff = pets1 - pets2
        print(pets_diff)
        if len(pets_diff) == 1:
            return owners_diff.pop(), pets_diff.pop()

def check_negative(data):
    for i, (owners1, pets1) in enumerate(data, 1):
        for owners2, pets2 in data[i:]:
            if owners1 == owners2 or pets1 == pets2:
                continue
            q = sdjfsiodjfsdiojfio(owners1, owners2, pets1, pets2)
            if q:
                yield q

            q = sdjfsiodjfsdiojfio(owners2, owners1, pets2, pets1)
            if q:
                yield q

class PET_BULLSHIT:
    def __init__(self, logs: list[str], enc_data: dict[str, list], data: dict, player_spec: str) -> None:
        if player_spec == "Unholy":
            self.spec_spell_id = "50526"
            self.pet_name = "Ghoul"
        elif player_spec == "Affliction":
            self.spec_spell_id = "59164"
            self.pet_name = "Felhunter"
        else:
            return
        
        self.logs = logs
        self.enc_data = enc_data
        self.everything: dict[str, dict[str, str]] = data["everything"]
        self.missing_owner: list[str] = data["missing_owner"]
        self.pet_spell_ids = SPELLS[self.pet_name]
        self.spec_pets: defaultdict[str, set[str]] = data[self.pet_name]
        self.pet_by_target = self.combine_pet_by_target()
        self.pet_data = self.get_pet_data()
        self.filter_loop()

    def combine_pet_by_target(self):
        q = defaultdict(set)
        for pet_guid, targets in self.spec_pets.items():
            pet_id = pet_guid[6:-6]
            for target_guid in targets:
                enc_name = convert_to_fight_name(target_guid)
                if enc_name:
                    q[enc_name].add(pet_id)
        return dict(q)

    def get_pet_data(self):
        q = {}
        for pet_guid in self.spec_pets:
            pet_id = pet_guid[6:-6]
            if q.get(pet_id):
                continue
            q[pet_id] = self.everything[pet_guid].get('master_guid')
        return q

    def get_all_classes_in_segment(self, s, f):
        spell_id = self.spec_spell_id
        spell_id_filter = f",{spell_id},"
        
        players = set()
        for line in self.logs[s:f]:
            if spell_id_filter not in line:
                continue
            try:
                _, _, sGUID, _, _, _, _spell_id, _ = line.split(',', 7)
                if _spell_id == spell_id and sGUID.startswith("0x0"):
                    players.add(sGUID)
            except:
                pass
        return players

    def get_all_pets_in_segment(self, s, f):
        pets = set()
        for line in self.logs[s:f]:
            if "0xF14" not in line:
                continue
            try:
                _, _, sGUID, _, _, _, spell_id, _ = line.split(',', 7)
                if self.pet_spell_ids[spell_id] and sGUID.startswith("0xF14"):
                    pets.add(sGUID)
            except:
                pass
        return pets
        
    def update_pet_owner(self, owner_guid, pet_id):
        if self.pet_data.get(pet_id):
            return

        self.pet_data[pet_id] = owner_guid
        
        PET_DATA = {
            'name': self.pet_name,
            'master_name': self.everything[owner_guid]['name'],
            'master_guid': owner_guid
        }

        for guid in self.spec_pets:
            if guid[6:-6] == pet_id:
                self.everything[guid] = PET_DATA
                print(f"set pet owner for {guid} {PET_DATA}")
    
    def filter_pets_by_combat(self):
        iosadjfiosajfuisdoj = []

        for enc_name, pet_ids in self.pet_by_target.items():
            if not pet_ids:
                continue

            boss_segments = self.enc_data.get(enc_name)
            if not boss_segments:
                continue

            for s, f in boss_segments:
            # for i, (s, f) in enumerate(boss_segments):
                _owners = self.get_all_classes_in_segment(s, f)
                _pets = self.get_all_pets_in_segment(s, f)
                if self.filter_out_pets(_pets, _owners):
                    self.update_pet_owner(_owners.pop(), _pets.pop()[6:-6])

                if len(_owners) != len(_pets):
                    continue

                _pets = {k[6:-6] for k in _pets}
                iosadjfiosajfuisdoj.append((_owners, _pets))

        # print(self.spec_pets)
        for _o, _p in check_negative(iosadjfiosajfuisdoj):
            self.update_pet_owner(_o, _p)

    def filter_out_pets(self, pets: set[str], owners: set[str]):
        for pet_guid in set(pets):
            if pet_guid not in self.everything:
                continue
            master_guid = self.everything[pet_guid].get('master_guid')
            if master_guid:
                if pet_guid in pets:
                    pets.remove(pet_guid)
                if master_guid in owners:
                    owners.remove(master_guid)
        return len(pets) == 1 and len(owners) == 1

    def filter_loop(self):
        for n in range(len(self.pet_data)):
            if None not in self.pet_data.values():
                break

            print('filter_pets_by_combat Loop:', n+1)
            print(self.pet_data)
            pet_data_cached = dict(self.pet_data)
            self.filter_pets_by_combat()
            
            if self.pet_data == pet_data_cached:
                break
        
        for pet_id in list(self.missing_owner):
            if self.pet_data.get(pet_id):
                self.missing_owner.remove(pet_id)
