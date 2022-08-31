import os
import discord
from discord import Spotify
from discord.utils import get
import random
import tracemalloc
import re
import datetime
import sqlite3
from youtube_search import YoutubeSearch
from apiclient.discovery import build
from datetime import timedelta

tracemalloc.start()

## Global variables

TOKEN = '#'
GUILD = 'bot test'
bannedWords = ['windows', 'facebook']
LOGID = 782211095359127572
SHOPID = 784093257264791602
COMMANDSID = 782717630939267142
intent = discord.Intents.all()
conn = sqlite3.connect('userinfo.db')
c = conn.cursor()
SHOPMSGID = 787391319722033152
gimageskey = '#'
GAMESID = 788119730530811995
cxkey = '#'
service = build("customsearch", "v1",
               developerKey=gimageskey)

##
priceDict = {}
roleFile = open('roles.txt', 'r+')
x = 0 
emojilist = ['🔴', '🟠','🟡','🟢','🌲','🔵','🐋','🟣','⚪','⚫']
for line in roleFile.readlines():
    priceDict[hex(ord(emojilist[x]))] = [int(line.split('/:/')[1]),'_'.join(line.split('/:/')[0].lower().split(' '))]
    x+=1
#print(priceDict)
##

client = discord.Client(intents = intent)

## Event handling

@client.event
async def on_ready():
    print(f'{client.user} is connected!')

    #await shopMessage()

@client.event
async def on_member_join(member):
    try:
        c.execute('INSERT OR REPLACE INTO users VALUES (?,0,0)',(member.id,))
        c.execute('INSERT INTO roles VALUES (?,0,0,0,0,0,0,0,0,0,0)',(member.id,))
    except Error as e:
        print(e)
    conn.commit()
    dm = await member.create_dm()
    await dm.send(f'Welcome to my server, {member.display_name}. I hope you have a pleasant stay')

@client.event
async def on_member_remove(member):
    try:
        c.execute('DELETE FROM users WHERE USERID=?',(member.id,))
        c.execute('INSERT FROM roles WHERE USERID=?',(member.id,))
    except Error as e:
        print(e)
    conn.commit()

@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == SHOPMSGID:
        shop_channel = client.get_channel(SHOPID)
        emoji = hex(ord(payload.emoji.name))

        x = c.execute('SELECT * FROM roles WHERE USERID=?',(payload.user_id,)).fetchall()
        credit = c.execute('SELECT * FROM users WHERE USERID=?',(payload.user_id,)).fetchall()[0][1]

        userRoleDict = {}
        for i in range(len(priceDict.keys())):
            userRoleDict[list(priceDict.keys())[i]] = x[0][1:][i]
        
        userHas,rolePrice,roleName = userRoleDict[emoji],priceDict[emoji][0],priceDict[emoji][1]

        if userHas == 1:
            return
        else:
            if credit < rolePrice:
                await(await shop_channel.send(f"`You don't have enough credits to buy this role! Price = {rolePrice}, Balance = {credit}.`")).delete(delay=6)
            else:
                newCredit = credit - rolePrice
                c.execute(f'UPDATE roles SET {roleName}=1 WHERE USERID=?',(payload.user_id,))
                c.execute(f'UPDATE users SET CREDITS=? WHERE USERID=?',(newCredit,payload.user_id,))
                conn.commit()

                receipt = discord.Embed(title='RECEIPT', description='Thank you for your purchase!', color=0x4287f5)
                receipt.add_field(name='ITEM:', value = ' '.join(roleName.split('_')).capitalize(), inline = False)
                receipt.add_field(name='PRICE:', value = f'{rolePrice} credits', inline= False)
                receipt.add_field(name='BALANCE AFTER TRANSACTION:', value = f'{newCredit} credits', inline= False)
                receipt.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=payload.member.avatar_url)
                dm = await payload.member.create_dm()
                await dm.send(embed=receipt)
        
