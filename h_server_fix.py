import re

from constants import SERVERS
SERVERS = set(SERVERS.values())

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
    # ServerName("", ""),
]

def server_cnv(server: str):
    if not server:
        return ""
    if server in SERVERS:
        return server
    
    _server_l = server.lower()
    for _server in SERVERS_OTHER:
        if re.findall(_server.re_string, _server_l):
            return _server.no_space

    return server.replace(" ", "-").title()

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
