# Corvus created by Max Norfolk
import asyncio
from typing import Optional
from traceback import TracebackException

import discord
from discord.ext import commands
from discord.ext.commands import errors
from time_tracker import *
from date_formatter import format_date
from locations import *

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')  # do not use default help, instead use a custom one making use of embeds

finished_conditions = []
set_on_condition_expire(lambda s: finished_conditions.append(s))  # on condition add it to the list

current_round = 0  # TODO keep track of combat

embed_color = 0x005b5b


# # # # # # # # # # # # # # # #
# Bot Events                  #
# # # # # # # # # # # # # # # #


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game("D&D"))

    print('\n' + '-=' * 35 + '-')
    print('Bot online')
    print('I am running on ' + bot.user.name)
    print('With the ID: ' + str(bot.user.id))
    print('Running Version: ' + discord.__version__)
    print('\n' + '-=' * 35 + '-')


# respond in discord on error
@bot.event
async def on_command_error(ctx, error: Exception):
    if type(error) == errors.CheckFailure:
        pass
    elif type(error) == errors.CommandNotFound:
        await ctx.send('An error occurred! The following command could not be found: `%s`' % ctx.message.content)

    else:
        await ctx.send('{} the following error occurred:\n`{}`.'.format(ctx.author.mention, str(error)))


# block dms
@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# # # # # # # # # # # # # # # #
# Helper functions            #
# # # # # # # # # # # # # # # #

def convert_duration(time: str) -> Optional[Duration]:
    """Converts a string for duration to a different duration"""
    time = time.upper()

    if time in ['D', 'DAY', 'DAYS']:  # determine what duration they meant
        return Duration.DAY
    elif time in ['H', 'HOUR', 'HOURS']:
        return Duration.HOUR
    elif time in ['M', 'MIN', 'MINS', 'MINUTE', 'MINUTES']:
        return Duration.MINUTE
    elif time in ['R', 'ROUND', 'ROUNDS']:
        return Duration.ROUND
    else:
        return None


# # # # # # # # # # # # # # # #
# Bot Commands                #
# # # # # # # # # # # # # # # #

# basic help command
@bot.command()
async def help(ctx):
    em = discord.Embed(title="Help", color=embed_color)
    em.add_field(inline=False, name=".ping", value="Tests whether the bot is online")
    em.add_field(inline=False, name=".help", value="Shows this message")
    em.add_field(inline=False, name=".food",
                 value="Returns the amount of food remaining or adds the given amount to your total food")
    em.add_field(inline=False, name=".date", value="Returns the current date and time in-game")
    em.add_field(inline=False, name=".advance", value="Advances the given amount")
    em.add_field(inline=False, name=".active", value="Shows the active conditions")
    em.add_field(inline=False, name=".infect",
                 value="Adds a condition to expire after the given amount of time expires")
    em.add_field(inline=False, name=".loc", value="Adds a location, or show a location at the given"
                                                  " address (or shows all location if no address is given)")
    em.add_field(inline=False, name=".recap", value="Shows all the locations that were added last session")
    em.add_field(inline=False, name=".new", value="Shows all the locations that have been added during this session")
    await ctx.send(embed=em)


# ping command
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command(aliases=['time'])
async def date(ctx):
    """Find's the current date using the time_tracker.py"""
    date, time, round, weekday = format_date(*get_time())

    desc = "**Date:** %s\n**Time:** %s" % (date, time)
    if round != 0:
        desc += "\n**Round:** %d" % round
    em = discord.Embed(title="Date (%s)" % weekday, description=desc, color=embed_color)

    await ctx.send(embed=em)


# returns the current food, or increments the amount of food
@bot.command()
async def food(ctx, amount=None):
    if amount is None:
        await ctx.send('`%d` food remaining!' % get_food())
        return

    amount = int(amount)
    remaining = add_food(amount)
    await ctx.send("`%d` food added! `%d` food remaining!" % (amount, remaining))


# Returns all conditions active, and when they expire
@bot.command(aliases=['conditions', 'conds'])
async def active(ctx):
    # TODO make this work with the 25 field limit
    em = discord.Embed(title="Conditions:", color=embed_color)
    for k, v in get_conditions().items():
        date, time, round, weekday = format_date(*v)
        formatted_str = "%s %s" % (date, time) if round == 0 else "%s %s.%d" % (date, time, round)
        em.add_field(name=k, value="Expires on: " + formatted_str, inline=False)
    await ctx.send(embed=em)