@client.event
async def on_message_edit(before, after):
    log_channel = client.get_channel(LOGID)
    if before.author == client.user:
        return
    embed = discord.Embed(title='Edit', description=before.author.name, color=0x4287f5)
    embed.add_field(name='Description:', value=f'`{before.author.name}` edited a message in `{before.channel}`')
    embed.add_field(name = 'Before:', value = f'`{before.content}`', inline= False)
    embed.add_field(name= 'After:', value = f'`{after.content}`', inline = False)
    embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=before.author.avatar_url)
    await log_channel.send(embed=embed)

    await badCheck(after)

@client.event
async def on_message_delete(message):
    log_channel = client.get_channel(LOGID)
    if message.author == client.user:
        return
    embed = discord.Embed(title='Edit', description=message.author.name, color=0x4287f5)
    embed.add_field(name='Description:', value=f'`{message.author.name}` deleted a message in `{message.channel}`')
    embed.add_field(name = 'Full message:', value = f'`{message.content}`', inline= False)
    embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=message.author.avatar_url)
    await log_channel.send(embed=embed)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    #for member in message.guild.members:
    #    c.execute('INSERT INTO users VALUES (?,0,0)',(member.id,))
    #    c.execute('INSERT INTO roles VALUES (?,0,0,0,0,0,0,0,0,0,0)',(member.id,))
    #conn.commit()

    await badCheck(message)

    if message.content[0] == '!' and message.content[1] != '!':
        split_msg = message.content[1:].split()
        command = split_msg[0]
        arguments = ' '.join(split_msg[1:])

        adminCommands = ['clear', 'kick', 'ban', 'mute']
        commandchannelCommands = ['repeat', 'select', 'balance','daily']
        games = ['trivia', 'answer']

        if not get(message.guild.roles, id = 782211126670262343) in message.author.roles and command in adminCommands:
            await (await message.channel.send("You can't execute this command.")).delete(delay=5)
            return
        elif not get(message.guild.roles, id = 782211126670262343) in message.author.roles and command in commandchannelCommands and message.channel == client.get_channel(COMMANDSID):
            await (await message.channel.send("Please use the commands channel for commands!.")).delete(delay=5)
            return
        elif not get(message.guild.roles, id = 782211126670262343) in message.author.roles and command in games and message.channel == client.get_channel(GAMESID):
            await (await message.channel.send("Please use the games channel for games!.")).delete(delay=5)
            return

        if command == 'repeat':
            await repeatCommand(message, arguments)
        elif command == 'roll':
            await diceCommand(message, arguments)
        elif command == 'clear':
            await clearCommand(message, arguments)
        elif command == 'spotify':
            await spotifyCommand(message, arguments)
        elif command == 'select':
            await selectCommand(message,arguments)
        elif command == 'balance':
            await balanceCommand(message)
        elif command == 'youtube' or command == 'yt':
            await youtubeCommand(message,arguments)
        elif command == 'image' or command == 'img':
            await imageCommand(message,arguments)
        elif command == 'daily':
            await dailyCommand(message)
        elif command == 'mute':
            await muteCommand(message,arguments)
        elif command == 'unmute':
            await unmuteCommand(message,arguments)
        elif command == 'trivia':
            await triviaCommand(message)
        elif command == 'answer':
            await answerCommand(message,arguments)
        else:
            await(await message.channel.send('Please enter a valid command.')).delete(delay=5)
            return
        
        print(f'{command} successfully executed')
    elif message.content[0] == '?' and message.content[1] != '?':
        if message.channel.id != 782717630939267142:
            await(await message.channel.send(f"Please use the commands channel for commands!")).delete(delay=5)
            return

        split_msg = message.content[1:].split()
        arguments = ' '.join(split_msg)
        helpFile = open('helpfile.txt', 'r+')

        if len(arguments) == 0:
            await message.channel.send('What command do you need help with? List all commands with `?all`')
        else:
            if arguments == 'all':
                embed = discord.Embed(title='List of server commands', color=0x4287f5)
                for line in helpFile.readlines():
                    splitLine = line.split('/:/')
                    embed.add_field(name=splitLine[0], value=splitLine[2], inline=True)
            else:
                x = 0
                for line in helpFile.readlines():
                    splitLine = line.split('/:/')
                    if arguments == splitLine[0]:
                        embed = discord.Embed(title=splitLine[0].capitalize(), color=0x4287f5)
                        embed.add_field(name="Description:", value=splitLine[1], inline=False)
                        embed.add_field(name="Usage:", value=splitLine[2], inline=False)
                        embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=message.author.avatar_url)
                        x += 1
                if x == 0:
                    await(await message.channel.send('Please enter an existing command.')).delete(delay=5)
                    return
            await message.channel.send(embed=embed)
            helpFile.close()
            
