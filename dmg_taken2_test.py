import _main
import dmg_heals2

def add_space(v):
    return f"{v:,}".replace(',', ' ')

def sort_dict_by_value(data: dict):
    return sorted(data.items(), key=lambda x: x[1], reverse=True)

def main1(name):
    z = {'0x06000000001DC33A': 21341568, '0x0600000000091368': 5227463, '0x0600000000127095': 5554626, '0x0600000000136922': 4947105, '0x06000000004AD68F': 4068022, '0x0600000000318855': 3830782, '0x06000000003BDAF4': 22077823, '0x06000000004486DF': 3587202, '0x060000000027D240': 6296658, '0x0600000000409678': 4467865, '0x06000000003E0A55': 5469847, '0x06000000001FE874': 6359179, '0x0600000000293503': 5639266, '0x060000000048BED2': 4042128, '0x060000000041D299': 6258192, '0x060000000002CCBC': 4219565, '0x0600000000309CE7': 3775896, '0x06000000003FC4CA': 5906989, '0x06000000003D1BE6': 4044280, '0x060000000021D3D1': 3853204, '0x06000000001DB98E': 5923248, '0x060000000037C227': 4286517, '0x0600000000479FBA': 3839625, '0x06000000003B5680': 3477320, '0x0600000000478498': 2919871}
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guid = '0x06000000001DC33A'
    dmg = dmg_heals2.dmg_taken_guid(logs, guid)
    # dmg = {report.guid_to_name(guid): value for guid, value in dmg}
    assert dmg == z[guid]
    # for guid, value in dmg:
    #     name = report.guid_to_name(guid)
    #     value = add_space(value)
    #     print(f"{name:<12}{value:>12}")


def main2(name):
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guid = '0xF13'
    guid = '0x06'
    dmg = dmg_heals2.dmg_taken_fast(logs, guid)
    new_data = {}
    for guid, value in dmg.items():
        # guid = report.get_master_guid(guid)
        name = report.guid_to_name(guid)
        new_data[name] = new_data.get(name, 0) + value
    new_data = sort_dict_by_value(new_data)

    # for name, value in new_data:
    #     value = add_space(value)
    #     print(f"{name:<30}{value:>12}")


def main3(name):
    report = _main.THE_LOGS(name)
    logs = report.get_logs()
    guid = '0xF13'
    # guid = '0x06'
    dmg = dmg_heals2.parse_dmg_taken(logs, guid)
    new_data = {}
    for tguid, sources in dmg.items():
        name = report.guid_to_name(tguid)
        q = new_data.setdefault(name, {})
        for sguid, value in sources.items():
            sguid = report.get_master_guid(sguid)
            q[sguid] = q.get(sguid, 0) + value
    print(new_data.keys())
    d = new_data['Shambling Horror']
    d = sort_dict_by_value(d)
    for tguid, value in d:
        name = report.guid_to_name(tguid)
        value = add_space(value)
        print(f"{name:<30}{value:>12}")

if __name__ == "__main__":
    name = '21-07-22--21-30--Inia'
    main3(name)