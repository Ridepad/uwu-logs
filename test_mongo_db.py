from pymongo import MongoClient

# Requires the PyMongo package.
# https://api.mongodb.com/python/current

CONNECTION_STRING = 'mongodb+srv://Ridepad:MakakMetumtam00@cluster0.rlcu6.mongodb.net/test?authSource=admin&replicaSet=atlas-xw4k29-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true'

client = MongoClient(CONNECTION_STRING)
filter={
    'names': {
        '$elemMatch': {
            '$eq': 'Weeds'
        }
    }
}

result = client['KillsDB']['BruhIDK'].find(
  filter=filter
)
for item in result:
    print(item)
# print(repr(result))