## Command functions

async def repeatCommand(message, arguments):
    await message.channel.send(arguments)

async def balanceCommand(message):
    balance = c.execute('SELECT * FROM users WHERE USERID=?',(message.author.id,)).fetchall()[0][1]
    await message.channel.send(f'Your current balance is: `{balance} credits`')

async def triviaCommand(message):
    questionsFile = open('trivia_questions.txt', 'r', encoding='utf-8')
    answerFile = open('answer.txt', 'r+', encoding='utf-8')
    questionsDict = {}

    a = answerFile.read()
    if a:
        return

    questionsFile.seek(0)
    answerFile.seek(0)
    for line in questionsFile.readlines():
        res = line.replace('[','').replace(']','').replace('"','').replace('\n','').split(', ')
        if  '|' in res[1]:
            continue
        if len(res) > 2:
            continue
        questionsDict[res[0]] = res[1]
    roll = random.randint(0, len(questionsDict.keys()))

    embed = discord.Embed(title='Trivia question', description='Answer with !answer', color=0x4287f5)
    embed.add_field(name='Question:', value=list(questionsDict.keys())[roll], inline = False)
    embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=message.author.avatar_url)
    answerFile.write(questionsDict[list(questionsDict.keys())[roll]])

    answerFile.close()
    questionsFile.close()
    await message.channel.send(embed=embed)

async def answerCommand(message, arguments):
    answerFile = open('answer.txt', 'r+', encoding='utf-8')
    answerFile.seek(0)
    
    answer = answerFile.read()
    useranswer = arguments

    if not answer:
        await message.channel.send('Use !trivia first to generate a question.')
    elif not arguments:
        await message.channel.send('Please enter an answer.')
    else:
        if answer.lower() == useranswer.lower():
            balance = c.execute('SELECT * FROM users WHERE USERID=?',(message.author.id,)).fetchall()[0][1]
            c.execute('UPDATE users SET CREDITS=? WHERE USERID=?', (balance+200, message.author.id,))
            conn.commit()

            await message.channel.send(f'Well done, {message.author.name}! You gained 200 credits. Your balance is now {balance+200} credits')
            await message.add_reaction('✔️')
            answerFile.truncate(0)
    answerFile.close()

async def muteCommand(message,arguments):
    if not arguments:
        await(await message.channel.send('Please provide a user to mute')).delete(delay=3)
    else:
        userToMute = message.mentions[0]
        log_channel = client.get_channel(LOGID)

        if userToMute == client.user:
            return

        if len(arguments.split(' ')) > 1:
            reason = ' '.join(arguments.split(' ')[1:])

            await userToMute.add_roles(get(message.guild.roles, id = 787755199539707906))
            embed = discord.Embed(title='Mute', description=message.author.name, color=0x4287f5)
            embed.add_field(name = 'Description:', value = f'`{userToMute.name}` was muted by `{message.author.name}`', inline= False)
            embed.add_field(name= 'Reason', value = f'`{reason}`', inline = False)
            embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=message.author.avatar_url)
            await log_channel.send(embed = embed)
        else:
            await(await message.channel.send('Please provide a reason for muting')).delete(delay=3)

async def unmuteCommand(message,arguments):
    if not arguments:
        await(await message.channel.send('Please provide a user to unmute')).delete(delay=3)
    else:
        userToUnmute = message.mentions[0]

        if userToUnmute == client.user:
            return

        await userToUnmute.remove_roles(get(message.guild.roles, id = 787755199539707906))

