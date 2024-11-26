
from c_path import Files
from api_top_db_v2 import Columns, DB


class Encounter:
    def __init__(self, name: str, mode: str = "25H") -> None:
        self.name = name
        self.mode = mode
        self.table_name = DB.get_table_name(name, mode)

    def __str__(self):
        return self.table_name

    def query_row_id(self, row_id):
        return f'''
        SELECT *
        FROM [{self.table_name}]
        WHERE {Columns.PLAYER_RAID_ID}='{row_id}'
        '''
    def query_row_id_min(self, row_id):
        return f'''
        SELECT {Columns.DURATION}, {Columns.REPORT_ID}
        FROM [{self.table_name}]
        WHERE {Columns.PLAYER_RAID_ID}='{row_id}'
        '''
    def query_stats(self):
        return f"""
        SELECT {Columns.SPEC}, {Columns.USEFUL_DPS}
        FROM [{self.table_name}]
        """
    def query_dps_spec(self, spec):
        return f"""
        SELECT {Columns.USEFUL_DPS}
        FROM [{self.table_name}]
        WHERE {Columns.SPEC}={spec}
        """
    def query_dps(self, spec):
        return f'''
        SELECT {Columns.PLAYER_RAID_ID}, {Columns.USEFUL_DPS}
        FROM [{self.table_name}]
        WHERE {Columns.SPEC}={spec}
        ORDER BY {Columns.USEFUL_DPS} DESC
        '''
    def query_players_data(self):
        return f'''
        SELECT {Columns.PLAYER_RAID_ID}, {Columns.GUID}, {Columns.NAME}, {Columns.SPEC}
        FROM [{self.table_name}]
        '''

class Phase:
    BOSSES_GET_GUID_NAME_PAIRS_FROM: tuple[Encounter]
    FOR_POINTS: tuple[Encounter]
    OTHER: tuple[Encounter]
    ALL_BOSSES: tuple[Encounter]


class Tier_10:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = (
        Encounter("Deathbringer Saurfang"),
        Encounter("The Lich King"),
        Encounter("Blood-Queen Lana'thel"),
        Encounter("Valithria Dreamwalker"),
    )
    FOR_POINTS = (
        Encounter("Lord Marrowgar"),
        Encounter("Lady Deathwhisper"),
        Encounter("Deathbringer Saurfang"),
        Encounter("Festergut"),
        Encounter("Rotface"),
        Encounter("Professor Putricide"),
        Encounter("Blood Prince Council"),
        Encounter("Blood-Queen Lana'thel"),
        Encounter("Sindragosa"),
        Encounter("The Lich King"),
    )
    OTHER = (
        Encounter("Toravon the Ice Watcher", "25N"),
        Encounter("Halion"),
        Encounter("Anub'arak"),
        Encounter("Valithria Dreamwalker"),
    )
    ALL_BOSSES = FOR_POINTS + OTHER


class Tier_3:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = (
        Encounter("Patchwerk", "25N"),
        Encounter("Anub'Rekhan", "25N"),
        Encounter("Noth the Plaguebringer", "25N"),
        Encounter("Kel'Thuzad", "25N"),
    )
    FOR_POINTS = (
        Encounter("Anub'Rekhan", "25N"),
        Encounter("Grand Widow Faerlina", "25N"),
        Encounter("Maexxna", "25N"),
        Encounter("Noth the Plaguebringer", "25N"),
        Encounter("Heigan the Unclean", "25N"),
        Encounter("Loatheb", "25N"),
        Encounter("Patchwerk", "25N"),
        Encounter("Grobbulus", "25N"),
        Encounter("Gluth", "25N"),
        Encounter("Thaddius", "25N"),
        Encounter("Instructor Razuvious", "25N"),
        Encounter("Gothik the Harvester", "25N"),
        Encounter("The Four Horsemen", "25N"),
        Encounter("Sapphiron", "25N"),
        Encounter("Kel'Thuzad", "25N"),
    )
    OTHER = ()
    ALL_BOSSES = FOR_POINTS + OTHER


