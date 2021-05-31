import os
from discord import channel, voice_client
from discord.ext.commands.errors import UserNotFound
from discord_components.select import Option
from dns.resolver import query
from dotenv import load_dotenv
from discord.utils import get  
import discord
from discord.ext import commands 
from discord_slash import SlashCommand, SlashContext
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType, Select, button, component
from mcstatus import MinecraftServer
import asyncio
import emoji as e
import mysql.connector
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
host = os.getenv("mariadb_host")
port = os.getenv("mariadb_port")
database = os.getenv("mariadb_database")
username = os.getenv("mariadb_username")
password = os.getenv("mariadb_password")

def sqlconnect(): 
    try:
        mydb = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password
        )
        return mydb
    except mysql.connector.Error as e:
        print(e)
        print('Failed to connect to MySQL')

# ------- SQL FUNCTIONS -------

def createtable(sql,table_name , query):
    tablecursor = sql.cursor()
    tablecursor.execute("SHOW TABLES")  
    tables = []
    for row in tablecursor.fetchall(): 
        tables.append(row[0])
    tablecursor.close()
    if table_name in tables:
        print(f'{table_name} already exists')
        return
    else:
        try:
            with sql.cursor() as cursor:
                cursor.execute(query)
                cursor.close()
                print(f'{table_name} created successfully!')
        except mysql.connector.Error as e:
            print(e)
            print(f'Failed to Create {table_name}')

def deletequery(sql, table , where):
    sql.connect()
    query = (f'DELETE FROM {table} WHERE {where}')
    print(query)
    try:
        with sql as sql:
            sql.connect()
            querycursor = sql.cursor()
            querycursor.execute(query)
            sql.commit()
            querycursor.close()
            print(f'Delete query executed successfully!')
            return 1
    except mysql.connector.Error as e:
        print(e)
        print(f'Failed to execute delete query')
        return 1
    except TypeError as e:
        return 1

def selectquery(sql, table , column , where):
    sql.connect()
    wherenew = str(where)
    query = (f'SELECT {column} FROM {table} WHERE {wherenew}')
    try:
        with sql as sql:
            sql.connect()
            querycursor = sql.cursor()
            querycursor.execute(query)  
            result = querycursor.fetchone()[0]
            sql.commit()
            querycursor.close()
            return result
    except mysql.connector.Error as e:
        print(e)
        print(f'Failed to execute select query')
        return 1
    except TypeError as e:
        return 1

def selectqueryall(sql, table , column, where):
    sql.connect()
    if where is not None:
        query = (f'SELECT {column} FROM {table} WHERE {where}')
    if where is None:
        query = (f'SELECT {column} FROM {table}')
    print(query)
    try:
        with sql as sql:
            sql.connect()
            querycursor = sql.cursor()
            querycursor.execute(query)  
            result = querycursor.fetchall()
            sql.commit()
            querycursor.close()
            print(f'Select query executed successfully {result}!')
            return result
    except mysql.connector.Error as e:
        print(e)
        print(f'Failed to execute select query')
        return 1
    except TypeError as e:
        return 1

def insertquery(sql, table , column , values , where):
    size = len(values)
    sql.connect()
    if where == None:
        query = (f'INSERT INTO {table} {column} VALUES(%s'+(size-1)*(',%s')+')')
        print(query)
    else:
        query = (f'UPDATE {table} SET {column} = {values}' + f' WHERE {where}')
        print(query)
    try:
        with sql as sql:
            querycursor = sql.cursor()
            querycursor.execute(query , values)  
            sql.commit()
            querycursor.close()
            print(f'Insert query executed successfully!')
            return 0
    except mysql.connector.Error as e:
        print(e)
        print(f'Failed to execute insert query')
        return 1

quilds_query = ('''
        CREATE TABLE guilds 
            (guild_id BIGINT NOT NULL PRIMARY KEY,
            guild_name VARCHAR(255) NOT NULL,
            premium BOOLEAN,
            prefix varchar(5) DEFAULT "-",
            administrator_id BIGINT,
            moderator_id BIGINT,
            generalchannel BIGINT,
            statuschannel BIGINT,
            alertschannel BIGINT,
            lpalertschannel BIGINT,
            crashalertschannel BIGINT,
            demandedsuggestions BIGINT,
            acceptedsuggestions BIGINT,
            rejectedsuggestions BIGINT)''')
categories_query = ('''
        CREATE TABLE categories 
            (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            FOREIGN KEY(guild_id) REFERENCES guilds(guild_id),
            category_id BIGINT,
            category_name VARCHAR(255),
            category_less VARCHAR(255)
            )''') 
restrict_query = ('''
        CREATE TABLE hambot3_.restrict (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            guild_id BIGINT DEFAULT NULL,
            restrictrole_name VARCHAR(255),
            restrictrole_id BIGINT,
            restrictrole2_id BIGINT,
            restrictrole3_id BIGINT
            )''')


sql = sqlconnect()      
createtable(sql,'guilds', quilds_query)
createtable(sql,'categories', categories_query)
createtable(sql,'restrict', restrict_query)

colors = {"green": 0x00ff00, "red": 0xff0000, "blue": 0x0000ff, "teal": 0x00FFFF, "dark_teal": 0x10816a}
premium_guilds = [selectqueryall(sql, 'guilds', 'guild_id', None)]
ham_guilds = [380308776114454528, 841225582967783445, 820383461202329671,
82038346120232967, 650658756803428381, 571626209868382236, 631067371661950977]
prefixes = {}
def getprefix(client, message):
    if message.guild.id in premium_guilds and message.guild.id not in prefixes:
        pref = selectquery(sql, "guilds", "prefix", f"guild_id={message.guild.id}")
        prefixes.update({f"{message.guild.id}": f"{pref}"})
    elif message.guild.id not in premium_guilds and message.guild.id not in prefixes:
        prefixes.update({f"{message.guild.id}": f"-"})
    return commands.when_mentioned_or(*prefixes[f"{message.guild.id}"])(client, message)
client = commands.Bot(command_prefix= (getprefix))  # Defines prefix and bot
DiscordComponents(client)
slash = SlashCommand(client, sync_commands=False)  # Defines slash commands

# ------- FUNCTIONS -------

async def stripmessage(string, targetstring):
    if targetstring in string:
            stringlist = string.split(f"\n")
            for stringa in stringlist:
                if targetstring in stringa:
                    return stringa

async def moderatorcheck(guild, member):
    if not guild:
        return 1
    moderatorrole = selectquery(sql, 'guilds', 'moderator_id', f'guild_id = {guild.id}')
    roleobject = guild.get_role(moderatorrole)
    administratorrole = selectquery(sql, 'guilds', 'administrator_id', f'guild_id = {guild.id}')
    roleobject1 = guild.get_role(administratorrole)
    if roleobject in member.roles or roleobject1 in member.roles:
        return 1
    else:
        return 0

async def administratorcheck(guild, member):
    if not guild:
        return 1
    administratorrole = selectquery(sql, 'guilds', 'administrator_id', f'guild_id = {guild.id}')
    roleobject = guild.get_role(administratorrole)
    if roleobject in member.roles:
        return 1
    else:
        return 0

