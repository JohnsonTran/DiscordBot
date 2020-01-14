import pymongo
from pymongo import MongoClient

#add a list of players and the time they won
#implement this into the game cog~~~

cluster = MongoClient('mongodb+srv://BOT_ACCESS:<BOT_ACCESS>@bot-by3ud.azure.mongodb.net/test?retryWrites=true&w=majority')
db = cluster["stats"]
collection = db["uno"]

def finish_game():
    collection.update(
        { _id: ObjectId("5e1d16d5df6dc71021b31c92")},
        { $inc: { total_games: 1 } } }
    )