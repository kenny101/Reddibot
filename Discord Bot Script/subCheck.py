import pymongo
from pymongo import MongoClient
import praw
from prawcore import NotFound
import random
import discord
from discord.ext import commands
import asyncio
from multiprocessing import Process


# put your mongoDB client bellow
cluster = MongoClient("your mongoDB client here")


# put your reddit client_id and client_secret bellow
reddit = praw.Reddit(
    client_id="put your reddit client_id here",
    client_secret="put your client_secret here",
    user_agent="your-user-agent-here",
    check_for_async=False
)


# put your discord bot token bellow
TOKEN = 'your discord bot token goes here'
intents = discord.Intents.default()
intents.members = True
client = discord.Client()

@client.event
async def on_ready():
    print('Subchecker is ready')
    p = Process(target=await checkSubreddits())
    p.daemon = True
    p.start()



async def checkSubreddits():
    while True:
        try:
            await asyncio.sleep(10)
            for sub in cluster.list_database_names():
                if sub == 'userData' or sub == 'admin' or sub == 'local':
                    continue  
                db = cluster[sub]

                collection_subs = db['subscribers']
                # if the sub has subscribers
                if collection_subs.count_documents({}) > 0:
                    collection = db['new']
                    newestSubSource = str((await getNewestSub(sub))[1])

                    # if item count is 0, remove and update to the newest subreddit
                    if await checkIfSourceExists(sub, newestSubSource) == False:
                        collection.delete_one({})
                        post = {'image': (await getNewestSub(sub))[0] ,'source': (await getNewestSub(sub))[1], 'title': (await getNewestSub(sub))[2]}
                        collection.insert_one(post)
                        await sendToSubscribers(sub)
        except Exception as e:
            print('ERROR in check_subreddits: ' + str(e))
            continue

async def checkIfSourceExists(sub, link):
    db = cluster[sub]
    collection = db['new']
    item_count = collection.count_documents({"source": link})
    if item_count == 0:
        return False
    
    return True

# if there was a newest post, call this function to send to the subscribers
async def sendToSubscribers(sub):
    #loop through subs
    db = cluster[sub]
    collection = db['new']
    subscribers = db['subscribers']

    # loop through channel ids
    try:
        for _id in subscribers.find():
            ch_id = int(_id['channel_id'])
            #send the data
            for data in collection.find():
                channel = client.get_channel(ch_id)

                results = collection.find()
                for obj in results:
                    data = (obj['source'], obj['image'], obj['title'])
                
                url = data[0][1:len(data[0])]

                embed = discord.Embed(title=data[2], description='[Source from r/' + sub + '](' + url + ')', color=0x99a7f6 )
                embed.set_image(url=data[1])
                await channel.send(embed=embed)
                break

    # if the channel id was removed, remove the channel id, and decrement total subs
    except AttributeError:
        print('Attribute error: channel was possibly deleted. at sub: ' +  str(sub) + ' with id: ' + str(ch_id))

        # remove channel id
        subscribers.delete_one({"channel_id": str(ch_id) })

async def getNewestSub(sub):
    for submission in reddit.subreddit(sub).new(limit=100):
        try:
            if hasattr(submission, 'preview'):
                if submission.url.endswith('mp4') or submission.url.endswith('.gif') or submission.url.endswith('.gifv'):
                    # post = {'image': submission.url ,'source': newestSubSource, 'title': submission.title}
                    post = [str(submission.url), str("<https://reddit.com/" + submission.id+">"), str(submission.title)]
                    str("sub: <https://reddit.com/" + submission.id+">")
                    return post
                else:
                    post = [str(submission.preview['images'][0]['resolutions'][3]['url']), str("<https://reddit.com/" + submission.id+">"), str(submission.title)]
                    return post      
        except IndexError:
                continue
    print("Error: none was returned")
    return "none"

client.run(TOKEN)