async def statuscheck():
    for guild in client.guilds:
        sql.connect()
        mycursor = sql.cursor()
        guildid = int(guild.id)
        guildname = str(f"{guild.name}")
        try:
            statuschannel = selectquery(sql, 'guilds', 'statuschannel', f'guild_id = {guildid}')
        except mysql.connector.Error as e:
            print(e)
            print(f'Failed to call statuschannel for {guildid}')
            return
        mycursor.close()
        try:
            channel = client.get_channel(statuschannel)
            await channel.purge(limit=10)
            server = MinecraftServer.lookup("play.ham5teak.xyz:25565")
            status = server.status()
            if status.latency >= 1:
                ham5teak = "Online ✅"
            else:
                ham5teak = "Offline ❌"
            embed = discord.Embed(description=f"**Ham5teak Status:** {ham5teak} \n**Players:** {status.players.online}\n**IP:** play.ham5teak.xyz\n**Versions:** 1.13.x, 1.14.x, 1.15.x, 1.16.x", color=discord.Color.teal())
            embed.set_footer(text="Ham5teak Bot 3.0 | play.ham5teak.xyz | Made by Beastman#1937 and Jaymz#7815")
            embed.set_author(name="Ham5teak Network Status", icon_url="https://cdn.discordapp.com/icons/380308776114454528/a_be4514bb0a52a206d1bddbd5fbd2250f.png?size=4096")
            await channel.send(embed=embed)
            print(f"{guild.name} status successfully sent!")
        except:
            print(f"{guildname} doesn't have a status channel set.")
    await asyncio.sleep(600)

def addEmbed(ctx , color, new, image = None):
    if image != None and ctx != None:
        newEmbed = discord.Embed(description=f"{new}", color=ctx.author.color)
        newEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        newEmbed.set_image(url=image)
    elif image != None and ctx == None:
        newEmbed = discord.Embed(description=f"{new}", color=colors[color])
        newEmbed.set_image(url=image)
    else:
        if ctx != None and color == None:
            newEmbed = discord.Embed(description=f"{new}", color=ctx.author.color)
            newEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        elif ctx != None and color != None:
            newEmbed = discord.Embed(description=f"{new}", color=colors[color])
        elif ctx == None:
            newEmbed = discord.Embed(description=f"{new}", color=colors[color])
    newEmbed.set_footer(text="Ham5teak Bot 3.0 | play.ham5teak.xyz | Made by Beastman#1937 and Jaymz#7815")
    return newEmbed

# ------- STARTUP EVENT -------

@client.event
async def on_ready():
    print("""\
╭╮ ╭╮     ╭━━━┳╮      ╭╮    ╭━━╮   ╭╮   ╭━━━╮   ╭━━━╮
┃┃ ┃┃     ┃╭━┳╯╰╮     ┃┃    ┃╭╮┃  ╭╯╰╮  ┃╭━╮┃   ┃╭━╮┃
┃╰━╯┣━━┳╮╭┫╰━┻╮╭╋━━┳━━┫┃╭╮  ┃╰╯╰┳━┻╮╭╯  ╰╯╭╯┃   ┃┃┃┃┃
┃╭━╮┃╭╮┃╰╯┣━━╮┃┃┃┃━┫╭╮┃╰╯╯  ┃╭━╮┃╭╮┃┃   ╭╮╰╮┃   ┃┃┃┃┃
┃┃ ┃┃╭╮┃┃┃┣━━╯┃╰┫┃━┫╭╮┃╭╮╮  ┃╰━╯┃╰╯┃╰╮  ┃╰━╯┣ ╭╮┃╰━╯┃
╰╯ ╰┻╯╰┻┻┻┻━━━┻━┻━━┻╯╰┻╯╰╯  ╰━━━┻━━┻━╯  ╰━━━┻ ╰╯╰━━━╯
                   """)
    sql.connect()
    quildcursor = sql.cursor()
    quildcursor.execute("SELECT guild_id FROM guilds")  
    for row in quildcursor.fetchall(): 
        premium_guilds.append(row[0])
    quildcursor.close()
    print('Logged on as {0}!'.format(client.user.name))
    activity = discord.Game(name="play.ham5teak.xyz")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print("Presence has been set!")
    message = ""
    for guild in client.guilds:
        message += f"{guild.name}\n"
    embedDiscription  = (f"**__Guilds:__ **\n{message}")
    channel = client.get_channel(841245744421273620)
    await channel.send(embed=addEmbed(None,"teal", embedDiscription ))
    # client.load_extension('music')
    client.remove_command('help')
    while True:
        await statuscheck()

# ------- CLIENT COMMANDS -------
@client.command()
@commands.has_permissions(manage_guild=True)
@commands.guild_only()
async def setprefix(ctx, prefix = None):
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    if prefix is None:
        embedDiscription  = (f"Please provide all required arguments. `-setprefix <prefix>`.")
        await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
        return
    if len(prefix) >= 6:
        embedDiscription  = (f"{prefix} has too many characters for a prefix.")
        await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
        return
    if ctx.guild.id in premium_guilds:
        insertquery(sql, "guilds", "prefix", f"'{prefix}'", f"guild_id={ctx.guild.id}")
        prefixes[f"{ctx.guild.id}"] = prefix
    elif ctx.guild.id not in premium_guilds:
        prefixes[f"{ctx.guild.id}"] = prefix
    else: 
        return
    embedDiscription  = (f"Prefix succesfully set to `{prefix}`")
    await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ), delete_after=5)

@client.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount:int):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
          
        return
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)
    embedDiscription  = (f"{amount} messages were successfully deleted.")
    await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ), delete_after=1)

@client.command()
@discord.ext.commands.has_guild_permissions(manage_guild=True)
async def setup(ctx, password, admin_role_id:discord.Role,mod_role_id:discord.Role):
    await ctx.message.delete()
    guild_id = ctx.guild.id
    if guild_id in premium_guilds:
        embedDiscription  = (f"You are already Logged in as Premium")
        await ctx.send(embed=addEmbed(ctx,discord.Color.blue,embedDiscription ))
        return
    else:
        guild_name = ctx.guild.name
        column = '(guild_id , guild_name , premium , administrator_id , moderator_id)'
        values = (guild_id , guild_name , True , admin_role_id.id , mod_role_id.id)
        where = None
        result = (insertquery(sql, 'guilds' , column , values, where))
        query = 'SELECT guild_id FROM guilds NATURAL JOIN categories'
        sql.connect()
        querycursor = sql.cursor()
        querycursor.execute(query)  
        result = querycursor.fetchall()
        sql.commit()
        querycursor.close()        
        if (result == 0):
            embedDiscription  = (f"Registered successfully")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
        else:
            embedDiscription  = (f"Register Failed")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
        query = 'SELECT guild_id FROM guilds NATURAL JOIN restrict'
        sql.connect()
        querycursor = sql.cursor()
        querycursor.execute(query)  
        result = querycursor.fetchall()
        sql.commit()
        querycursor.close()        
        if (result == 0):
            embedDiscription  = (f"Registered successfully")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
        else:
            embedDiscription  = (f"Register Failed")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)

