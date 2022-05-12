import _main
import constants
import logs_player_class

PLAYERS = {}

def main():
    name = "22-04-27--21-02--Safiyah"
    report = _main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    # boss = "The Lich King"
    # s, f = enc_data[boss][-2]
    # logs = report.get_logs(s, f)
    players = report.get_players_guids()
    PLAYERS.update(players)
    classes = report.get_classes()
    # ud = report.useful_damage()
    report.format_attempts()
    sep = report.SEGMENTS_SEPARATED
    print(sep)
    # for x, y in specs.items():
        # print(f"{players[x]:<12} {y[0]}")


if __name__ == "__main__":
    main()