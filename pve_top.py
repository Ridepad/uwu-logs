import dmg_useful
import _main


def do(report, boss_name):
    _diff = report.get_difficulty()
    lk = _diff[boss_name]
    for n, (_mode, is_kill) in enumerate(lk):
        if is_kill:
            return n, _mode

def main():
    boss_name = "The Lich King"
    name = '21-10-01--21-07--Safiyah'
    report = _main.THE_LOGS(name)
    enc_data = report.get_enc_data()
    if 
    q = do(report, boss_name)
    if not q:
        return
    attempt, mode = q
main()