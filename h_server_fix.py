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
SERVERS_NAMES = set(SERVERS.values())


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
    ServerID("Way of Elendil", "(way.*?elendil)"),
    ServerID("WoW Brasil", "(wow.*?brasil)"),
    ServerID("Aequitas", "(aequitas)"),
    ServerID("Everlook", "(everlook)"),
    # ServerName("", ""),
]

def server_cnv(server: str):
    if not server:
        return ""
    if server in SERVERS_NAMES:
        return server
    if server in SERVERS_WC:
        return server
    
    _server_l = server.lower()
    for _server in SERVERS_OTHER:
        if re.findall(_server.re_string, _server_l):
            return _server.no_space

    return server.replace(" ", "-").title()


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
    z = server_cnv("Lordaeron")
    print(z)
    z = server_cnv("Wow Circle 3.3.5a x5")
    print(z)
    z = server_cnv("rIsing godSs")
    print(z)
    z = server_cnv("risINGg godds")
    print(z)
    z = server_cnv("Way-of-Elendil")
    print(z)

if __name__ == "__main__":
    test1()