@client.command()
@discord.ext.commands.has_guild_permissions(manage_guild=True)
async def setrestrict(ctx, alias ,role1:discord.Role, role2:discord.Role = None, role3:discord.Role = None):
    await ctx.message.delete()
    guild_id = ctx.guild.id
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    if guild_id not in premium_guilds:
        embedDiscription  = (f"You premium to use this command.")
        await ctx.send(embed=addEmbed(ctx,discord.Color.blue,embedDiscription ), delete_after=5)
        return
    restricttypes = selectqueryall(sql, 'hambot3_.restrict', 'restrictrole_name', f'guild_id = {ctx.guild.id}')
    for stralias in restricttypes:
        if alias == stralias[0]:
            embedDiscription  =(f"Restrict type `{alias}` already exists.")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
            return 1
    else:
        if role3 is None:
            if role2 is None:
                column = '(guild_id  , restrictrole_name , restrictrole_id)'
                values = (guild_id , alias , role1.id)
                where = None
                result = (insertquery(sql, 'hambot3_.restrict' , column , values, where))
                sql.connect()
                querycursor = sql.cursor()
                sql.commit()
                querycursor.close()        
                if (result == 0):
                    embedDiscription  = (f"Restrict `{alias}` successfully set as {role1.mention}")
                    await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
                else:
                    embedDiscription  = (f"Restrict `{alias}` failed to set as {role1.mention}")
                    await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
                return
            column = '(guild_id  , restrictrole_name , restrictrole_id , restrictrole2_id)'
            values = (guild_id , alias , role1.id , role2.id)
            where = None
            result = (insertquery(sql, 'hambot3_.restrict' , column , values, where))
            sql.connect()
            querycursor = sql.cursor()
            sql.commit()
            querycursor.close()        
            if (result == 0):
                embedDiscription  = (f"Restrict `{alias}` successfully set as {role1.mention} and {role2.mention}")
                await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
            else:
                embedDiscription  = (f"Restrict `{alias}` failed to set as {role1.mention} and {role2.mention}")
                await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
            return
        column = '(guild_id  , restrictrole_name , restrictrole_id , restrictrole2_id, restrictrole3_id)'
        values = (guild_id , alias , role1.id , role2.id, role3.id)
        where = None
        result = (insertquery(sql, 'hambot3_.restrict' , column , values, where))
        sql.connect()
        querycursor = sql.cursor()
        sql.commit()
        querycursor.close()        
        if (result == 0):
            embedDiscription  = (f"Restrict `{alias}` successfully set as {role1.mention}, {role2.mention} and {role3.mention}")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
        else:
            embedDiscription  = (f"Restrict `{alias}` failed to set as {role1.mention}, {role2.mention} and {role3.mention}")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
        return

@client.command()
async def edit(ctx, id, *, embedDiscription):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    await ctx.channel.get_partial_message(id).edit(embed = addEmbed(ctx, id, embedDiscription ))

@client.command()
@commands.guild_only()
async def prefix(ctx):
    await ctx.message.delete()
    prefix = prefixes[f"{ctx.guild.id}"]
    await ctx.send(embed=addEmbed(ctx, None, f"Prefix: `{prefix}`"), delete_after=5)

@client.command()
async def setchannel(ctx, command, channel: discord.TextChannel):
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    guild_id = ctx.guild.id
    channelid = str(channel.id)
    commandsloop = ["statuschannel", "alertschannel", "lpalertschannel", "crashalertschannel", "generalchannel"
    , "rejectedsuggestions", "acceptedsuggestions", "demandedsuggestions"]
    for commanda in commandsloop:
        if commanda == command:
            print(f"{commanda} {channelid}")
            column = (command)
            values = (channelid)
            where = (f"guild_id = {guild_id}")
            result = (insertquery(sql, 'guilds', column , values, where))
            if (result == 0):
                embedDiscription  = (f"Successfully registered {command} as `{channel.id}`")
                await ctx.channel.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
            else:
                embedDiscription  = (f"Couldn't register {command} as {channelid}")
                await ctx.channel.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)     

@client.command()
@commands.has_permissions(manage_messages=True)
async def move(ctx, alias):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    sql.connect()
    mycursor = sql.cursor()
    mycursor.execute(f"SELECT category_name FROM categories WHERE guild_id = {ctx.guild.id}")
    aliaslist = mycursor.fetchall()
    mycursor.close()
    for stralias in aliaslist:
        if alias == stralias[0]:
            ctxchannel = ctx.channel
            sql.connect()
            mycursor = sql.cursor()
            mycursor.execute(f"SELECT category_id FROM categories WHERE category_name = '{alias}' AND guild_id = {ctx.guild.id}")
            result = mycursor.fetchone()
            mycursor.close()
            cat = client.get_channel(result[0])
            await ctxchannel.edit(category=cat)
            embedDiscription  = (f"{ctxchannel.mention} has been moved to category {alias}")
            await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)

@client.command(aliases=['rl'])
@commands.has_permissions(manage_messages=True)
async def restrictlist(ctx):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    types = [selectqueryall(sql, 'hambot3_.restrict', 'restrictrole_name', f'guild_id = {ctx.guild.id}')]
    for type in types:
        if types == 0:
            embedDiscription  = ("You don't have any restriction types set")
            await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ), delete_after=5)
            return
        type1 = str(type).replace('(', '').replace(')', '').replace('(', '').replace("'", '').replace("[", '').replace("]", '').replace(',', '').replace(' ', f'\n')
        embedDiscription  = (f"__**Restriction types you can use:**__\n{type1}")
        await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription), delete_after=10)
        print(addEmbed(ctx,"red",embedDiscription))