async def dailyCommand(message):
    userid = message.author.id
    userrow = c.execute('SELECT * FROM users WHERE USERID=?', (userid,)).fetchall()[0]
    credit = userrow[1]
    time = userrow[3]

    if not time:
        c.execute('UPDATE users SET CREDITS=? WHERE USERID=?', (credit+1000, userid,))
        c.execute('UPDATE users SET DAILYTIME=? WHERE USERID=?', (datetime.datetime.now().strftime('%Y %m %d %H %M'), userid,))
        conn.commit()
    else:
        if datetime.datetime.now() - timedelta(hours=24) >= datetime.datetime.strptime(time, '%Y %m %d %H %M'):
            c.execute('UPDATE users SET CREDITS=? WHERE USERID=?', (credit+1000, userid,))
            c.execute('UPDATE users SET DAILYTIME=? WHERE USERID=?', (datetime.datetime.now().strftime('%Y %m %d %H %M'), userid,))
            conn.commit()
            await message.channel.send(f'Daily reward given! Your balance is now {credit+1000} credits.')
        else:
            nexttime= (datetime.datetime.strptime(time, '%Y %m %d %H %M') + timedelta(hours=24))
            await message.channel.send(f"You can't get your daily reward yet! Come back at {nexttime.strftime('%H:%M')} on {nexttime.strftime('%A')}")

async def youtubeCommand(message, arguments):
    if arguments:
        results = YoutubeSearch(arguments, max_results=10).to_dict()
        if results:
            url = results[0]["url_suffix"]
            await message.channel.send(f'https://youtube.com{url}')
        else:
            await(await message.channel.send("Couldn't find any results for that query!")).delete(delay=3)
    else:
        await(await message.channel.send('Please provide a search term.')).delete(delay=3)

async def imageCommand(message,arguments):
    if arguments:
        res = service.cse().list(
            q=arguments,
            cx=cxkey,
            searchType='image',
            fileType='png',
            num=1,
            safe= 'off'
        ).execute()

        if not 'items' in res:
            await(await message.channel.send("Couldn't find any results for that query!")).delete(delay=3)
        else:
            for item in res['items']:
                await message.channel.send(item['link'])
    else:
        await(await message.channel.send('Please provide a search term.')).delete(delay=3)

async def diceCommand(message, arguments):
    for x in arguments.split():
        if numCheck(x) == False:
            await message.channel.send(f'Input `{x}` is not a number, please try again.')
            return
    if len(arguments.split()) == 1:
        roll = random.randint(1, int(arguments))
        await message.channel.send(f'You rolled: {roll}')
    elif len(arguments.split()) == 2:
        roll = random.randint(int(arguments.split(' ')[0]), int(arguments.split(' ')[1]))
        await message.channel.send(f'You rolled: {roll}')
    else:
        await message.channel.send('Specify the range (maximum of two numbers).')

async def clearCommand(message,arguments):
    if arguments:
        if len(arguments.split()) > 1:
            await message.channel.send('Please provide only one number.')
            return
        elif numCheck(arguments) == False:
            await message.channel.send(f'Input `{arguments}` is not a number, please try again.')
            return
        else:
            num = int(arguments)
            todelete = []
            async for x in message.channel.history(limit = num + 1):
                todelete.append(x)
            await message.channel.delete_messages(todelete)
    else:
        await message.channel.send('Please provide a number')

async def spotifyCommand(message,arguments):
    if message.mentions:
        user = message.mentions[0]
    else:
        user = message.author
    for activity in user.activities:
        if isinstance(activity, Spotify):
            embed = discord.Embed(title=f'{user.name} is listening to:', color = activity.color)
            embed.add_field(name='Track:', value=f'{activity.title}', inline = True)
            embed.add_field(name='Album:', value=f'{activity.album}', inline = True)
            embed.add_field(name='Artists:', value=f'{", ".join(activity.artists)}', inline = True)
            embed.set_thumbnail(url=activity.album_cover_url)
            embed.set_footer(text=f'Started at {activity.created_at.strftime("%H:%M")}', icon_url=user.avatar_url)
            await message.channel.send(embed = embed)
            return
    await(await message.channel.send(f"{user} isn't listening to anything.")).delete(delay=5)
        
