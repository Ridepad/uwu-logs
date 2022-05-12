from constants import running_time

import numpy

def to_perc(v, dur):
    applied, v = v
    return applied, v/dur*100000//1/1000

def find_trues(final):
    slices = numpy.ma.clump_masked(numpy.ma.masked_where(final, final))
    return [(s.start, s.stop - 1) for s in slices]

def to_ms_numpy(uptime: list):
    func = [numpy.zeros, numpy.ones]
    a = [func[applied](_length, dtype=int) for applied, _length in uptime]
    return numpy.concatenate(a)

def condense(trues, dur):
    condensed = []
    start = trues[0][0]
    if start != 0:
        condensed.append((False, start))
    
    for (s1,f1), (s2,f2) in zip(trues, trues[1:]):
        condensed.append((True, f1-s1+1))
        condensed.append((False, s2-f1-1))
    
    s, f = trues[-1]
    condensed.append((True, f-s+1))

    end = dur-f-1
    if end != 0:
        condensed.append((False, end))
    return condensed

def combine_targets(all_cases, dur):
    if not all_cases:
        return []
    final = numpy.zeros(dur, dtype=int)

    rounding_error = numpy.array([0,])
    for uptime in all_cases:
        c = to_ms_numpy(uptime)
        while 1:
            try:
                final = numpy.logical_or(final, c)
                break
            except ValueError:
                c = numpy.concatenate((c, rounding_error))
    try:
        trues = find_trues(final)
        return condense(trues, dur)
    except IndexError:
        print(all_cases)
        return []

def combine_by_guid(casts):
    q: dict
    new_casts = {}
    for guid, spells in casts.items():
        q = new_casts.setdefault(guid[:12], {})
        q.setdefault("targets", []).append(guid)
        for spell, uptime in spells.items():
            q.setdefault("spells", {}).setdefault(spell, []).append(uptime)
    return new_casts

def _sum(_list):
    return sum(x[1] for x in _list)

def sdikojfiosdjfio(uptimes):
    dur = max(_sum(uptime) for uptime in uptimes)
    for uptime in uptimes:
        diff = _sum(uptime) - dur
        if diff:
            print()
            print(uptime)
            applied, u = uptime.pop(-1)
            u = u + diff
            uptime.append((applied, u))
            print(uptime)
    return uptimes, dur

@running_time
def main(casts):
    new_casts = combine_by_guid(casts)
    spells_set = set()
    for id_ in new_casts:
        spells = new_casts[id_]['spells']
        for spell, uptimes in spells.items():
            uptimes, dur = sdikojfiosdjfio(uptimes)
            print("DUR:", dur)
            q = combine_targets(uptimes, dur)
            q = [to_perc(x, dur) for x in q]
            spells[spell] = q
            spells_set.add(spell)
    return new_casts, spells_set
