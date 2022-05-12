import os

import pandas
from pandas import DataFrame

try:
    from . import constants_WBF
except ImportError:
    import constants_WBF

real_path = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(real_path)
DB_PATH = os.path.join(DIR_PATH, "kill_db")

CLASSES_LIST = constants_WBF.CLASSES_LIST
SPECS_LIST = constants_WBF.SPECS_LIST
RACES_LIST = constants_WBF.RACES_LIST
FACTION = constants_WBF.FACTION
BOSSES_FROM_HTML = constants_WBF.BOSSES_FROM_HTML

# df_cols = boss, size, mode, duration, wipes, mainGuild, achievements, guilds, playerNames, playerGuilds, playerClasses, playerSpecs

def df_from_pickle(name):
    df_pickle: DataFrame
    try:
        df_pickle = pandas.read_pickle(name)
        return df_pickle
    except FileNotFoundError:
        print('NO DB:', name)
        return

DF_CACHE: dict[str, DataFrame] = {}
@constants_WBF.running_time
def df_read(name):
    if name in DF_CACHE:
        return DF_CACHE[name]
    
    if len(DF_CACHE) > 10:
        DF_CACHE.pop(min(DF_CACHE))
    
    df = df_from_pickle(name)
    DF_CACHE[name] = df
    return df

def get_df_name_by_n(n):
    return os.path.join(DB_PATH, f"data_kills_{n}-{n+1}.pickle")

def get_df_by_n(n):
    name = get_df_name_by_n(n)
    return df_read(name)

def get_df_by_kill(kill_id):
    n = kill_id // 100000
    return get_df_by_n(n)

class DB_Cache:
    cache = {}
    def get_df(self, n: int):
        name = f"{DB_PATH}/data_kills_{n}-{n+1}.pickle"
        if name in self.cache:
            return self.cache[name]
        try:
            df = pandas.read_pickle(name)
        except FileNotFoundError:
            df = None
            print('NO DB:', name)
        if len(self.cache) > 2:
            self.cache.pop(min(self.cache))
        self.cache[name] = df
        return df

    def df_from_range(self, start, end):
        sID = start // 100000
        eID = end // 100000
        DF = self.get_df(sID)
        DF = DF.loc[start:]
        if sID == eID:
            return DF.loc[:end]
        DF2 = self.get_df(eID)
        DF2 = DF2.loc[:end]
        return DF.append(DF2)

NUMBERS = ['wipes', 'duration']
TUPLES = ['guilds', 'playerNames', 'playerGuilds', 'playerClasses', 'playerSpecs']

def get_df_filter(category: str, _filter):
    if category in TUPLES:
        # print('category in TUPLES')
        return lambda x: _filter in x
    elif category in NUMBERS:
        # print('category in NUMBERS')
        return lambda x: _filter <= x
    elif category == "achievements":
        # print('category is achievements')
        return lambda x: bool(_filter) == bool(x)
    elif category == "mainGuild":
        # print('category is mainGuild')
        return lambda x: bool(_filter) == (x == 'Pug')
    else:
        # print('category is else')
        return lambda x: _filter == x

def filter_to_number(v):
    try:
        return int(v)
    except ValueError:
        return v

def df_filter_by(df: DataFrame, category: str, filter_by):
    by_category = df[category]
    filter_by = filter_to_number(filter_by)
    df_filter = get_df_filter(category, filter_by)
    filtered = by_category.apply(df_filter)
    return df[filtered]

DB_CATEGORIES = {
    'boss': "boss",
    "size": 'size',
    "mode": 'mode',
    'wipes': 'wipes',
    'dur': 'duration',
    'isPug': 'mainGuild',
    'achievs': 'achievements',
    'names': 'playerNames',
    'guilds': 'guilds',
    "cls": "playerClasses",
    "specs": "playerSpecs",
}

def cnv_cat(c: str):
    return DB_CATEGORIES.get(c, c)

def cnv_var(value: str):
    try:
        return int(value)
    except ValueError:
        # value = value.lower().title()
        return value.replace('+', ' ')

def convert_filter(args: dict):
    return {
        cnv_cat(k): cnv_var(v)
        for k, v in args.items()
        if v
    }

@constants_WBF.running_time
def df_apply_filters(df: DataFrame, filters: dict[str]):
    if df is None:
        return
    for category, _filter in filters.items():
        df = df_filter_by(df, category, _filter)
        # print(category, _filter)
        # print(df)
        # for row_, data in df.iterrows():
        #     print(data)
        #     break
        if df.empty: break
    return df

@constants_WBF.running_time
def get_data(filters: dict, name: str):
    print(f"[main_db] get_data filters{filters}")
    filters = convert_filter(filters)
    if 'boss' in filters:
        filters['boss'] = BOSSES_FROM_HTML[filters['boss']]
    print(f"[main_db] get_data filters{filters}")
    name = os.path.join(DB_PATH, name)
    df = df_read(name)
    return df_apply_filters(df, filters)


def has_achievs(df: DataFrame):
    filt = df["achievements"].apply(lambda x: bool(x))
    return df[filt]

def has_1_achievs(df: DataFrame):
    filt = df["achievements"].apply(lambda x: len(x) == 1)
    return df[filt]




def __main():
    s = 34
    name = os.path.join(DB_PATH, f"data_kills_{s}-{s+1}.pickle")
    df = df_read(name)
    s = set()
    for index, row in df.iterrows():
        s.update(row['guilds'])

    print(sorted(s))

if __name__ == "__main__":
    df = get_df_by_n(36)
    print(df.loc[3600000])