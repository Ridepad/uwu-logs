from collections import defaultdict
from typing import TypedDict

import logs_base
from h_debug import running_time
from h_other import (
    sort_dict_by_value,
    separate_thousands,
    separate_thousands_dict,
)


REDUCED_KEYS = {"OVERKILL", "OVERHEAL", "ABSORBED", "RESISTED", "GLANCING", "BLOCKED"}

HIT_TYPE = ["spells_hit", "spells_crit", "dot_hit", "dot_crit"]
PERIODIC = {'SPELL_PERIODIC_DAMAGE', 'SPELL_PERIODIC_HEAL'}
FLAGS_DAMAGE = {
    "SPELL_DAMAGE",
    "SWING_DAMAGE",
    "RANGE_DAMAGE",
    "DAMAGE_SHIELD",
    "SPELL_PERIODIC_DAMAGE",
}

class BreakdownType(TypedDict):
    ACTUAL: defaultdict[str, defaultdict[str, defaultdict[str, int]]]
    HITS: defaultdict[str, defaultdict[str, defaultdict[str, defaultdict[str, list[int]]]]]
    OTHER: defaultdict[str, defaultdict[str, defaultdict[str, defaultdict[str, int]]]]
    MISSES: defaultdict[str, defaultdict[str, defaultdict[str, defaultdict[str, int]]]]


class BreakdownTypeExtended(BreakdownType):
    SPELLS: dict[str, dict[str, str]]
    TARGETS: set[str]


def total_detailed(d: dict[str, dict[str, int]]):
    total = defaultdict(int)
    detailed = defaultdict(dict)
    for spell_id, type_data in d.items():
        for _type, value in type_data.items():
            total[spell_id] += value
            detailed[spell_id][_type] = value
    return total, detailed

def detailed_sort_separate_thousands(d: dict):
    return {
        t: separate_thousands_dict(sort_dict_by_value(v))
        for t, v in d.items()
    }
    
def get_avgs(hits: list):
    if not hits:
        return "", []

    hits = sorted(hits)
    _len = len(hits)
    len10 = _len//10 or 1
    len50 = _len//2 or 1
    avgs = [
        sum(hits) // _len,
        max(hits),
        sum(hits[-len10:]) // len10,
        sum(hits[-len50:]) // len50,
        sum(hits[:len50]) // len50,
        sum(hits[:len10]) // len10,
        min(hits),
    ]
    avg, *other = map(separate_thousands, avgs)
    return avg, other

def format_percent(hit, crit):
    if crit == 0:
        return ""
    percent = crit/(hit+crit)*100
    percent = separate_thousands(percent)
    return f"{percent}%"

def format_hits_data(hits, crits):
    hits_count = len(hits)
    crits_count = len(crits)
    percent = format_percent(hits_count, crits_count)
    hit_avg, hits_avg = get_avgs(hits)
    crit_avg, crits_avg = get_avgs(crits)
    return {
        "total": separate_thousands(hits_count+crits_count),
        "hits": separate_thousands(hits_count),
        "crits": separate_thousands(crits_count),
        "percent": percent,
        "hit_avg": hit_avg,
        "hits_avg": hits_avg,
        "crit_avg": crit_avg,
        "crits_avg": crits_avg,
    }

def format_hits(hits: dict[str, list[int]]):
    hit_hit, hit_crt, dot_hit, dot_crt = [hits.get(x, []) for x in HIT_TYPE]
    return {
        "HIT": format_hits_data(hit_hit, hit_crt),
        "DOT": format_hits_data(dot_hit, dot_crt),
    }

def hits_data(data: dict[int, dict[str, list[int]]]):
    return {spell_id: format_hits(hits) for spell_id, hits in data.items()}


def default_dict() -> BreakdownType:
    actual = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    hits = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    other = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    misses = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

    return {
        "ACTUAL": actual,
        "HITS": hits,
        "OTHER": other,
        "MISSES": misses,
    }

