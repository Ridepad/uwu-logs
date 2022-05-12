from constants import CLASSES_LIST, SPECS_LIST, CLASS_TO_HTML, find_date, get_all_files

DB_PATH = "WarmaneBossFights/kill_db"
MODES = ["N", "H"]
PLAYER_DATA = ["playerNames", "playerGuilds", "playerClasses", "playerSpecs"]


def page_parse(page):
    q = get_all_files(DB_PATH, 'pickle')[::-1]
    page %= len(q)
    name = q[page]
    page = q.index(name)
    # print("[ladder_db_list] Page {name}")
    return page, name


def get_guild(report_data):
    guilds: list[str] = report_data["g"]
    if guilds:
        the_guild = max(guilds, key=guilds.count)
        if the_guild and guilds.count(the_guild) > len(guilds) // 2:
            return the_guild
    return 'Pug'

def get_guild(report_data):
    if not report_data["g"]:
        return 'Pug'
    players: list[str] = report_data["p"]
    guilds = [p[1] for p in players]
    the_guild = max(guilds, key=guilds.count)
    if the_guild and guilds.count(the_guild) > len(guilds) // 2:
        return the_guild
    return 'Pug'

def duration_format(duration: int):
    return f"{duration//60}:{duration%60:0>2}"

def players_gen(report_data):
    guilds = report_data['guilds']
    for name, gi, ci, si in zip(*[report_data[v] for v in PLAYER_DATA]):
        class_name = CLASSES_LIST[ci]
        spec_name, icon = SPECS_LIST[si]
        yield {
            "name": name,
            "icon": icon,
            "spec": spec_name,
            "guild": guilds[gi],
            "class": CLASS_TO_HTML[class_name],
        }

def df_gen(df):
    for report_id, report_data in df.iterrows():
        yield {
            "id": report_id,
            "d": find_date(report_id),
            "b": report_data["boss"],
            "s": report_data["size"],
            "m": MODES[report_data["mode"]],
            "w": report_data["wipes"],
            "t": duration_format(report_data["duration"]),
            "g": report_data["mainGuild"],
            "p": players_gen(report_data),
        }