@client.command()
@commands.has_permissions(manage_messages=True)
async def restrict(ctx, alias):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    if alias.lower() == "none":
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        embedDiscription  = (f"{ctx.channel.mention} has been opened to public.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
    sql.connect()
    mycursor = sql.cursor()
    mycursor.execute(f"SELECT restrictrole_name FROM hambot3_.restrict WHERE guild_id = {ctx.guild.id}")
    aliaslist = mycursor.fetchall()
    mycursor.close()
    for stralias in aliaslist:
        if alias == stralias[0]:
            ctxchannel = ctx.channel
            sql.connect()
            mycursor = sql.cursor()
            mycursor.execute(f"SELECT restrictrole3_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
            result = mycursor.fetchone()
            mycursor.close()
            if result[0] is None:
                sql.connect()
                mycursor = sql.cursor()
                mycursor.execute(f"SELECT restrictrole2_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
                result1 = mycursor.fetchone()
                mycursor.close()
                if result1[0] is None:
                    sql.connect()
                    mycursor = sql.cursor()
                    mycursor.execute(f"SELECT restrictrole_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
                    result1 = mycursor.fetchone()
                    mycursor.close()
                    cat = ctx.guild.get_role(result1[0])
                    await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
                    await ctx.channel.set_permissions(cat, view_channel=True)
                    embedDiscription  = (f"{ctxchannel.mention} has been restricted to {cat.mention}")
                    await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
                    return
                sql.connect()
                mycursor = sql.cursor()
                mycursor.execute(f"SELECT restrictrole_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
                result2 = mycursor.fetchone()
                mycursor.close()
                cat = ctx.guild.get_role(result1[0])
                cat2 = ctx.guild.get_role(result2[0])
                await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
                await ctx.channel.set_permissions(cat, view_channel=True)
                await ctx.channel.set_permissions(cat2, view_channel=True)
                embedDiscription  = (f"{ctxchannel.mention} has been restricted to {cat.mention} and {cat2.mention}")
                await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
                return
            sql.connect()
            mycursor = sql.cursor()
            mycursor.execute(f"SELECT restrictrole_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
            result2 = mycursor.fetchone()
            mycursor.close()
            sql.connect()
            mycursor = sql.cursor()
            mycursor.execute(f"SELECT restrictrole2_id FROM hambot3_.restrict WHERE restrictrole_name = '{alias}' AND guild_id = {ctx.guild.id}")
            result3 = mycursor.fetchone()
            mycursor.close()
            print(result[0])
            cat = ctx.guild.get_role(result[0])
            cat2 = ctx.guild.get_role(result2[0])
            cat3 = ctx.guild.get_role(result3[0])
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.channel.set_permissions(cat, view_channel=True)
            await ctx.channel.set_permissions(cat2, view_channel=True)
            await ctx.channel.set_permissions(cat3, view_channel=True)
            embedDiscription  = (f"{ctxchannel.mention} has been restricted to {cat.mention}, {cat2.mention} and {cat3.mention}")
            await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)

@client.command()
@commands.has_permissions(manage_guild=True)
async def setmove(ctx, categoryi: discord.CategoryChannel, alias):
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    guild_id = ctx.guild.id
    categoryid = str(categoryi.id)
    categoryname = alias
    if guild_id not in premium_guilds:
        embedDiscription  = (f"You need premium to use this command.")
        await ctx.send(embed=addEmbed(ctx,discord.Color.blue,embedDiscription ))
        return
    categoryn = selectqueryall(sql, 'categories', 'category_name', f'guild_id = {ctx.guild.id}')
    for stralias in categoryn:
        if categoryname == stralias[0]:
            embedDiscription  =(f"Category `{categoryname}` already exists.")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)
            return 1
    print(f"{categoryid} {categoryname}")
    column = '(guild_id, category_id)'
    values = (guild_id, categoryid)
    where = None
    result = (insertquery(sql, 'categories', column , values, where))
    column = ('category_name')
    values = (f"'{categoryname}'")
    where = (f"category_id = {categoryid}")
    result = (insertquery(sql, 'categories', column , values, where))
    if (result == 0):
        embedDiscription =(f"Successfully registered {categoryname} as `{categoryid}`")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)    
    else:
        embedDiscription  =(f"Couldn't register {categoryname} as `{categoryid}`")
        await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ), delete_after=5)

@client.command()
@commands.has_permissions(manage_guild=True)
async def removemove(ctx, alias):
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.message.delete()
    categoryname = alias
    categoryn = selectqueryall(sql, 'categories', 'category_name', f'guild_id = {ctx.guild.id}')
    for stralias in categoryn:
        if categoryname == stralias[0]:
            categoryn = deletequery(sql, 'categories', f"category_name = '{categoryname}'")
            embedDiscription  =(f"Category `{categoryname}` has been removed.")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
            return 1
    embedDiscription  =(f"Category `{categoryname}` couldn't be removed.")
    await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ), delete_after=5)
    return 1
    
@client.command(aliases=['scc'])
async def simchannelcreate(ctx):
    await ctx.message.delete()
    await on_guild_channel_create(ctx.channel)

@client.command(aliases=['ml'])
@commands.has_permissions(manage_guild=True)
async def movelist(ctx):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5) 
        return
    await ctx.message.delete()
    categories = [selectqueryall(sql, 'categories', 'category_name', f'guild_id = {ctx.guild.id}')]
    for category in categories:
        if categories == 0:
            embedDiscription  = ("You don't have any categories set")
            await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ), delete_after=5)
            return
        newcat = str(category).replace('(', '').replace(')', '').replace('(', '').replace("'", '').replace("[", '').replace("]", '').replace(',', '').replace(' ', f'\n')
        embedDiscription  = (f"__**Categories you can move channels to:**__\n{newcat}")
        await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ), delete_after=10)    

# ------- ERROR HANDLERS -------

@move.error
async def clear_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.message.delete()
        error = await ctx.send('Please enter the command correctly. `-move <category>`')
        await asyncio.sleep(5)
        await error.delete()

@setmove.error
async def clear_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.ChannelNotFound):
        await ctx.message.delete()
        error = await ctx.send('Please enter a valid category id. `-setmove <categoryid> <alias>`')
        await asyncio.sleep(5)
        await error.delete()
        
@removemove.error
async def clear_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.message.delete()
        error = await ctx.send('Please enter a valid category name. `-removemove <categoryname>`')
        await asyncio.sleep(5)
        await error.delete()

@edit.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.delete()
        error = await ctx.send('Please specify the amount of message you would like to edit. `-edit <messageid> <newmessage>`')
        await asyncio.sleep(5)
        await error.delete()
    if isinstance(error, commands.CommandInvokeError):
        error = await ctx.send('Please enter a valid message ID.')
        await asyncio.sleep(5)
        await error.delete()

@setchannel.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.delete()
        error = await ctx.send('Please specify the channel you would like to set. `-setchannel <channel> <id>`')
        await asyncio.sleep(5)
        await error.delete()

@purge.error
async def clear_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.BadArgument):
        await ctx.message.delete()
        error = await ctx.send('Please make sure to enter a number. `-purge <amount>`')
        await asyncio.sleep(5)
        await error.delete()

# ------- SLASH COMMANDS -------
    
@slash.slash(name="accept")
async def accept(ctx, messageid):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    print(moderatorcheck1)
    if moderatorcheck1 == 0:
        await ctx.defer(hidden=True)
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    result = selectquery(sql, 'guilds', 'acceptedsuggestions', f'guild_id = {ctx.guild.id}')
    if result == 0:
        embedDiscription  = (f"This server doesn't have an accepted suggestions channel set.")
        await ctx.send(embed=addEmbed(ctx,discord.Color.teal,embedDiscription ), hidden=True)
    else:
        msg = await ctx.guild.get_channel(ctx.channel.id).fetch_message(messageid)
        for reaction in msg.reactions:
            if reaction.emoji != "✅":
                return 
            else:
                await ctx.defer(hidden=True)
                reactiona = reaction
                aschannel = client.get_channel(result)
                embedDiscription  = (f"**{reactiona.count} Upvotes:** [Go To Suggestion]({msg.jump_url}) - Suggestion was made in: {ctx.channel.mention}")
                await aschannel.send(embed=addEmbed(ctx,discord.Color.blue,embedDiscription ))
                await aschannel.send(embed=msg.embeds[0])
                embedDiscription  = (f"[Suggestion]({msg.jump_url}) successfully accepted!")
                await ctx.send(embed=addEmbed(ctx,discord.Color.blue,embedDiscription ))
                return

@slash.slash(name="ham5teak", description="View Ham5teak network status")
async def ham5teak(ctx):
    server = MinecraftServer.lookup("play.ham5teak.xyz:25565")
    status = server.status()
    if status.latency >= 1:
        ham5teak = "Online ✅"
    else:
        ham5teak = "Offline ❌"
    print("The server has {0} players and replied in {1} ms".format(status.players.online, status.latency))
    embedDiscription =(f"**Ham5teak Status:** {ham5teak} \n **Players:** {status.players.online}")
    await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))  

@slash.slash(name="help")
async def help(ctx):
    await ctx.defer(hidden=True)
    await ctx.send("boo")

@slash.slash(name="move", description="Move a channel to specified category.", )
async def move(ctx, category):
    await ctx.defer(hidden=True)
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    if moderatorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
        return
    alias = category
    sql.connect()
    mycursor = sql.cursor()
    mycursor.execute(f"SELECT category_name FROM categories WHERE guild_id = {ctx.guild.id}")
    aliaslist = mycursor.fetchall()
    mycursor.close()
    for stralias in aliaslist:
        if alias == stralias[0]:
            ctxchannel = ctx.channel
            sql.connect()
            mycursor = sql.cursor()
            mycursor.execute(f"SELECT category_id FROM categories WHERE category_name = '{alias}' AND guild_id = {ctx.guild.id}")
            result = mycursor.fetchone()
            mycursor.close()
            cat = client.get_channel(result[0])
            await ctxchannel.edit(category=cat)
            embedDiscription  = (f"{ctxchannel.mention} has been moved to category {alias}")
            await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))