@running_time
def _damage(logs_slice: list[str]) -> BreakdownType:
    d = default_dict()
    actual = d["ACTUAL"]
    hits = d["HITS"]
    other = d["OTHER"]
    misses = d["MISSES"]

    for line in logs_slice:
        if "DAMAGE" not in line:
            continue
        _, flag, etc = line.split(',', 2)
        if flag not in FLAGS_DAMAGE:
            continue
        
        sGUID, _, tGUID, _, spell_id, _, _, dmg, over, _, res, _, absrb, crit, glanc, _ = etc.split(',', 15)
        _value = int(dmg)
        
        _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
        hits[sGUID][tGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        
        _other = other[sGUID][tGUID][spell_id]
        
        if over != "0":
            _over = int(over)
            _value = _value - _over
            _other["OVERKILL"] += _over
        actual[sGUID][tGUID][spell_id] += _value

        if res != "0":
            _other["RESISTED"] += int(res)
        if absrb != "0":
            _other["ABSORBED"] += int(absrb)
        if glanc == "1":
            _other["GLANCED"] += int(_value/3)
            misses[sGUID][tGUID][spell_id]["GLANCING"] += 1

    return d
        

@running_time
def _heal(logs_slice: list[str]) -> BreakdownType:
    d = default_dict()
    actual = d["ACTUAL"]
    hits = d["HITS"]
    other = d["OTHER"]
    
    for line in logs_slice:
        if "_HEAL" not in line:
            continue
        
        _, flag, sGUID, _, tGUID, _, spell_id, _, _, heal, over, _, crit = line.split(',', 12)
        _value = int(heal)

        _hit_type = (flag in PERIODIC) * 2 + (crit == "1")
        hits[sGUID][tGUID][spell_id][HIT_TYPE[_hit_type]].append(_value)
        
        if over != "0":
            _over = int(over)
            _value = _value - _over
            other[sGUID][tGUID][spell_id]["OVERHEAL"] += _over
        actual[sGUID][tGUID][spell_id] += _value

    return d

@running_time
def _cast(logs_slice: list[str]):
    casts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for line in logs_slice:
        if "_CAST" not in line:
            continue
        
        _, _, sGUID, _, tGUID, _, spell_id, _ = line.split(',', 7)

        casts[sGUID][tGUID][spell_id] += 1

    return casts

@running_time
def _miss(logs_slice: list[str]) -> BreakdownType:
    d = default_dict()
    other = d["OTHER"]
    misses = d["MISSES"]
    
    for line in logs_slice:
        if "_MISSED" not in line:
            continue
        
        _, _, sGUID, _, tGUID, _, spell_id, *more = line.split(',')
        try:
            v = int(more[-1])
            type = more[-2]
            _type = f"{type}ED"
            other[sGUID][tGUID][spell_id][_type] += v
        except ValueError:
            type = more[-1]
        misses[sGUID][tGUID][spell_id][type] += 1

    return d

def format_total_data(data: dict):
    data["Total"] = sum(data.values())
    return separate_thousands_dict(data)

def format_percentage(v, total):
    if not total:
        total = 1
    return f"{(v / total * 100):.1f}%"

def sort_by_name_type(targets: set[str]):
    _targets = list(targets)
    _targets.sort(key=lambda x: x[:3] == "0x0")
    _targets.sort(key=lambda x: x[:5] == "0xF14")
    return _targets

def _return_dict():
    casts = defaultdict(int)
    actual = defaultdict(int)
    hits = defaultdict(lambda: defaultdict(list))
    other = defaultdict(lambda: defaultdict(int))
    misses = defaultdict(lambda: defaultdict(int))

    return {
        "ACTUAL": actual,
        "HITS": hits,
        "OTHER": other,
        "MISSES": misses,
        "CASTS": casts,
    }

class SourceNumbers(logs_base.THE_LOGS):
    def conv_spell_id(self, spell_id: str, source_guid=None):
        self.SPELL_DATA = {}
        spell_id = self.convert_to_main_spell_id(spell_id)
        if source_guid:
            source_id = source_guid[6:-6]
            if source_id != "000000":
                return f"{spell_id}--{source_id}"
        return spell_id
    
    @logs_base.cache_wrap
    def numbers_damage(self, s, f):
        logs_slice = self.LOGS[s:f]
        return _damage(logs_slice)
    @logs_base.cache_wrap
    def numbers_heal(self, s, f):
        logs_slice = self.LOGS[s:f]
        return _heal(logs_slice)
    @logs_base.cache_wrap
    def numbers_cast(self, s, f):
        logs_slice = self.LOGS[s:f]
        return _cast(logs_slice)
    @logs_base.cache_wrap
    def numbers_miss(self, s, f):
        logs_slice = self.LOGS[s:f]
        return _miss(logs_slice)

    @staticmethod
    def combine_values(data, new_data):
        for key, value in new_data.items():
            data[key] += value

    def add_other(self, data, new_data):
        for sGUID, targets in new_data.items():
            for tGUID, spells in targets.items():
                for spell_id, v in spells.items():
                    self.combine_values(data[sGUID][tGUID][spell_id], v)

    def add_actual(self, data, new_data):
        for sGUID, targets in new_data.items():
            for tGUID, spells in targets.items():
                self.combine_values(data[sGUID][tGUID], spells)

    def combine_dict(self, data, new_data):
        self.add_actual(data["ACTUAL"], new_data["ACTUAL"])
        for k in ["HITS", "OTHER", "MISSES"]:
            self.add_other(data[k], new_data[k])

    def _actual(self, actual_sum: dict[str, int]):
        ACTUAL_FORMATTED = format_total_data(actual_sum)
        actual_total = actual_sum['Total'] or 1
        ACTUAL_PERCENT =  {
            spell_id: format_percentage(value, actual_total)
            for spell_id, value in actual_sum.items()
        }

        return {
            "ACTUAL": ACTUAL_FORMATTED,
            "ACTUAL_PERCENT": ACTUAL_PERCENT,
        }
    
    def _reduced(self, actual_sum, other):
        reduced_total, reduced_detailed = total_detailed(other)
        reduced_detailed = detailed_sort_separate_thousands(reduced_detailed)
        reduced_formatted = format_total_data(reduced_total)
        reduced_percent = {
            spell_id: format_percentage(value, value + actual_sum.get(spell_id, 0))
            for spell_id, value in reduced_total.items()
        }

        return {
            "REDUCED": reduced_formatted,
            "REDUCED_PERCENT": reduced_percent,
            "REDUCED_DETAILED": reduced_detailed,
        }

    def _misses(self, misses):
        misses_total, misses_detailed = total_detailed(misses)
        misses_detailed = detailed_sort_separate_thousands(misses_detailed)
        misses_total = format_total_data(misses_total)
        return {
            "MISSES": misses_total,
            "MISS_DETAILED": misses_detailed,
        }

    def _get_spell_data(self, spell_id: str):
        source_guid = None
        if '--' in spell_id:
            spell_id, source_guid = spell_id.split('--')
        
        spell_id_int = abs(int(spell_id))
        spell_data = self.SPELLS[spell_id_int].to_dict()
        
        if source_guid and source_guid != "000000":
            pet_name = self.guid_to_name(source_guid)
            spell_data['name'] = f"{spell_data['name']} ({pet_name})"

        return spell_data

    def _order_spells(self, rd):
        actual_sum = rd["ACTUAL"]
        spell_ids = set(actual_sum) | set(rd["OTHER"]) | set(rd["CASTS"]) | set(rd["MISSES"])
        spell_ids = sorted(spell_ids)
        spell_ids = sorted(spell_ids, key=lambda x: actual_sum.get(x, 0), reverse=True)
        print(spell_ids)
        return {
            spell_id: self._get_spell_data(spell_id)
            for spell_id in spell_ids
        }

    def _order_targets(self, all_targets: set[str]):
        t = {
            guid: self.guid_to_name(guid)
            for guid in all_targets
        }
        t = dict(sorted(t.items(), key=lambda x: x[1]))
        t2 = {}
        for guid in sort_by_name_type(t):
            target_id = guid if guid.startswith("0x0") else guid[6:-6]
            t2[target_id] = t[guid]
        return t2
    
    def _filter_sources(self, data: dict[str, dict], guids):
        if type(guids) == set:
            for guid, values in data.items():
                if guid not in guids:
                    continue
                yield guid, values
        elif type(guids) == str:
            for guid, values in data.items():
                if guids not in guid:
                    continue
                yield guid, values
        else:
            for guid, values in data.items():
                yield guid, values

    def _filter(self, a: BreakdownType, sources_filter: set[str], target_filter: str=None):
        all_targets = set()
        pets_in_slice = set()

        d = _return_dict()
        for k, sources in a.items():
            for source_guid, targets in self._filter_sources(sources, sources_filter):
                all_targets.update(targets)
                pets_in_slice.add(source_guid)
                for target_guid, spells in self._filter_sources(targets, target_filter):
                    for spell_id, vv in spells.items():
                        spell_id_full = self.conv_spell_id(spell_id, source_guid)
                        if k in ["ACTUAL", "CASTS"]:
                            d[k][spell_id_full] += vv
                            continue
                        for _type, vvv in vv.items():
                            d[k][spell_id_full][_type] += vvv

        d["PETS"] = pets_in_slice
        d["TARGETS"] = all_targets
        return d

    def _format_pets(self, pets, taken=False):
        d = {}
        for guid in sorted(pets):
            if guid[:3] == "0x0":
                continue
            d[guid] = self.guid_to_name(guid[6:12])
        return d

    def _format(self, d: dict):
        d["HITS"] = hits_data(d["HITS"])
        d["PETS"] = self._format_pets(d["PETS"])
        d["TARGETS"] = self._order_targets(d["TARGETS"])
        d["HITS_DATA"] = separate_thousands_dict(d["HITS"])
        d["CASTS"] = separate_thousands_dict(d["CASTS"])
        d["SPELLS_DATA"] = self._order_spells(d)
        actual_sum = d["ACTUAL"]
        other = d["OTHER"]
        d.update(self._actual(actual_sum))
        d.update(self._reduced(actual_sum, other))
        d.update(self._misses(d["MISSES"]))
        return d

    @running_time
    def numbers_combined(self, segments: list[str, str], heal=False):
        combined = default_dict()
        casts_combined = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        combined["CASTS"] = casts_combined
        for s, f in segments:
            if heal:
                dmgheal = self.numbers_heal(s, f)
            else:
                dmgheal = self.numbers_damage(s, f)
            self.combine_dict(combined, dmgheal)
            misses = self.numbers_miss(s, f)
            self.combine_dict(combined, misses)
            casts = self.numbers_cast(s, f)
            self.add_actual(casts_combined, casts)
        return combined

def _test1():
    n = "23-02-10--21-00--Safiyah--Lordaeron"
    report = SourceNumbers(n)
    # s, f = report.ENCOUNTER_DATA["Rotface"][-1]
    # logs_slice = report.LOGS[s:f]
    segments = report.ENCOUNTER_DATA["Rotface"]
    report.LOGS
    for _ in range(10):
        print()
        d = report.numbers_combined(segments)

    s = set(['0x060000000054682E', '0x06000000003AC5F3', '0x06000000005992AB', '0xF130008F13000428', '0x06000000004B2086', '0x060000000057C2BB', '0x06000000002D47FB', '0x0600000000238FF1', '0x06000000000314D5', '0x0600000000353204', '0x06000000002795F1', '0x06000000001D5C6E', '0x0600000000540445', '0x0000000000000000', '0x06000000005410C6', '0x06000000003F9E49', '0xF1400EF6F3000027', '0x06000000004E2F01', '0x060000000044D28B', '0xF14008FB8E000023', '0x06000000005907E1', '0x0600000000588CE6', '0x060000000023EEB1', '0xF1401CD81C000024', '0x060000000060ED5D', '0x0600000000462207', '0xF1300007AC00054A', '0xF14006A3AC000026', '0xF1300007AC000549', '0xF1401ABD72000025', '0xF1300007AC000548', '0xF1300079F000054D', '0xF1300079F000054C', '0xF1300079F000054E', '0xF1300079F0000551', '0xF1300079F0000550', '0xF1300079F0000552', '0xF130006CB500055B', '0x06000000004EE87E', '0x060000000061945A', '0xF130009021000565', '0xF130004CD4000567', '0xF130009023000569', '0xF150008F460004D8', '0x0600000000320EBF', '0xF13000902100056F', '0xF13000902100057B', '0xF130004CD400057C', '0xF130009021000580', '0xF13000902100058B', '0xF130004CD40005A5', '0xF1300090210005AC', '0xF1300090210005AE', '0xF1300090230005B0', '0xF1300090210005B5', '0xF1300090210005BF', '0xF1300090210005C1', '0xF1300090210005DB', '0xF130006CB50005DC', '0xF1300090230005E3', '0xF1300090210005E5', '0xF130004CD40005E9', '0xF1300090210005EA', '0x060000000040B832', '0xF1300090210005ED'])
    print(set(d["ACTUAL"].keys()) == s)

if __name__ == "__main__":
    _test1()
