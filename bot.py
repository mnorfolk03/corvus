# Corvus created by Max Norfolk
import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import errors
from time_tracker import *
from date_formatter import format_date

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')  # do not use default help, instead use a custom one making use of embeds


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
        await ctx.send('{} the following error occurred: `{}`.'.format(ctx.author.mention, str(error)))


# block dms
@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# basic help command
@bot.command()
async def help(ctx):
    em = discord.Embed(title="Help", color=0x42810a)
    em.add_field(inline=False, name=".ping", value="Tests whether the bot is online")
    em.add_field(inline=False, name=".help", value="Shows this message")
    em.add_field(inline=False, name=".food",
                 value="Returns the amount of food remaining or adds the given amount to your total food")
    em.add_field(inline=False, name=".date", value="Returns the current date and time in-game")

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
    if (round != 0):
        desc += "\n**Round:** %d" % round
    em = discord.Embed(title="Date (%s)" % weekday, description=desc,
                       color=0x42810a)

    await ctx.send(embed=em)

# returns the current food, or increments the amount of food
@bot.command()
async def food(ctx, amount=None):
    if amount == None:
        await ctx.send('`%d` food remaining!' % get_food())
        return

    amount = int(amount)
    remaining = add_food(amount)
    await ctx.send("`%d` food added! `%d` food remaining!" % (amount, remaining))


# advances the time in game, and if a day passes, asks the user to enter the number of rations to consume (how many
# party members are currently playing)
@bot.command()
async def advance(ctx, amount=0, time=""):
    try:
        amount = int(amount)
    except TypeError:
        ctx.send("`%s` is not a valid number!" % amount)
        return

    time = time.upper()
    if time in ['D', 'DAY', 'DAYS']: # determine what duration they meant
        duration = Duration.DAY
    elif time in ['H', 'HOUR', 'HOURS']:
        duration = Duration.HOUR
    elif time in ['M', 'MIN', 'MINS', 'MINUTE', 'MINUTES']:
        duration = Duration.MINUTE
    elif time in ['R', 'ROUND', 'ROUNDS']:
        duration = Duration.ROUND
    else:
        ctx.send("`%s` is not a valid duration!")
        return
    days = advance_time(amount, duration)

    # show .date
    await date(ctx)

    if days > 0: # if a day passed
        await ctx.send("A day has passed! How many people are you supplying food to?")
        try:
            # wait for the user to give an amount of food to use
            msg = await bot.wait_for('message', check=(lambda m: m.channel == ctx.channel), timeout=30)
            food = int(msg.content)
            remaining = add_food(-food)
            await ctx.send("`%d` food removed! `%d` remaining!" % (food, remaining))
        except asyncio.TimeoutError:
            await ctx.send("No response received.")


# run with hidden token
with open('data/token.txt', 'r') as f:
    bot.run(f.read())
