import json
import time

import kill_date
import main
import pickle

tm = time.time

'''
every 300
'''

class ETA_TIME:
    started = 0
    at_index = 0
    total = 0
    df_index = 0
    date = ""

    def new(self, total: int):
        self.started = tm()
        self.total = total

CURRENT = ETA_TIME()

def get_time_str(t):
    t = int(t)
    seconds = t % 60
    minutes = t // 60 % 60
    hours = minutes // 60
    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"

def create_report_str():
    current = f"{CURRENT.at_index:>7}/{CURRENT.total:>7}"

    duration = tm() - CURRENT.started
    running = get_time_str(duration)

    e = duration / (CURRENT.at_index / CURRENT.total) - duration
    eta = get_time_str(e)
    posts = f" | POSTS: {kill_date.POST_REQUESTS[0]:>8}"
    v = f" | {CURRENT.df_index} | {CURRENT.date}"
    print(f"\r{current} | {running} | ETA: {eta}{posts}{v} | ", end="")

def saveshit():
    with open('cache_no_char.pickle','rb') as f:
        NO_CHAR_OLD = pickle.load(f)
    if NO_CHAR_OLD != kill_date.NO_CHAR:
        with open('cache_no_char.pickle', 'wb') as f:
            pickle.dump(kill_date.NO_CHAR, f)
            
    with open('cache_achi.json','r') as f:
        CACHE_OLD = json.load(f)
    if CACHE_OLD != kill_date.CACHE:
        with open('cache_achi.json', 'w') as f:
            json.dump(kill_date.CACHE, f)

def loop1(df):
    for n, (index, row) in enumerate(df.iterrows(), 1):
        CURRENT.at_index = n
        CURRENT.df_index = index

        names = row['names']
        achievements = row['achievements']
        try:
            d = kill_date.main(names, achievements)
            CURRENT.date = d
            create_report_str()
        except Exception as e:
            print(e)
            print(index, achievements, names)
        if n%100==0:
            saveshit()
    saveshit()

def loop2(df):
    d = {}
    for n, (index, row) in enumerate(df.iterrows(), 1):
        CURRENT.at_index = n
        CURRENT.df_index = index
        _id = d.setdefault(index, {})
        _id['names'] = row['names']
        _id['achievements'] = row['achievements']
    

def main1(s):
    name = f"data_kills_{s}-{s+10}"
    df = main.get_df(name)
    df = main.has_achievs(df)
    df = df.loc[::50]
    CURRENT.new(len(df))
    loop1(df)

main1(320)

# NO_ = set()
# with open('cache_no_char.pickle', 'wb') as f:
#     pickle.dump(NO_, f)