@slash.slash(name="tag", description="A command used to leave a note to a channel")
async def tag(ctx, note, user:discord.User = None, channel:discord.TextChannel = None, role:discord.Role = None):
    moderatorcheck1 = await moderatorcheck(ctx.guild, ctx.author)
    print(moderatorcheck1)
    if moderatorcheck1 == 0:
        await ctx.defer(hidden=True)
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), delete_after=5)
        return
    await ctx.defer(hidden=False)
    print(f"{note} {user} {channel} {role}")
    finalmentions = []
    mentions = [user, channel, role]
    for mention in mentions:
        if mention is not None:
            if finalmentions == 0:
                finalmentions.insert(mention.mention)
                print(', '.join(finalmentions))
            finalmentions.append(mention.mention)
            print(', '.join(finalmentions))
    for mention in mentions:
        if mention is not None:
            print(finalmentions)
            print("message has a mention")
            embedDiscription =(f"{ctx.author.mention} has tagged the channel as `{note.upper()}` \n\n**Mentions:** {', '.join(finalmentions)}")
            await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
            return
    print("message doesn't have mentions")
    embedDiscription  = (f"{ctx.author.mention} has tagged the channel as `{note.upper()}`")
    await ctx.send(embed=addEmbed(ctx,None,embedDiscription )) 

# ------- SETTING SLASH COMMANDS -------

@slash.slash(name="setchannel", description="Set channels for your server")
@commands.has_permissions(manage_guild=True)
async def setchannel(ctx, value: discord.TextChannel, channel):
    await ctx.defer(hidden=True)
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
        return
    guild_id = ctx.guild.id
    channelid = str(value.id)
    commandsloop = ["statuschannel", "alertschannel", "lpalertschannel", "crashalertschannel", "generalchannel"
    , "acceptedsuggestions", "rejectedsuggestions", "demandedsuggestions"]
    for commanda in commandsloop:
        if commanda == channel:
            print(f"{commanda} {channelid}")
            column = (channel)
            values = (channelid)
            where = (f"guild_id = {guild_id}")
            result = (insertquery(sql, 'guilds', column , values, where))
            if result is not None:
                embedDiscription  = (f"{channel} successfully registered as <#{channelid}>")
                await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ))
            else:
                embedDiscription  = (f"{channel} couldn't be registered as {channelid}")
                await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ))  
        
@slash.slash(name="setmove")
@commands.has_permissions(manage_guild=True)
async def setmove(ctx, categoryi: discord.CategoryChannel, alias):
    await ctx.defer(hidden=True)
    await administratorcheck(ctx.guild, ctx.author)
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
        return
    guild_id = ctx.guild.id
    categoryid = str(categoryi.id)
    categoryname = alias
    categoryn = selectqueryall(sql, 'categories', 'category_name', f'guild_id = {ctx.guild.id}')
    for stralias in categoryn:
        if categoryname == stralias[0]:
            embedDiscription  =(f"Category `{categoryname}` already exists.")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ))
            return 1
    print(f"{categoryid} {categoryname}")
    column = '(guild_id, category_id)'
    values = (guild_id, categoryid)
    where = None
    result = (insertquery(sql, 'categories', column , values, where))
    column = ('category_name')
    values = (f"'{categoryname}'")
    where = (f"category_id = {categoryid}")
    result = (insertquery(sql, 'categories', column , values, where))
    if (result == 0):
        embedDiscription =(f"Successfully registered {categoryname} as `{categoryid}`")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))   
    else:
        embedDiscription  =(f"Couldn't register {categoryname} as `{categoryid}`")
        await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ))

@slash.slash(name="setrole")
@commands.has_permissions(manage_guild=True)
async def setrole(ctx, administrator:discord.Role, moderator: discord.Role):
    await ctx.defer(hidden=True)
    administratorcheck1 = await administratorcheck(ctx.guild, ctx.author)
    if administratorcheck1 == 0:
        embedDiscription  = (f"You don't have permission to do this.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
        return
    print(f"{administrator.id} {moderator.id}")
    result = selectquery(sql, 'guilds', 'moderator_id', f'guild_id = {ctx.guild.id}')
    if result is None:
        embedDiscription  = (f"Server needs to be setup before executing this command.")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ))
    elif result is not None:
        a = insertquery(sql, "guilds", "moderator_id", f"{moderator.id}", f"guild_id = {ctx.guild.id}")
        b = insertquery(sql, "guilds", "administrator_id", f"{administrator.id}", f"guild_id = {ctx.guild.id}")
        if (a == 0) and (b == 0):
            embedDiscription  = (f"New administrator and moderator roles have successfully been set as {administrator.mention} {moderator.mention}")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ))
        else:
            embedDiscription  = (f"Couldn't register {administrator.mention} {moderator.mention} as administrator and moderator.")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ))

@slash.slash(name="setup")
@commands.has_permissions(manage_guild=True)
async def setup(ctx, password, administrator:discord.Role, moderator:discord.Role):
    await ctx.defer(hidden=True)
    print(password)
    guild_id = ctx.guild.id
    if guild_id in premium_guilds:
        embedDiscription  = (f"You are already logged in as Premium")
        await ctx.send(embed=addEmbed(ctx,"dark_teal",embedDiscription ))
        return
    else:
        guild_name = ctx.guild.name
        column = '(guild_id , guild_name , premium , administrator_id , moderator_id)'
        values = (guild_id , guild_name , True , administrator.id , moderator.id)
        where = None
        await insertquery(sql, 'guilds' , column , values, where)
        insertcheck = selectquery(sql, 'guilds', 'premium', f'guild_id = {ctx.guild.id}')    
        if (insertcheck != 0):
            embedDiscription  = (f"Setup successfully completed!")
            await ctx.send(embed=addEmbed(ctx,"green",embedDiscription ))
        else:
            embedDiscription  = (f"Setup failed!")
            await ctx.send(embed=addEmbed(ctx,"red",embedDiscription ))

# ------- SLASH COMMAND ERROR HANDLERS -------
@client.event
async def on_slash_command_error(ctx, error):
    print(error)
    if isinstance(error, discord.errors.NotFound):
        embedDiscription  = (f"Please enter a valid ID. \n{error}")
        await ctx.send(embed=addEmbed(ctx,"teal",embedDiscription ), hidden=True)
    if isinstance(error, commands.MissingPermissions):
        await ctx.defer(hidden=True)
        embedDiscription  = (f"Please make sure you have entered all values correctly.\n{error}")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), hidden=True)
    if isinstance(error, commands.ChannelNotFound):
        await ctx.defer(hidden=True)
        embedDiscription  = (f"Please make sure you have entered all values correctly.\n{error}")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), hidden=True)
    if isinstance(error, commands.RoleNotFound):
        await ctx.defer(hidden=True)
        embedDiscription  = (f"Please make sure you have entered all values correctly.\n{error}")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), hidden=True)
    if isinstance(error, commands.MemberNotFound):
        await ctx.defer(hidden=True)
        embedDiscription  = (f"Please make sure you have entered all values correctly.\n{error}")
        await ctx.send(embed=addEmbed(ctx,None,embedDiscription ), hidden=True)

