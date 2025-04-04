import re

from c_path import Directories, Files

SERVERS = {
    "0x06": "Lordaeron",
    "0x07": "Icecrown",
    "0x0D": "Frostmourne3",
    "0x0C": "Frostmourne2",
    "0x0A": "Blackrock",
    "0x0E": "Onyxia",
}
SERVERS_WC = {
    "WoW-Circle-x100": "6",
    "WoW-Circle-x1":   "2",
    "WoW-Circle-x5":   "1",
    "WoW-Circle-Fun":  "13",
}


class ServerID:
    __slots__ = "name", "re_string"

    def __init__(self, name: str, re_string: str) -> None:
        self.name = name
        self.re_string = re_string

    @property
    def no_space(self):
        return self.name.replace(" ", "-")

    @property
    def html(self):
        return self.no_space.lower()

    def __str__(self):
        return ' | '.join((
            self.name,
            self.re_string,
            self.no_space,
            self.html,
        ))
    
    __repr__ = __str__
         
SERVERS_WITH_SERVER_ID_IN_LOGS = [
    ServerID("Lordaeron", "(lordaeron)"),
    ServerID("Icecrown", "(icecrown)"),
    ServerID("Blackrock", "(blackrock)"),
    ServerID("Onyxia", "(onyxia)"),
]
SERVERS_OTHER = [
    ServerID("Rising Gods", "(risin.*?god)"),
    ServerID("WoW Circle", "(circle)"),
    ServerID("Whitemane-PTR", "(whitemane.*?ptr)"),
    ServerID("Whitemane-Frostmourne", "(frostmo)"),
    ServerID("Whitemane-Frostmourne", "(whitema)"),
    ServerID("WoW-Mania", "(mania)"),
    ServerID("ChromieCraft", "(chromie.*?craft)"),
    ServerID("EzWoW", "(ez.*?wow)"),
    ServerID("NaerZone", "(naer.*?zone)"),
    ServerID("Way of Elendil", "(elendil)"),
    ServerID("WoW Brasil", "(wow.*?brasil)"),
    ServerID("Aequitas", "(aequitas)"),
    ServerID("Everlook", "(everlook)"),
    ServerID("UltimoWoW", "(ultim.*wow)"),
    ServerID("UltimoWoW", "(benn?u)"),
    ServerID("FreedomUA", "(freedom)"),
    ServerID("Hellscream", "(hellscream)"),
    ServerID("Hellscream", "(garrosh)"),
    ServerID("WoWZone", "(wowzone)"),
    # ServerName("", ""),
]

def server_cnv(server: str):
    if not server:
        return ""
    
    _server_l = server.lower()
    for _server in SERVERS_WITH_SERVER_ID_IN_LOGS:
        if re.findall(_server.re_string, _server_l):
            return

    for _server in SERVERS_OTHER:
        if re.findall(_server.re_string, _server_l):
            return _server.no_space

    return server.replace(" ", "-")


@Directories.top.cache_until_new_self
def _get_servers(folder):
    s = set((
        file_path.stem
        for file_path in folder.iterdir()
        if file_path.suffix == ".db"
    ))
    SERVERS_MAIN = Files.server_main.json_cached_ignore_error()
    new = sorted(s - set(SERVERS_MAIN))
    return SERVERS_MAIN + new

def get_servers() -> list[str]:
    return _get_servers()

def test1():
    re_test = [
        "Lordaeron",
        "Wow Circle 3.3.5a x5",
        "rIsing godSs",
        "risINGg godds",
        "Way Elendil",
        "Way-of-Elendil",
        "Benu",
        "Bennu",
        "ULTIMAWOW",
        "ez--wow",
        "onyxia",
        "onyxia-test",
    ]
    for s in re_test:
        print(f"{s:30} | {server_cnv(s)}")

if __name__ == "__main__":
    test1()
