import json

with open('_DATA4.json') as f:
    data = json.load(f)


a = [f"21-{m:>02}" for m in range(1,13)]
a = ['22-01'] + a

new = {}
for x in a:
    new[x] = data[x]

with open("_DATA5.json", 'w') as f:
    json.dump(new, f)