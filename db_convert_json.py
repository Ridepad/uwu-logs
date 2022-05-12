
folder = "WarmaneBossFights/tmp_cache"
name = "data_kills_3633-3634.json"

file = f"{folder}{name}"

import constants

data = constants.json_read(file)

print(data)