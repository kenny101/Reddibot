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
bot = commands.Bot(command_prefix='send ', help_command=None)

async def getAvatar():
    urls = ['https://i.imgur.com/yaktK6q.png','https://i.imgur.com/PdY3IV3.png','https://i.imgur.com/0oOfHIZ.png','https://i.imgur.com/KZgbR05.png','https://i.imgur.com/lZXs1VD.png','https://i.imgur.com/7V8X8Xi.png','https://i.imgur.com/AzWPj5K.png','https://i.imgur.com/doXLlka.png','https://i.imgur.com/4dax7DZ.png','https://i.imgur.com/l1Kyki7.png','https://i.imgur.com/GukyDiR.png','https://i.imgur.com/rOTLBj0.png','https://i.imgur.com/fT7kVew.png','https://i.imgur.com/Rfpv0Tw.png','https://i.imgur.com/1DDuVTx.png','https://i.imgur.com/B9osUe6.png','https://i.imgur.com/R4MsMA1.png','https://i.imgur.com/30X6f8Y.png','https://i.imgur.com/4oJyL9W.png','https://i.imgur.com/8JXCIH1.png','https://i.imgur.com/am3I9Ov.png','https://i.imgur.com/3G5mEf9.png','https://i.imgur.com/7YCrnYa.png','https://i.imgur.com/pXKuptH.png','https://i.imgur.com/eUu3cvF.png','https://i.imgur.com/DJP5ife.png','https://i.imgur.com/8ObTBsp.png','https://i.imgur.com/98wHZjL.png','https://i.imgur.com/8AZ4Pnv.png','https://i.imgur.com/bFgbIcw.png']
    num =  random.randint(0,29)
    return urls[num]

@bot.command()
async def help(ctx):
    commands = "**Displays this message:**\n `send help` \n\n **Sends a random image from a subreddit:**\n `send me <name of a subreddit>` \n\n **Subscribe to receive new images from a subreddit:**\n `send more <name of a subreddit>` \n\n **Stop receiving images from a subreddit:**\n `send less <name of a subreddit>`\n\n\n > **[Add me to your server?](https://discord.com/oauth2/authorize?client_id=809958396585312266&scope=bot&permissions=0)**"
    embed = discord.Embed(title="**Reddibot's Commands List:**", description=commands, color=0x99a7f6)
    embed.set_image(url=await getAvatar())
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print('ready')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='"send help" for commands'))
    p = Process(target=await shiftPfp())

    # set daemon true to not have to wait for the process to join
    p.daemon = True
    p.start()



@bot.event
async def shiftPfp():
    while(True):
        try:
            num =  random.randint(0,500)
            fp = open('pfps/pfps_'+str(num)+'.png', 'rb')
            pfp = fp.read()
            await bot.user.edit(avatar=pfp)
            await asyncio.sleep(21600)
        except:
            await asyncio.sleep(500)


# check if the subreddit exists
async def sub_exists(sub:str):
    exists = True
    try:
        reddit.subreddits.search_by_name(sub, exact=True)
        for submission in reddit.subreddit(sub).top(limit=1):
            check = submission.url
    except NotFound:
        exists = False
    except:
        exists = False
    return exists


# add a subreddit to the database, if true add the sub, if false handdle it
def addSub(sub:str):
    sub = sub.lower() 
    db = cluster[sub]
    collection = db['posts']
    i = collection.count_documents({})


    for submission in reddit.subreddit(sub).top(limit=3000):
        try:
            if hasattr(submission, 'preview'):
                if submission.url.endswith('mp4') or submission.url.endswith('.gif') or submission.url.endswith('.gifv'):
                    post = {'ind': i ,'image': submission.url ,'source':"<https://reddit.com/" + submission.id+">", 'title': submission.title}
                    i = i + 1
                    collection.insert_one(post)
                else:
                    post = {'ind': i ,'image': submission.preview['images'][0]['resolutions'][3]['url'] ,'source':"<https://reddit.com/" + submission.id+">", 'title': submission.title}
                    i = i + 1
                    collection.insert_one(post)
        except:
            continue


# get a random image from a sub (source, image)
async def get_random_image(sub:str) -> tuple:
    sub = sub.lower()
    db = cluster[sub]
    collection = db['posts']
    randnum = random.randint(0,collection.count_documents({}))
    results = collection.find({"ind": randnum })

    try:
        for obj in results:
            sources = (obj['source'], obj['image'], obj['title'])
    except Exception as e:
        print('ERROR IN get_random_image: ' + e)
        return
    return sources


@bot.command(name='me', help='send a random image from a subreddit')
async def send_image(ctx, sub:str):
    sub = sub.lower()

    # check nsfw
    if reddit.subreddit(sub).over18 and ctx.channel.is_nsfw() == False:
        embed = discord.Embed(title='Subreddit is NSFW:', description="Whoops, this subreddit is NSFW. Please make sure that this channel is marked as NSFW first.", color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed, delete_after=20)
        return

    if await sub_exists(sub):
        db = cluster[sub]
        collection = db['posts']
        if collection.count_documents({}) > 0:
            source = await get_random_image(sub)

            embed = discord.Embed(title=source[2], description='[Source from r/' + sub + '](' + source[0] + ')', color=0x99a7f6 )
            embed.set_image(url=source[1])
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(title='Sending it soon!', description="I haven't heard of that subreddit before. I'll add it for you right now! :)", color=0x99a7f6)
            embed.set_image(url=await getAvatar())
            await ctx.send(embed=embed, delete_after=20)
            n = Process(target=addSub, args=(sub, ))
            n.daemon = True
            n.start()
            await asyncio.sleep(7)
            data = await get_random_image(sub)

            embed = discord.Embed(title=data[2], description='[Source from r/' + sub + '](' + data[0] + ')', color=0x99a7f6 )
            embed.set_image(url=data[1])
            await ctx.send(embed=embed)

    else:
        embed = discord.Embed(title='Invalid Subreddit:', description="Whoops, I don't think that is a subreddit. Please check your spelling", color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed, delete_after=20)