class Tier_5:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = (
        Encounter("Prince Malchezaar", "10N"),
        Encounter("Gruul the Dragonkiller", "25N"),
        Encounter("Magtheridon", "25N"),
    )
    FOR_POINTS = (
        Encounter("Attumen the Huntsman", "10N"),
        Encounter("Moroes", "10N"),
        Encounter("Maiden of Virtue", "10N"),
        Encounter("Opera House", "10N"),
        Encounter("The Curator", "10N"),
        Encounter("Terestian Illhoof", "10N"),
        Encounter("Shade of Aran", "10N"),
        Encounter("Netherspite", "10N"),
        Encounter("Prince Malchezaar", "10N"),

        Encounter("High King Maulgar", "25N"),
        Encounter("Gruul the Dragonkiller", "25N"),

        Encounter("Magtheridon", "25N"),
    )
    OTHER = ()
    ALL_BOSSES = FOR_POINTS + OTHER


class Tier_6:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = (
        Encounter("Archimonde", "25N"),
        Encounter("Illidan Stormrage", "25N"),
        Encounter("Kil'jaeden", "25N"),
    )
    FOR_POINTS = (
        Encounter("Rage Winterchill", "25N"),
        Encounter("Anetheron", "25N"),
        Encounter("Kaz'rogal", "25N"),
        Encounter("Azgalor", "25N"),
        Encounter("Archimonde", "25N"),

        Encounter("High Warlord Naj'entus", "25N"),
        Encounter("Supremus", "25N"),
        Encounter("Shade of Akama", "25N"),
        Encounter("Teron Gorefiend", "25N"),
        Encounter("Gurtogg Bloodboil", "25N"),
        Encounter("Reliquary of Souls", "25N"),
        Encounter("Mother Shahraz", "25N"),
        Encounter("The Illidari Council", "25N"),
        Encounter("Illidan Stormrage", "25N"),

        Encounter("Kalecgos", "25N"),
        Encounter("Brutallus", "25N"),
        Encounter("Felmyst", "25N"),
        Encounter("Eredar Twins", "25N"),
        Encounter("M'uru", "25N"),
        Encounter("Kil'jaeden", "25N"),
    )
    OTHER = ()
    ALL_BOSSES = FOR_POINTS + OTHER


class Tier_7(Tier_3):
    OTHER = (
        Encounter("Archavon the Stone Watcher", "25N"),
    )
    ALL_BOSSES = Tier_3.FOR_POINTS + OTHER

class Tier_8:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = (
        Encounter("XT-002 Deconstructor", "25H"),
        Encounter("Kologarn", "25N"),
        Encounter("Yogg-Saron", "25H"),
        Encounter("Algalon the Observer", "25N"),
    )
    FOR_POINTS = (
        Encounter("Ignis the Furnace Master", "25N"),
        Encounter("Razorscale", "25N"),
        Encounter("XT-002 Deconstructor", "25H"),
        Encounter("Assembly of Iron", "25H"),
        Encounter("Kologarn", "25N"),
        Encounter("Auriaya", "25N"),
        Encounter("Hodir", "25N"),
        Encounter("Thorim", "25N"),
        Encounter("Freya", "25H"),
        Encounter("Mimiron", "25H"),
        Encounter("General Vezax", "25H"),
        Encounter("Yogg-Saron", "25H"),
        Encounter("Algalon the Observer", "25N"),
    )
    OTHER = (
        Encounter("Emalon the Storm Watcher", "25N"),
    )
    ALL_BOSSES = FOR_POINTS + OTHER


SERVER_PHASE: dict[str, str] = Files.server_phases.json_ignore_error()

def get_server_phase(server):
    try:
        phase = SERVER_PHASE[server]
        return globals()[phase]
    except KeyError:
        return Tier_10

def main():
    print(get_server_phase("Lordaeron"))
    print(get_server_phase("Whitemane-Frostmourne"))
    print(get_server_phase("Onyxia"))


if __name__ == "__main__":
    main()