# ------- EVENT HANDLERS -------

@client.event
async def on_guild_channel_create(channel):
    if "ticket-" not in channel.name:
        return
    if channel.guild.id not in ham_guilds:
        return

    embedDescription  = f"""Hello! The staff team will be assisting you shortly.
In order to make this process easier for us staff, please choose from
the following choices by clicking the button describing your issue.

1. **Item Lost** 
2. **Reporting an Issue/Bug**
3. **Same IP Connection** 
4. **Connection Problems**
5. **Discord Issue**
6. **Forgot Password**
7. **Ban/Mute Appeal**
8. **Queries**
9. **In-Game Rank Parity**
10. **Role Application**"""

    async def embed1(embedDescription):
        embed1 = discord.Embed(description=f"{embedDescription}", color=discord.Color.dark_teal())
        embed1.set_author(name="Ham5teak Bot Ticket Assistant", icon_url="https://cdn.discordapp.com/icons/380308776114454528/a_be4514bb0a52a206d1bddbd5fbd2250f.png?size=4096")
        embed1.set_footer(text="Ham5teak Bot 3.0 | play.ham5teak.xyz | Made by Beastman#1937 and Jaymz#7815")
        return embed1
    

    msg = await channel.send(embed=await embed1(embedDescription),components=[
                # Row 1
                [Button(style=ButtonStyle.green, label=f"1", id="Item Lost"),
                Button(style=ButtonStyle.green, label=f"2", id="Issue or Bug Report"),
                Button(style=ButtonStyle.green, label=f"3", id="Same IP Connection"),
                Button(style=ButtonStyle.green, label=f"4", id="Connection Problems"),
                Button(style=ButtonStyle.green, label=f"5", id="Discord Issue")],
                # Row 2
                [Button(style=ButtonStyle.green, label=f"6", id="Forgot Password"),
                Button(style=ButtonStyle.green, label=f"7", id="Ban or Mute Appeal"),
                Button(style=ButtonStyle.green, label=f"8", id="Queries"),
                Button(style=ButtonStyle.green, label=f"9", id="In-Game Rank Parity"),
                Button(style=ButtonStyle.green, label=f"10", id="Role Application"),],
                # Row 3
                [Button(style=ButtonStyle.URL, label=f"Visit Store", url="http://shop.ham5teak.xyz/"),
                Button(style=ButtonStyle.URL, label=f"Visit Forums", url="https://ham5teak.xyz/")],
                ])
    while True:
        res = await client.wait_for(event="button_click",check=lambda res: res.channel == channel)
        if res.component.id == "Item Lost":
            embedDescription1 = f"1. **Item Lost Due To Server Lag/Crash** \n\n\`\`\`\nIn-game Name:\nServer:\nItems you lost:  \n\`\`\`\n\nIf they are enchanted tools, please mention the enchantments if possible."
        elif res.component.id == "Issue or Bug Report":
            embedDescription1 = f"2. **Issue/Bug Report** \n\n\`\`\`\nIn-Game Name : \nServer: \nIssue/Bug :\n\`\`\`"
        elif res.component.id == "Same IP Connection":
            embedDescription1 = f"3. **Same IP Connection** \n\n\`\`\`\nIn-Game Name of Same IP Connection : \n- \n- \n\nIP Address : (Format should be xxx.xxx.xxx.xxx)\n\`\`\`"
        elif res.component.id == "Connection Problems":
            embedDescription1 = f"4. **Connection Problems** \n\n\`\`\`\nIn-game Name:\nWhat connection problem are you facing? Please explain briefly:\n\`\`\`\n\n"
        elif res.component.id == "Discord Issue":
            embedDescription1 = f"5. **Discord Issue** \nPlease state your issue and wait patiently until our support team arrives."
        elif res.component.id == "Forgot Password":
            embedDescription1 = f"6. **Forgot Password** \n\n\`\`\`\nIn-game Name:\nIP Address : (Format should be xxx.xxx.xxx.xxx)\n\`\`\`"
        elif res.component.id == "Ban or Mute Appeal":
            embedDescription1 = f"""7. **Ban/Mute Appeal** \n\n\`\`\`\nWhy did you get banned/muted? \nWas it on discord or in-game?\n\`\`\` \nIf it was in-game, what is your in-game name and who banned/muted you? 
        \nAlso - please do a ban appeal/mute appeal next time using https://ham5teak.xyz/forums/ban-appeal.21/"""
        elif res.component.id == "Queries":
            embedDescription1 = f"""8. **Queries** \nPlease state your questions here and wait patiently for a staff to reply.\nIf you have to do something at the moment, please leave a note for Staff."""
        elif res.component.id == "In-Game Rank Parity":
            embedDescription1 = f"""9. **In-Game Rank Parity** \nPlease state your In-Game Name and rank you would like to be paired.\nIf you have to do something at the moment, please leave a note for Staff.
            \n\`\`\`\nIn-Game Name: \nRank: \n\`\`\`\n"""
        elif res.component.id == "Role Application":
            embedDescription1 = f"""10. **Role Application** \nPlease state the role you want to apply for `Youtuber/DJ/Dev-Chat`.
            \nIf you're applying for youtuber please send a video you've recorded in Ham5teak if not please wait until our support team arrives."""
        if embedDescription1 is not None:
            await msg.edit(embed=await embed1(embedDescription1),components=[
            Button(style=ButtonStyle.green, label=f"{res.user} chose {res.component.id}", disabled=True)
            ]) 
        serversandcats = {"Survival": 848284762514391061, "Skyblocks": 841403196693413888, "Semi-Vanilla": 841403196693413888, 
        "Factions": 841403196693413888, "Prison": 841403196693413888, "Creative": 841403196693413888, 
        "Caveblocks": 841403196693413888, "Minigames": 841403196693413888}
        options1 = []
        for server in serversandcats.keys():
            options1.append(Option(label=server, value=server))
        await res.respond(
            type=InteractionType.ChannelMessageWithSource,
            embed= await embed1(f"""{res.component.id} chosen.
        \nIf your issue is occurring in a specific server you can optionally select it."""),
            components=[Select(id=f"{res.component.id}-{res.user.name}",options=options1
        )])
        if "ticket-" in channel.name:
            await channel.edit(name=f"{res.component.id}-{res.user.name}")
        if channel.guild.id not in ham_guilds:
            return
        serversent = True
        while serversent == True:
            res1 = await client.wait_for("select_option", check=lambda res1: res1.component["custom_id"].replace(" ", "-").lower() == channel.name)
            for servername in serversandcats.keys():
                if res1.component["values"][0] == servername:
                    cat = client.get_channel(serversandcats[servername])
                    await channel.edit(category=cat)
            embedDescription2 = f"{res1.component['values'][0]} selected as ticket category."
            await res1.respond(
                type=InteractionType.UpdateMessage,
                embed=await embed1(embedDescription2),
                components=[]
            )
            serversent = False