@bot.command(name='more', help='subscribe to a subreddit to get the newest posts (image posts only)')
async def subscribe(ctx, sub):
    if await sub_exists(sub):

        # check nsfw
        if reddit.subreddit(sub).over18 and ctx.channel.is_nsfw() == False:
            embed = discord.Embed(title='Subreddit is NSFW:', description="Whoops, this subreddit is NSFW. Please make sure that this channel is marked as NSFW first.", color=0x99a7f6)
            embed.set_image(url=await getAvatar())
            await ctx.send(embed=embed, delete_after=20)
            return

        db = cluster[sub]
        collection = db['new']
        check = db['subscribers']

        channel_id = str(ctx.message.channel.id)
        guild_id = str(ctx.message.guild.id)

        embed = discord.Embed(title='One moment please', color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed, delete_after=20)

        # check if subbed already
        checkIfSub = check.count_documents({"channel_id": channel_id})

        if checkIfSub > 0:
            embed = discord.Embed(title='Duplicate Subscription!', description="Whoops, It looks like you are already subscribed to this subreddit.", color=0x99a7f6)
            embed.set_image(url=await getAvatar())
            await ctx.send(embed=embed, delete_after=20)
            return


        if await updateTotalSubs(guild_id, channel_id, sub) == False:
            embed = discord.Embed(title='Max Subcriptions:', description="Whoops, you can only subscribe to at most 10 subreddits per channel. Please remove one and try again!", color=0x99a7f6)
            embed.set_image(url=await getAvatar())
            await ctx.send(embed=embed, delete_after=20)

            #subscribe to the sub
        else:
                embed = discord.Embed(title='Success!', description="I've subscribed to r/" + str(sub) + " for you. You'll receive images from " + str(sub) + " from now on. To unsubscribe type: send less <subreddit name>" , color=0x99a7f6)
                embed.set_image(url=await getAvatar())
                await ctx.send(embed=embed, delete_after=20)
                return
    else:
        embed = discord.Embed(title='Invalid Subreddit:', description="Whoops, I don't think that is a subreddit. Please check your spelling", color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed)







# update total subs, return true if updated, false if max capacity 
async def updateTotalSubs(guild_id, channel_id, sub):
    db = cluster[sub]
    collection = db['subscribers']

    userDb = cluster['userData']
    userCollection = userDb['guild_id']

    guild = str(guild_id)
    channel = str(channel_id)

    total_guilds = userCollection.count_documents({"guild_id": guild})

    # get the total subs:
    if total_guilds != 0:
        results = userCollection.find({"guild_id": guild})
        for guild in results:
            total = int(guild['total_subs'])

    #if first time subscribing
    if total_guilds == 0:
        post = {'channel_id': channel}
        collection.insert_one(post)

        post = {"guild_id": guild, "total_subs": 1}
        userCollection.insert_one(post)

    # if reached max subs
    elif total > 10:
        return False
    else:
        total = total + 1
        userCollection.delete_one({"guild_id": str(guild_id) })        
        post = {"guild_id": str(guild_id), "total_subs": total}
        userCollection.insert_one(post)

        post = {'channel_id': channel_id}
        collection.insert_one(post)

    return True


@bot.command(name='less', help='unsubcribe a subreddit.')
async def unsubscribe(ctx, sub):
    channel_id = str(ctx.message.channel.id)
    guild_id = str(ctx.message.guild.id)

    db = cluster[sub]
    collection = db['subscribers']

    userDb = cluster['userData']
    userCollection = userDb['guild_id']


    checkIfSub = collection.count_documents({"channel_id": channel_id})
    if checkIfSub == 0:
        embed = discord.Embed(title='Not Subscribed:', description="Whoops, I don't think you are subscribed to this subreddit. Please check your spelling", color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed)
        return

        # else unsub
    else:
        results = userCollection.find({"guild_id": guild_id})
        for guild in results:
            total = int(guild['total_subs'])

        # decrement from subscriber
        collection.delete_one({"channel_id": channel_id })

        # in case a guild no longer wants to receive subreddit updates:
        if total == 1:
            userCollection.delete_one({"guild_id": guild_id, "total_subs": total })
            embed = discord.Embed(title='Success!', description="You will no longer receive images from r/" + str(sub), color=0x99a7f6)
            embed.set_image(url=await getAvatar())
            await ctx.send(embed=embed, delete_after=20)
            return


        userCollection.delete_one({"guild_id": guild_id})
        total = total - 1
        post = {"guild_id": guild_id, "total_subs": total}
        userCollection.insert_one(post)

        embed = discord.Embed(title='Success!', description="You will no longer receive images from r/" + str(sub), color=0x99a7f6)
        embed.set_image(url=await getAvatar())
        await ctx.send(embed=embed, delete_after=20)


bot.run(TOKEN)