async def selectCommand(message, arguments):
    x = c.execute('SELECT * FROM roles WHERE USERID=?',(message.author.id,)).fetchall()

    valueList = x[0][1:]
    allDict = {}
    emojiDict = {}
    testlist = []
    roleFile = open('roles.txt', 'r+')

    embed = discord.Embed(title='Your roles:', description='These are the role colours you own, select them by typing in their name after !select', color=0x4287f5)

    roleFile.seek(0)
    x = 0
    for line in roleFile.readlines():
        splitLine = line.split('/:/')
        if valueList[x] == 1:
            allDict[splitLine[0].lower()] = splitLine[3].replace('\n','')
            emojiDict[splitLine[0]] = splitLine[2]
        testlist.append(splitLine[0].lower())
        x+=1

    print(testlist)
        
    if len(arguments) == 0:
        for role in list(allDict.keys()):
            embed.add_field(name=role.capitalize(), value=emojiDict[role.capitalize()], inline = True)

        await message.channel.send(embed=embed)
    elif arguments.lower() not in testlist:
        await(await message.channel.send("Please enter a valid colour.")).delete(delay=5)
    elif arguments.lower() not in allDict.keys():
        await message.channel.send("You don't own this colour")
    else:
        if arguments.lower() in allDict.keys():
            id = allDict[arguments.lower()]
            role = get(message.guild.roles, id=int(id))

            for roleid in list(allDict.values()):
                if get(message.guild.roles, id=int(roleid)) in message.author.roles:
                    await message.author.remove_roles(get(message.guild.roles, id=int(roleid)))

            await message.author.add_roles(role)
            await message.channel.send(f'`Successfully set colour to {arguments.lower()}`')
    

## Other functions

def numCheck(a):
    while True:
        try:
            val = int(a)
            break
        except ValueError:
            try:
                val = float(a)
                break
            except ValueError:
                print('Input is not a number.')
                return False

async def badCheck(message):
    for x in bannedWords:
        z = re.compile(rf"{x}", re.IGNORECASE)
        if z.search(''.join(message.content.split())):
            await(await message.channel.send(f"`Please refrain from using profane language such as: {x}!`")).delete(delay=5)   
            await adminLog(message, 'profanity', x) 
            return

async def adminLog(message, type, x):
    log_channel = client.get_channel(LOGID)
    embed = discord.Embed(title=type.capitalize(), description=message.author.name, color=0x4287f5)
    if type == 'profanity':
        embed.add_field(name = 'Description:', value = f'`{message.author.name}` said `{x}` in `{message.channel}`', inline= False)
        embed.add_field(name= 'Full message:', value = f'`{message.content}`', inline = False)
        embed.set_footer(text=datetime.datetime.now().strftime("%b %d %Y %H:%M"), icon_url=message.author.avatar_url)
    elif type == 'edit':
        embed.add_field()
    await log_channel.send(embed=embed)

async def shopMessage():
    shop_channel = client.get_channel(SHOPID)

    roleFile = open('roles.txt', 'r+')
    embed = discord.Embed(title='Name Colours:', description='Here you can buy colours for your name, which you can select with !select. To buy a colour, select the appropriate reaction', color=0x4287f5)
    roleFile.seek(0)
    for line in roleFile.readlines():
        splitLine = line.split('/:/')
        embed.add_field(name=splitLine[0], value=f'`Cost: {splitLine[1]} credits `{splitLine[2]}', inline = True)
    x = await shop_channel.send(embed=embed)

    emojilist = ['🔴', '🟠','🟡','🟢','🌲','🔵','🐋','🟣','⚪','⚫']
    for emoji in emojilist:
        await x.add_reaction(emoji)

client.run(TOKEN)