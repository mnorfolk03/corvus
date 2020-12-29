# this is used to keep track of time and the like

import json
from enum import Enum
from math import ceil
from typing import Tuple

__all__ = ['writeStates', 'advance_time', 'add_food', 'Duration', 'nearest_minute', 'get_time', 'get_food']

time_file = 'data/time.json'
save_states_file = 'data/save_states.json'

time = {}
save_states = [] # TODO add save states


class Duration(Enum):
    """Duration is used to keep track of time. The value of the enum constant is how many rounds it is."""
    ROUND = 1
    MINUTE = 10
    HOUR = 600
    DAY = 14400


def writeStates():
    """Writes the current values to the files"""
    time_f = open(time_file, 'w')
    save_states_f = open(save_states_file, 'w')

    time_f.write(json.dumps(time, indent=2))
    save_states_f.write(json.dumps(save_states, indent=2))


def readStates():
    """Reads the current values from the file, and replaces the current values with them (only useful on start)"""
    time_f = open(time_file, 'r')
    save_states_f = open(save_states_file, 'r')

    global time, save_states

    try:
        time = json.loads(time_f.read())
        s = save_states_f.read()
        save_states = json.loads(s)
    except json.decoder.JSONDecodeError:
        time = {
            'food': 0,  # days of rations left
            'time': 0,  # current time in rounds the maximum is minutes in a day * rounds in a minute (1440 * 10)
            'date': 0,  # the current day
            'conditions': []
        }
        writeStates()


def add_condition(con: str, length: int, dur_type: Duration):
    """
    adds a condition for a given length of dur_type
    """


# TODO add conditions, and keep track of when they expire


def get_food() -> int:
    """Returns the amount of food the players currently have"""
    return time['food']


def add_food(amount: int) -> int:
    """Adds food to the players amount, and returns the amount of food"""
    time['food'] += amount
    writeStates()
    return time['food']


def nearest_minute() -> None:
    """rounds up the rounds unless the round is 0"""
    time['time'] = int(ceil((time['time']) / 10))


def get_time() -> Tuple[int, int]:
    """Returns the current date and time formatted as a tuple such that it is (date, time)"""
    return time['date'], time['time']


def advance_time(amount: int, length: Duration) -> int:
    """Advances time the given amount of lengths. Then returns the number of days that have passed"""
    real_amount = amount * length.value
    days, time['time'] = divmod(real_amount + time['time'], Duration.DAY.value)
    time['date'] += days
    writeStates()
    return days


readStates()
