
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
        SELECT *
        FROM (
            SELECT {Columns.GUID}, {Columns.NAME}, {Columns.SPEC}
            FROM [{self.table_name}]
            ORDER BY {Columns.PLAYER_RAID_ID} DESC
        )
        GROUP BY {Columns.GUID}
        '''

class Phase:
    BOSSES_GET_GUID_NAME_PAIRS_FROM: list[Encounter]
    FOR_POINTS: list[Encounter]
    OTHER: list[Encounter]
    ALL_BOSSES: list[Encounter]


class Tier_10:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = [
        Encounter("Deathbringer Saurfang"),
        Encounter("The Lich King"),
        # Encounter("Festergut"),
        # Encounter("Blood-Queen Lana'thel"),
        # Encounter("Valithria Dreamwalker"),
    ]
    FOR_POINTS = [
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
    ]
    OTHER = [
        Encounter("Toravon the Ice Watcher", "25N"),
        Encounter("Halion"),
        Encounter("Anub'arak"),
        Encounter("Valithria Dreamwalker"),
    ]
    ALL_BOSSES = FOR_POINTS + OTHER


class Tier_7:
    BOSSES_GET_GUID_NAME_PAIRS_FROM = [
        Encounter("Patchwerk", "25N"),
        Encounter("Anub'Rekhan", "25N"),
        Encounter("Noth the Plaguebringer", "25N"),
        Encounter("Kel'Thuzad", "25N"),
    ]
    FOR_POINTS = [
        Encounter("Patchwerk", "25N"),
        Encounter("Grobbulus", "25N"),
        Encounter("Gluth", "25N"),
        Encounter("Thaddius", "25N"),
        Encounter("Anub'Rekhan", "25N"),
        Encounter("Grand Widow Faerlina", "25N"),
        Encounter("Maexxna", "25N"),
        Encounter("Noth the Plaguebringer", "25N"),
        Encounter("Heigan the Unclean", "25N"),
        Encounter("Loatheb", "25N"),
        Encounter("Instructor Razuvious", "25N"),
        Encounter("Gothik the Harvester", "25N"),
        Encounter("The Four Horsemen", "25N"),
        Encounter("Sapphiron", "25N"),
        Encounter("Kel'Thuzad", "25N"),
    ]
    OTHER = [
        Encounter("Archavon the Stone Watcher", "25N"),
    ]
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


if __name__ == "__main__":
    main()
