
from multiprocessing import Pool
import is_kill
import main_db


AA = [
    'The Lich King',
    'Lord Marrowgar', 'Lady Deathwhisper', 'Gunship Battle', 'Deathbringer Saurfang',
    'Festergut', 'Rotface', 'Professor Putricide', 'Blood Prince Council', "Blood-Queen Lana'thel",
    'Valithria Dreamwalker', 'Sindragosa', 'Halion', 'Baltharus the Warborn', 'General Zarithrian',
    'Saviana Ragefire', "Anub'arak", 'Northrend Beasts', 'Lord Jaraxxus', 'Faction Champions',
    "Twin Val'kyr", 'Toravon the Ice Watcher', 'Archavon the Stone Watcher', 'Emalon the Storm Watcher',
    'Koralon the Flame Watcher', 'Onyxia', 'Malygos', 'Sartharion', "Anub'Rekhan", 'Grand Widow Faerlina',
    'Maexxna', 'Noth the Plaguebringer', 'Heigan the Unclean', 'Loatheb', 'Patchwerk', 'Grobbulus', 'Gluth',
    'Thaddius', 'Instructor Razuvious', 'Gothik the Harvester', 'The Four Horsemen', 'Sapphiron', "Kel'Thuzad",
    'Flame Leviathan', 'Ignis the Furnace Master', 'Razorscale', 'XT-002 Deconstructor', 'Assembly of Iron',
    'Kologarn', 'Auriaya', 'Hodir', 'Thorim', 'Freya', 'Mimiron', 'General Vezax', 'Yogg-Saron', 'Algalon the Observer'
]

def convert_to_json(v):
    try:
        v = int(v)
    except:
        try:
            if type(v) != str:
                v = list(v)
        except:
            pass
    return v

COLUMNS = ['guild', 'duration', 'attempts', 'date', 'report_id']
def bfosdpkfsopd(data):
    return [{k: convert_to_json(v) for k, v in d.items() if k in COLUMNS} for _, d in data]

def __main(top: is_kill.Top, filters):
    ALL = {}
    COMB = {}
    db = top.prep_df(filters)
    for bossname in AA:
        db_f = main_db.df_apply_filters(db, {'boss': bossname})
        _all = is_kill.make_top_all(db_f)
        ALL[bossname] = bfosdpkfsopd(_all)
        _combined = is_kill.make_top_combined(db_f)
        COMB[bossname] = bfosdpkfsopd(_combined)
    
    return {
        'filters': filters,
        'all': ALL,
        'combined': COMB,
    }

def __themain(s):
    top = is_kill.Top(s)
    
    q = [
        (top, {'difficulty': diff, 'size': size})
        for size in [10, 25]
        for diff in [0, 1]
    ]

    with Pool(4) as p:
        done = p.starmap(__main, q)
    DATA = {}
    for d in done:
        diff = d['filters']['difficulty']
        size = d['filters']['size']
        for type_ in ['all', 'combined']:
            for bossname, new_data in d[type_].items():
                q = DATA.setdefault(type_, {}).setdefault(bossname, {}).setdefault(size, {})
                q[diff] = new_data
    # for d in done:
    #     for type_, bosses in d.items():
    #         for boss, sizes in bosses.items():
    #             for size, new_data in sizes.items():
    #                 DATA.setdefault(type_, {}).setdefault(boss, {}).setdefault(size, {}).update(new_data)

    print('done')

    return DATA
    # DATA = {'all': ALL, 'combined': COMB}
    # with open('_DATA3.json', 'w') as f:
    #     json.dump(DATA, f, indent=4, default=list)
    
    # for n, data in __q:
    #     z = f'{n:>3} | {data["date"]:>9} | {data["duration"]:>5} | {data["attempts"]:>2} | {data["guild"]:>30}'
    #     # z = f'{data["report_id"]} | {data["date"]:>9} | {data["duration"]:>5} | {data["attempts"]:>2} | {data["guild"]:>30}'
    #     print(z)

def main():
    DATA = {}
    for i in range(len(Top.files)):
        name = Top.files[i].split('_')[-1].split('.')[0]
        print(name)
        DATA[name] = __themain(i)
    with open('_DATA4.json', 'w') as f:
        json.dump(DATA, f, indent=4, default=list)


if __name__ == "__main__":
    main()