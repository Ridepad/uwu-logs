import constants
import pickle

# HPS = {
#     "Lord Marrowgar": [,,,47064376],
#     "Lady Deathwhisper":[,,,33225699],
#     "The Skybreaker":[,,,33225699],
#     "Orgrim's Hammer":[,,,33225699],
#     "Deathbringer Saurfang":[,,,43926752],
#     "Festergut":[,,,57523128],
#     "Rotface":[,,,61636896],
#     "Professor Putricide":[,,,52712096],
#     "Prince Valanar":[,,,41171916],
#     "Prince Keleseth":[,,,33225699],
#     "Prince Taldaram":[,,,33225699],
#     "Blood-Queen Lana'thel":[,,,33225699],
#     "Valithria Dreamwalker":[,,,33225699],
#     "Sindragosa":[,,,33225699],
#     "The Lich King": [,30.93,,],
#     "Baltharus the Warborn":[,,11156000,],
#     "Saviana Ragefire":[,,13945000,],
#     "General Zarithrian":[,,14098395,], 
#     "Halion":[,,40440500,],
#     "Anub'arak":[]}

# valk = [,1417500,,]
DIFFICULTY = ('10NM', '10HM', '25NM', '25HM')
SPELLS = {
    "Lord Marrowgar": ('Bone Spike Graveyard', ('69057', '72088', '70826', '72089')),
    "Lady Deathwhisper": ('Shadow Bolt', ('71254', '72503', '72008', '72504')),
    "Gunship": ('Shoot', ('70162', '72567', '72566', '72568')),
    "Deathbringer Saurfang": ('Rune of Blood', ('72409', '72448', '72447', '72449')),
    "Festergut": ('Gastric Bloat', ('72219', '72552', '72551', '72553')),
    "Rotface": ('Mutated Infection', ('69674', '73022', '71224', '73023')),
    "Professor Putricide": ('Malleable Goo', ('72295', '74280', '72615', '74281')),
    "Blood Prince Council": ('Empowered Shock Vortex', ('72039', '73038', '73037', '73039')),
    "Blood-Queen Lana'thel": ('Shroud of Sorrow', ('70985', '71699', '71698', '71700')),
    "Valithria Dreamwalker": ('Frostbolt Volley', ('70759', '72015', '71889', '72016')),
    "Sindragosa": ('Frost Aura', ('70084', '71051', '71050', '71052')),
    "The Lich King": ('Infest', ('70541', '73780', '73779', '73781')),
    "Baltharus the Warborn": ('Enervating Brand', ('99999', '99999', '74502', '99999')),
    "Saviana Ragefire": ('Flame Breath', ('74403', '99999', '74404', '99999')),
    "General Zarithrian": ('Intimidating Roar', ('99999', '99999', '74384', '99999')),
    "Halion": ('Flame Breath', ('74525','74527','74526','74528')),
    "Anub'arak": ('Penetrating Cold', ('66013','68509','67700','68510'))}


def get_encounter_data():
    with open(constants.ENCOUNTER_DATA_FILE_NAME, 'rb') as f:
        return pickle.load(f)
            
def fast_in(logs, boss_name):
    spell_name, ids = SPELLS[boss_name]
    for line in logs:
        if spell_name in line:
            for n, id_ in enumerate(ids):
                if id_ in line:
                    return DIFFICULTY[n]
    return '10NM'

def diff_gen(logs_raw, enc_data):
    for boss_name, tries in enc_data.items():
        for n, (s, f) in enumerate(tries, 1):
            logs_slice = logs_raw[s:f]
            diff = fast_in(logs_slice, boss_name)
            kill = 'UNIT_DIED' in logs_slice[-1]
            yield diff, boss_name, n, kill

if __name__ == "__main__":
    logs_cut_name = constants.LOGS_CUT_NAME
    guids, players = constants.get_guids()

    logs_raw = constants.logs_read(logs_cut_name)
    logs_raw = constants.logs_splitlines(logs_raw)
    enc_data = get_encounter_data()
    for x in diff_gen(logs_raw, enc_data):
        print(x)
