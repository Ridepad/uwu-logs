from logs_units_guid import UDK_PET_NAMES
import pandas as pd
import pickle
import constants
# split 1 column into time + event

COLS = ['time','event','sourceGUID', 'sourceName', 'targetGUID', 'targetName', 'other1', 'other2', 'other3', 'other4', 'other5', 'other6']
COLS = ['time_event','sourceGUID', 'sourceName', 'sourceFlags', 'targetGUID', 'targetName', 'targetFlags', 'other1', 'other2', 'other3', 'other4', 'other5', 'other6']

@constants.running_time
def cache_df(name, df):
    with open(f'{name}.df', 'wb') as f:
        pickle.dump(df, f)

@constants.running_time
def cut_df(df):
    df[['time', 'event']] = df['time_event'].str.split('  ', expand=True)
    df.drop(columns=['sourceFlags', 'targetFlags', 'time_event'], inplace=True)
    # q = df['time'].str.split(' ')
    # df['day'] = q.apply(lambda x: x[0])
    # df['time'] = q.apply(lambda x: x[1])
    cols = list(df.columns.values)
    cols = cols[-2:] + cols[:-2]
    # cols.insert(0, cols.pop(-1))
    # cols.insert(0, cols.pop(-1))
    # df = df[cols]
    # return df
    return df[cols]

@constants.running_time
def read_from_file(name):
    return pd.read_csv(name, delimiter=',', names=COLS)

@constants.running_time
def drop_cast_failed(df):
    filt = df['event'] == 'SPELL_CAST_FAILED'
    q = df.loc[filt].index.values
    df.drop(q, inplace=True)
    return df

@constants.running_time
def get_df(name):
    try:
        with open(f'{name}.df', 'rb') as f:
            return pickle.load(f)
    except:
        df = read_from_file(name)
        df = cut_df(df)
        df = drop_cast_failed(df)
        # cache_df(name, df)
        return df

@constants.running_time
def f1(df):
    return df['event'].value_counts()

@constants.running_time
def f2(df):
    _filt = df['other2'] == 'Life Tap'
    return df[_filt]

@constants.running_time
def f3(df):
    _filt = df['other2'] == 'Life Tap'
    return df.loc[_filt]


# name = '21-05-24-Passionne'
# name = f'RawLogs\{name}.txt'
udks_pet_name_prefix = [
    'Bat', 'Blight', 'Bone', 'Brain', 'Carrion', 'Corpse', 'Crypt', 'Dirt', 'Earth', 'Eye', 'Grave', 'Gravel',
    'Hammer', 'Limb', 'Plague', 'Rat', 'Rib', 'Root', 'Rot', 'Skull', 'Spine', 'Stone', 'Tomb', 'Worm']
udks_pet_name_suffix = [
    'basher', 'breaker', 'breaker', 'catcher', 'chewer', 'chomp', 'cruncher', 'drinker', 'feeder', 'flayer',
    'gnaw', 'gobbler', 'grinder', 'keeper', 'leaper', 'masher', 'muncher', 'ravager', 'rawler', 'ripper', 'rumbler',
    'slicer', 'stalker', 'stealer', 'thief']
UDK_PET_NAMES = {x+y for x in udks_pet_name_prefix for y in udks_pet_name_suffix}
PRIMARY_UDKS_PETS = {'Army of the Dead Ghoul', 'Risen Ghoul', 'Risen Ally'}
UDK_PET_NAMES = UDK_PET_NAMES | PRIMARY_UDKS_PETS
# df = get_df(name)
import os
for name in os.listdir('F:\Python\wow_logs\RawLogs'):
    name = f'RawLogs\{name}'
    df = read_from_file(name)
    filt = df['other2'] == 'Claw'
    df = df.loc[filt]
    q = df['sourceName'].value_counts()
    # print(type(q))
    # print(q)
    for x in q.index.values:
        if x not in UDK_PET_NAMES:
            print(x)
