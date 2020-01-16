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
        { $inc: { total_games: 1 } },
        { $set: {last_played: Date()} }
    )

'''
def add_winner(discord_id):
    collection.update(
        { _id: ObjectId("5e1d16d5df6dc71021b31c92")},
        {$inc: winners[{discord_id: 1}] },
        {upsert: true}
    )
    BUGFIXING THIS, LOOK AT BOTTOM'''

#probably need to format this since discord should display BSON
def get_stats(): 
    collection.find(_id: ObjectId("5e1d16d5df6dc71021b31c92")).pretty()


    #currently only sets, needs to inc
    db.uno.update({ _id: ObjectId("5e1d16d5df6dc71021b31c92")},
        {winners: [ {GruntyBunty: 1} ]},
        {upsert: true}   
    )

       db.uno.update({ _id: ObjectId("5e1d16d5df6dc71021b31c92")},
        {$inc:{"winners.GruntyBunty": 1}},
        {upsert: true}
    )
   