# adds a condition
@bot.command(aliases=['condition', 'cond'])
async def infect(ctx, amount=0, time="", *text):
    try:
        amount = int(amount)
    except TypeError:
        await ctx.send("`%s` is not a valid number!" % amount)
        return

    duration = convert_duration(time)
    if duration is None:  # is not a valid duration
        await ctx.send("`%s` is not a valid duration!")
        return
    if len(text) == 0:
        await ctx.send("No condition description listed!")
        return
    add_condition(' '.join(text), amount, duration)

    await active(ctx)


# advances the time in game, and if a day passes, asks the user to enter the number of rations to consume (how many
# party members are currently playing)
@bot.command()
async def advance(ctx, amount=0, time=""):
    try:
        amount = int(amount)
    except TypeError:
        await ctx.send("`%s` is not a valid number!" % amount)
        return

    duration = convert_duration(time)
    if duration is None:  # is not a valid duration
        await ctx.send("`%s` is not a valid duration!")
        return

    days = advance_time(amount, duration)

    # show .date
    await date(ctx)

    global finished_conditions
    if len(finished_conditions) > 0:  # some conditions finished
        await ctx.send(embed=discord.Embed(title="The following conditions expired:",
                                           description="\n".join(finished_conditions), color=embed_color))
        finished_conditions = []

    if days > 0:  # if a day passed
        await ctx.send("A day has passed! How many people are you supplying food to?")
        try:
            # wait for the user to give an amount of food to use
            msg = await bot.wait_for('message', check=(lambda m: m.channel == ctx.channel), timeout=30)
            food = int(msg.content)
            remaining = add_food(-food)
            await ctx.send("`%d` food removed! `%d` remaining!" % (food, remaining))
        except asyncio.TimeoutError:
            await ctx.send("No response received.")


@bot.command()
async def loc(ctx, addr=None, *str):
    # if specific address, then show specific, otherwise show all
    if addr is None:
        first = "ABCDEFGHIJKLMNOPQR"
        second = "0123456789X"
        em = discord.Embed(title="Location", color=embed_color)

        # TODO, make this work with the 25 field limit for embeds.
        for c1 in first:  # create all the addresses
            for c2 in second:
                locs = at_location(location_indices(c1 + c2))
                if len(locs) > 0:
                    names = []
                    for loc in locs:  # for each address get the name

                        # if comma, then everything to comma, otherwise done
                        index_of_comma = loc.find(', ')
                        loc_name = loc[:index_of_comma]

                        # get the name of the location, and add a bullet point before it
                        names.append("\u2022 " + loc_name)

                    # add the embed for the given location
                    em.add_field(name=c1 + c2, value='\n'.join(names), inline=False)
        await ctx.send(embed=em)
        return

    # If provided a address parameter, then find the address
    addr_tuple = location_indices(addr)

    if len(str) != 0:  # if given a location to add, add that location
        add_location(addr_tuple, " ".join(str))

    arr = at_location(addr_tuple)  # list of locations at this place
    em = discord.Embed(title="Location (%s)" % addr, color=embed_color)

    for s in arr:
        split = s.find(', ')
        em.add_field(name=s[:split], value=s[split + 1:] + "\u200b", inline=False)
    await ctx.send(embed=em)


@bot.command()
async def map(ctx):  # displays the map of the world.
    em = discord.Embed(title="Map", color=embed_color)
    em.set_image(url='https://cdn.discordapp.com/attachments/450305957185060864/793889427565838386/road.png')
    await ctx.send(embed=em)


@bot.command()
async def peek(ctx, channel: discord.TextChannel):
    arr = []
    async for message in channel.history(limit=5):
        s = "%s\n%s\n" % (message.author.mention, message.content)
        if len(message.attachments) > 0:
            for attach in message.attachments:
                s += attach.url + "\n"
        arr.append(s)
    await ctx.send(embed=discord.Embed(title="#" + channel.name, description="\n".join(arr), color=embed_color))


@bot.command(aliases=['prev', 'previous'])
async def recap(ctx):
    await ctx.send(embed=discord.Embed(title="Recap:", description="\n".join(previously_added()), color=embed_color))


@bot.command(aliases=['current'])
async def new(ctx):
    await ctx.send(embed=discord.Embed(title="Newly Added Locations:",
                                       description="\n".join(currently_added()), color=embed_color))


# run with hidden token
with open('data/token.txt', 'r') as f:
    bot.run(f.read())

# .map
# .recap (all locations added)
