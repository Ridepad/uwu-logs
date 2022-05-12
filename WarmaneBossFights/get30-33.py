import json

kill_json = "kill_json"

# 3012 3300

with open('kill_json/data_kills_30-31.json', 'r') as f:
    j: dict = json.load(f)

# j = {int(k):v for k,v in j.items()}

__data = {}
__siodfjmosdij = dict(sorted(j.items())[-1000:])
print(next(iter(__siodfjmosdij)))
def save_json(name, data):
    with open(name, 'w') as f:
        json.dump(data, f)
# for x in range(3299*1000, 3300*1000):
#     report_id = str(x)
#     if x in j:
#         __data[report_id] = j[report_id]
name = f'tmp_cache2/data_kills_{3099}-{3100}.json'
save_json(name, __siodfjmosdij)
# for report_id, data in j.items():
#     report_id = int(report_id)
#     # if report_id < 3012000: continue
#     if report_id % 1000 == 0:
#         if not __data: continue
#         rID = report_id // 1000
#         name = f'tmp_cache2/data_kills_{rID-1}-{rID}.json'
#         save_json(name, __data)
#         __data.clear()
#     __data[report_id] = data