@client.event
async def on_reaction_add(reaction, user):
    messageid = reaction.message.id
    rcount = 2
    reacted = True
    reacted = False
    if "polls" in reaction.message.channel.name:
        if user.bot:
            return
        while reacted == False:
            messageobj = await reaction.message.channel.fetch_message(messageid)
            messagereactions = messageobj.reactions
            reactioncounts = []
            await asyncio.sleep(10)
            for reaction in messagereactions:
                reactioncounts.append(int(reaction.count))
            for reaction in messagereactions:
                if reaction.count == int(max(reactioncounts)):
                    finalcount = int(reaction.count - 1)
                    channel = reaction.message.channel
                    dsuggestionschannel = client.get_channel(channel.id)
                    msg = await channel.fetch_message(messageid)
                    channelcheck = await client.get_channel(channel.id).history(limit=20).flatten()
                    for sc in channelcheck:
                        if f'https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}' in sc.content:
                            return
                    try:
                        await messageobj.edit(content=f'**{reaction.emoji} won with {finalcount} votes:**\n https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}',embed=msg.embeds[0])
                    except AttributeError as e:
                        print(f"{reaction.message.guild.name} doesn't have a demanded suggestions channel set.")
                    return
    if "suggestions" in reaction.message.channel.name:
        if reaction.emoji == "✅":
            if reaction.count == rcount:
                dsuggestions = selectquery(sql, 'guilds', 'demandedsuggestions', f'guild_id = {reaction.message.guild.id}')
                channel = reaction.message.channel
                if dsuggestions is None:
                    return
                dsuggestionschannel = client.get_channel(dsuggestions)
                msg = await channel.fetch_message(messageid)
                suggestioncheck = await client.get_channel(dsuggestions).history(limit=20).flatten()
                for sc in suggestioncheck:
                    if f'https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}' in sc.content:
                        return
                try:
                    await dsuggestionschannel.send(f'**{reaction.count} upvotes:** https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}',embed=msg.embeds[0])
                except AttributeError as e:
                    print(f"{reaction.message.guild.name} doesn't have a demanded suggestions channel set.")
                return
        elif reaction.emoji == "❌":
            if reaction.count == rcount:
                rsuggestions = selectquery(sql, 'guilds', 'rejectedsuggestions', f'guild_id = {reaction.message.guild.id}')
                channel = reaction.message.channel
                if rsuggestions is None:
                    return
                rsuggestionschannel = client.get_channel(rsuggestions)
                msg = await channel.fetch_message(messageid)
                try:
                    suggestioncheck = await client.get_channel(rsuggestions).history(limit=20).flatten()
                    for sc in suggestioncheck:
                        if f'https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}' in sc.content:
                            return
                except AttributeError as e:
                    print(f"{rsuggestions} channel has no suggestion history.")
                try:
                    await rsuggestionschannel.send(f'**{reaction.count} downvotes:** https://discordapp.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{messageid}',embed=msg.embeds[0])
                except AttributeError as e:
                    print(f"{reaction.message.guild.name} doesn't have a rejected suggestions channel set.")
                return

