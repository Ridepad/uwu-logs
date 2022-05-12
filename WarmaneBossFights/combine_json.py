import json

from constants_WBF import read_json


def main(s):
    f = s+1
    d = {}
    
    z = read_json(f"./tmp_cache/data_kills_{s}-{f}")
    d.update(z)

    for x in range(s*10, f*10):
        name = f"data_kills_{x}-{x+1}"
        z = read_json(name)
        d.update(z)
    
    d = dict(sorted(d.items()))
    print("TOTAL REPORTS:", len(d))

    with open(f"data_kills_{s}-{f}.json", 'w') as j:
        json.dump(d, j)


if __name__ == "__main__":
    s = 331
    main(s)