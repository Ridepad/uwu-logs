import json
import os

import pandas as pd

from constants_WBF import running_time, CLASSES_LIST, SPECS_LIST

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
TMP_CACHE = os.path.join(DIR_PATH, "tmp_cache")
# TMP_CACHE = os.path.join(DIR_PATH, "tmp_cache_redo")
DB_PATH = os.path.join(DIR_PATH, "kill_db")
JSON_CACHE = os.path.join(DIR_PATH, "kill_json")

SAVES = []

def load_json(name):
    print(name)
    try:
        with open(name) as file:
            return json.load(file)
    except FileNotFoundError:
        print('-- empty')
        return {}

def add_small(data: dict, s):
    for x in range(s, s+10):
        chunk_name = os.path.join(TMP_CACHE, f"data_kills_{x}-{x+1}.json")
        chunk_data = load_json(chunk_name)
        data.update(chunk_data)
    print("TOTAL ENTRIES:", len(data))
    return dict(sorted(data.items()))

@running_time
def save_new(full_name, data):
    old_name = f"{full_name}.old"
    if os.path.isfile(full_name):
        if os.path.isfile(old_name):
            os.remove(old_name)
        os.rename(full_name, old_name)

    with open(full_name, 'w') as file:
        json.dump(data, file)

def combine_json(s):
    full_name = os.path.join(TMP_CACHE, f"data_kills_{s}-{s+1}.json")
    _old = load_json(full_name)
    _new = dict(_old)
    _new = add_small(_new, s*10)

    # if _new == {}: return
    # if _old == _new: return
    # if _new and _old != _new:
    #     t = threading.Thread(target=save_new, args=(full_name, _new))
    #     t.start()
    #     SAVES.append(t)

    return _new



def is_guild(row: dict):
    gnames: list[str] = row["g"]
    guilds: list[int] = row["pg"]
    if gnames and guilds:
        the_guild = max(guilds, key=guilds.count)
        if guilds.count(the_guild) > len(guilds) // 2:
            return gnames[the_guild]
    return 'Pug'


def convert_players(report_data):
    names = report_data['pn']
    guilds = report_data['pg']
    classes = report_data['pc']
    specs = report_data['ps']
    return tuple(
        (name, guild, class_name, spec_name)
        for name, guild, class_name, spec_name in zip(names, guilds, classes, specs)
    )


def reformat(report_data: dict):
    # if type(report_data) is not dict:
    #     print(report_data)
    return {
        'boss': report_data['b'],
        'size': int(report_data['s']),
        'mode': int(report_data['m']),
        'duration': int(report_data['t']),
        'wipes': int(report_data['w']),
        'mainGuild': is_guild(report_data),
        'achievements': tuple(report_data['a']),
        'guilds': tuple(report_data['g']),
        'playerNames': tuple(report_data['pn']),
        'playerGuilds': tuple(report_data['pg']),
        'playerClasses': tuple(report_data['pc']),
        'playerSpecs': tuple(report_data['ps']),
    }

@running_time
def format_reports(data: dict):
    formatted_data = {
        int(report_id): reformat(report_data)
        for report_id, report_data in data.items()
    }
    return dict(sorted(formatted_data.items()))

@running_time
def dataframe_from_dict(data):
    return pd.DataFrame.from_dict(data, orient="index")

@running_time
def dataframe_save(df: pd.DataFrame, s: int):
    name = os.path.join(DB_PATH, f"data_kills_{s}-{s+1}.pickle")
    df.to_pickle(name)

@running_time
def save_list(df: pd.DataFrame):
    names: dict[str, int] = {}
    guilds: dict[str, int] = {}
    for _, row in df.iterrows():
        for name in row['names']:
            if name:
                names[name] = names.get(name, 0) + 1
        for guild_name in row['guilds']:
            if guild_name:
                guilds[guild_name] = guilds.get(guild_name, 0) + 1

    for ff in ["names", "guilds"]:
        _d: dict[str, int] = locals()[ff]
        _sorted = sorted(_d.items(), key=lambda x: x[1], reverse=True)
        _dict = {x.lower(): x for x, _ in _sorted}
        with open(f'{ff}.txt', 'w') as f:
            json.dump(_dict, f, indent=4)

@running_time
def read_all_json(s, shift=10):
    old_name = os.path.join(JSON_CACHE, f"data_kills_{s}-{s+1}.json")
    all_json = load_json(old_name)
    for x in range(s*10, s*10+shift):
        print(x)
        new_data = combine_json(x)
        all_json.update(new_data)
    return all_json

@running_time
def read_all_json(s, shift=10):
    all_json = {}
    for x in range(s*10, s*10+shift):
        all_json |= combine_json(x)
    return all_json

@running_time
def main(s, shift=10):
    all_json = read_all_json(s, shift)
    data = format_reports(all_json)
    df = dataframe_from_dict(data)
    dataframe_save(df, s)

if __name__ == "__main__":
    for x in range(25,34):
        main(x)
    # main(36)