@client.event
async def on_message(ctx):
    if not ctx.guild:
        return
    channelnames = ["announcements", "updates", "competitions", "events"]
    for channel in channelnames:
        if channel in ctx.channel.name:
            if not ctx.author.bot:
                if ctx.content.startswith(getprefix(client, ctx)):
                    await client.process_commands(ctx)
                else:
                    if ctx.attachments:
                        for imageextensions in [".jpg", ".jpeg", ".png", ".gif"]:
                            if imageextensions in ctx.attachments[0].filename:
                                await ctx.attachments[0].save(f"./{ctx.attachments[0].filename}")
                                file = discord.File(ctx.attachments[0].filename)
                                embedDiscription  = (f"{ctx.content}")
                                embed = addEmbed(ctx,None,embedDiscription )
                                embed.set_image(url=f"attachment://{ctx.attachments[0].filename}")
                                msg = await ctx.channel.send(embed=embed, file=file)
                                await msg.add_reaction("👍")
                                await msg.add_reaction("❤️")  
                                print(f"An image inclusive announcement was made in #{ctx.channel.name} by {ctx.author}.")
                                await ctx.delete()
                                os.remove(f"./{ctx.attachments[0].filename}")
                                return
                        await ctx.attachments[0].save(f"./{ctx.attachments[0].filename}")
                        file = discord.File(ctx.attachments[0].filename)
                        embedDiscription  = (f"{ctx.content}")
                        embed = addEmbed(ctx,None,embedDiscription )
                        msg = await ctx.channel.send(embed=embed, file=file)
                        await msg.add_reaction("👍")
                        await msg.add_reaction("❤️")
                        print(f"An attachment inclusive announcement was made in #{ctx.channel.name} by {ctx.author}.")
                        await ctx.delete()
                        os.remove(f"./{ctx.attachments[0].filename}")
                    if not ctx.attachments:
                        await ctx.delete()
                        embedDiscription  = (f"{ctx.content}")
                        msg = await ctx.channel.send(embed=addEmbed(ctx,None,embedDiscription ))
                        await msg.add_reaction("👍")
                        await msg.add_reaction("❤️")
                        print(f"An announcement was made in #{ctx.channel.name} by {ctx.author}.")
    if "suggestions" in ctx.channel.name:
        if not ctx.author.bot:
            if ctx.content.startswith(client.command_prefix):
                await client.process_commands(ctx)
            else:
                if ctx.attachments:
                    await ctx.attachments[0].save(f"./{ctx.attachments[0].filename}")
                    file = discord.File(ctx.attachments[0].filename)
                    embedDiscription  = (f"{ctx.content}")
                    embed = addEmbed(ctx,None,embedDiscription )
                    embed.set_image(url=f"attachment://{ctx.attachments[0].filename}")
                    msg = await ctx.channel.send(embed=embed, file = file)
                    await msg.add_reaction("✅")
                    await msg.add_reaction("❌")
                    print(f"An image inclusive suggestion was made in #{ctx.channel.name} by {ctx.author}.")
                    await ctx.delete()
                    os.remove(f"./{ctx.attachments[0].filename}")
                if not ctx.attachments:
                    await ctx.delete()
                    embedDiscription  = (f"{ctx.content}")
                    msg = await ctx.channel.send(embed=addEmbed(ctx,None,embedDiscription ))
                    await msg.add_reaction("✅")
                    await msg.add_reaction("❌")
                    print(f"A suggestion was made in #{ctx.channel.name} by {ctx.author}.")
    if "polls" in ctx.channel.name or "poll" in ctx.channel.name:
        if not ctx.author.bot:
            if ctx.content.startswith("-"):
                await client.process_commands(ctx)
            else:
                if ctx.attachments:
                    await ctx.attachments[0].save(f"./{ctx.attachments[0].filename}")
                    file = discord.File(ctx.attachments[0].filename)
                    sent = True
                    await ctx.delete()
                    components1 = []
                    reactionstotal = {}
                    reactedusers = []
                    content = e.demojize(ctx.content)
                    messageemojis = re.findall(r'(:[^:]*:)', content)
                    for emoji in messageemojis:
                        try:
                            emoji1 = e.emojize(emoji)
                            components1.append(Button(emoji=emoji1, id=emoji1))
                            reactionstotal.update({emoji1: 0})
                        except: 
                            pass
                    reactionstotal1 = str(reactionstotal).replace("{", " ").replace("}", "").replace(",", f"\n").replace(":", "").replace("'", "")
                    embedDescription  = (f"{ctx.content}\n\n```{reactionstotal1}\n```")
                    msg = await ctx.channel.send(embed=addEmbed(ctx,None,embedDescription, f"attachment://{ctx.attachments[0].filename}"), components=[components1], file=file)
                    print(f"An image inclusive poll was made in #{ctx.channel.name} by {ctx.author}.")
                    while sent == True:
                        try:
                            res = await client.wait_for(event="button_click",check=lambda res: res.channel == ctx.channel, timeout=108000)
                            if res.user.id in reactedusers:
                                await res.respond(
                                    type=InteractionType.ChannelMessageWithSource,
                                    content=f'You have already voted for this poll.'
                                )
                            else:
                                getdata = reactionstotal[res.component.id]
                                reactionstotal.update({res.component.id: getdata + 1})
                                reactionstotal1 = str(reactionstotal).replace("{", " ").replace("}", "").replace(",", f"\n").replace(":", "").replace("'", "")
                                embedDescription1 = f"{ctx.content}\n\n```{reactionstotal1}\n```"
                                await msg.edit(embed=addEmbed(ctx,None,embedDescription1, f"attachment://{ctx.attachments[0].filename}"),
                                    components=[components1])
                                await res.respond(
                                    type=InteractionType.ChannelMessageWithSource,
                                    content=f'Successfully voted for {res.component.id}.'
                                )
                                reactedusers.append(res.user.id)
                        except asyncio.TimeoutError:
                            embedDescription1 = f"{ctx.content}\n\n```{reactionstotal1}\n```\n\n **This poll has ended.**"
                            await msg.edit(embed=addEmbed(ctx,None,embedDescription1, f"attachment://{ctx.attachments[0].filename}"),
                                    components=[])
                            sent = False
                    os.remove(f"./{ctx.attachments[0].filename}")
                if not ctx.attachments:
                    sent = True
                    await ctx.delete()
                    components1 = []
                    reactionstotal = {}
                    reactedusers = []
                    content = e.demojize(ctx.content)
                    messageemojis = re.findall(r'(:[^:]*:)', content)
                    for emoji in messageemojis:
                        try:
                            emoji1 = e.emojize(emoji)
                            components1.append(Button(emoji=emoji1, id=emoji1))
                            reactionstotal.update({emoji1: 0})
                        except: 
                            pass
                    reactionstotal1 = str(reactionstotal).replace("{", " ").replace("}", "").replace(",", f"\n").replace(":", "").replace("'", "")
                    embedDescription  = (f"{ctx.content}\n\n```{reactionstotal1}\n```")
                    msg = await ctx.channel.send(embed=addEmbed(ctx,None,embedDescription ), components=[components1])
                    print(f"A poll was made in #{ctx.channel.name} by {ctx.author}.")
                    while sent == True:
                        try:
                            res = await client.wait_for(event="button_click",check=lambda res: res.channel == ctx.channel, timeout=108000)
                            if res.user.id in reactedusers:
                                await res.respond(
                                    type=InteractionType.ChannelMessageWithSource,
                                    content=f'You have already voted for this poll.'
                                )
                            else:
                                getdata = reactionstotal[res.component.id]
                                reactionstotal.update({res.component.id: getdata + 1})
                                reactionstotal1 = str(reactionstotal).replace("{", " ").replace("}", "").replace(",", f"\n").replace(":", "").replace("'", "")
                                embedDescription1 = f"{ctx.content}\n\n```{reactionstotal1}\n```"
                                await msg.edit(embed=addEmbed(ctx,None,embedDescription1 ),
                                    components=[components1])
                                await res.respond(
                                    type=InteractionType.ChannelMessageWithSource,
                                    content=f'Successfully voted for {res.component.id}.'
                                )
                                reactedusers.append(res.user.id)
                        except asyncio.TimeoutError:
                            embedDescription1 = f"{ctx.content}\n\n```{reactionstotal1}\n```\n\n **This poll has ended.**"
                            await msg.edit(embed=addEmbed(ctx,None,embedDescription1 ),
                                    components=[])
                            sent = False

    await client.process_commands(ctx)

    if "console-" in ctx.channel.name:
        messagestrip = await stripmessage(ctx.content, 'a server operator')
        if messagestrip:
            print(messagestrip)
            alertschannelcheck = selectquery(sql, 'guilds', 'alertschannel', f'guild_id = {ctx.guild.id}')
            generalchannelcheck = selectquery(sql, 'guilds', 'generalchannel', f'guild_id = {ctx.guild.id}')
            if alertschannelcheck != 0:
                alertschannel = client.get_channel(alertschannelcheck)
                msg = await alertschannel.send(content=f'```{messagestrip}``` It originated from {ctx.channel.mention}!',
                components=[Button(style=ButtonStyle.red, label="Verify", id=messagestrip)])
                if generalchannelcheck != 0:
                    generalchannel = client.get_channel(generalchannelcheck)
                    await generalchannel.send(content=f'**WARNING!** `/op` or `/deop` was used. Check {alertschannel.mention} for more info.', delete_after=600)
                verified = False
                while verified == False:
                    res = await client.wait_for("button_click")
                    if res.component.id == messagestrip:
                        await msg.edit(content=f'```{messagestrip}``` It originated from {ctx.channel.mention}!',
                        components=[Button(style=ButtonStyle.green, disabled=True ,label=f"OP Verified By {res.user}")])
                        await res.respond(
                            type=InteractionType.ChannelMessageWithSource,
                            content=f'Op successfully verified.'
                        )
                        verified = True
        messagestrip = await stripmessage(ctx.content, 'Main thread terminated by WatchDog due to hard crash')
        if messagestrip:
            print(messagestrip)
            crashalertschannelcheck = selectquery(sql, 'guilds', 'crashalertschannel', f'guild_id = {ctx.guild.id}')
            generalchannelcheck = selectquery(sql, 'guilds', 'generalchannel', f'guild_id = {ctx.guild.id}')
            if crashalertschannelcheck != 0:
                crashalertschannel = client.get_channel(crashalertschannelcheck)
                await crashalertschannel.send(f'```{messagestrip}``` It originated from {ctx.channel.mention}!')
                if generalchannelcheck != 0:
                    generalchannel = client.get_channel(generalchannelcheck)
                    await generalchannel.send(f'**WARNING!** {ctx.channel.mention} has just **hard crashed!** Check {crashalertschannel.mention} for more info.')
    if "console-lobby" in ctx.channel.name:
        lptriggers = ["now inherits permissions from", "no longer inherits permissions from", "[LP] Demoting",
         "[LP] Promoting", "[LP] Web editor data was applied", "[LP] LOG > webeditor", "[LP] LOG > (Console@"
         , "[LP] Set"]
        for trigger in lptriggers:
            messagestrip = await stripmessage(ctx.content, trigger)
            if messagestrip:
                print(messagestrip)
                lpalertschannelcheck = selectquery(sql, 'guilds', 'lpalertschannel', f'guild_id = {ctx.guild.id}')
                if lpalertschannelcheck != 0:
                    lpalertschannel = client.get_channel(lpalertschannelcheck)
                    await lpalertschannel.send(f'```{messagestrip}``` It originated from {ctx.channel.mention}!')
    if ctx.guild.id in ham_guilds:
        if "console-survival" in ctx.channel.name:
            messagestrip = await stripmessage(ctx.content, '[HamAlerts] Thank you')
            if messagestrip:
                print(messagestrip)
                guildchannels = ctx.guild.channels
                for channel in guildchannels:
                    if "receipts" in channel.name:
                        await channel.send(f'```{messagestrip}```')
    return

client.run(TOKEN)  # Changes