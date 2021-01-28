# this is used to keep track of time and the like

import json
from enum import Enum
from math import ceil
from typing import Tuple, Dict

__all__ = ['advance_time', 'add_food', 'Duration', 'nearest_minute', 'get_time', 'get_food', 'add_condition',
           'get_conditions', 'set_on_condition_expire']

time_file_path = 'data/time.json'
save_states_file_path = 'data/save_states.json'

time_map = {}
save_states = []  # TODO add save states

DATE = 'date'
TIME = 'time'
FOOD = 'food'
CONDITIONS = 'conditions'

# This function is called on a condition expiring. This should be set to something else to be used.
on_condition_expire = lambda name: None


class Duration(Enum):
    """Duration is used to keep track of time. The value of the enum constant is how many rounds it is."""
    ROUND = 1
    MINUTE = 10
    HOUR = 600
    DAY = 14400


def write_states():
    """Writes the current values to the files"""
    time_f = open(time_file_path, 'w')
    save_states_f = open(save_states_file_path, 'w')

    time_f.write(json.dumps(time_map, indent=2))
    save_states_f.write(json.dumps(save_states, indent=2))

    time_f.close()
    save_states_f.close()


def read_states():
    """Reads the current values from the file, and replaces the current values with them (only useful on start)"""
    time_f = open(time_file_path, 'r')
    save_states_f = open(save_states_file_path, 'r')

    global time_map, save_states

    try:
        time_map = json.loads(time_f.read())
        s = save_states_f.read()
        save_states = json.loads(s)
    except json.decoder.JSONDecodeError:
        time_map = {
            FOOD: 0,  # days of rations left
            TIME: 0,  # current time in rounds the maximum is minutes in a day * rounds in a minute (1440 * 10)
            DATE: 0,  # the current day
            CONDITIONS: {}
        }
        write_states()

    time_f.close()
    save_states_f.close()


def add_condition(con: str, length: int, dur_type: Duration):
    """
    adds a condition for a given length of dur_type
    """
    if dur_type == Duration.DAY:  # if day, we can skip be a bit more efficient
        expire_time = time_map[TIME]  # the time will be the same regardless of how many days added
        expire_day = time_map[DATE] + length
    else:
        real_length = length * dur_type.value  # the real length of time

        # if the condition takes place in 5 minutes or more, then rounds are irrelevant
        current_time = nearest_minute(time_map[TIME]) if real_length > 500 else time_map[TIME]

        expire_day, expire_time = divmod(real_length + current_time, Duration.DAY.value)
        expire_day += time_map[DATE]

    # store the value
    time_map[CONDITIONS][con] = [expire_day, expire_time]
    write_states()


def check_conditions():
    """Checks conditions and sees whether they are true or if they have expired"""

    all_expired = []

    for con_name, (expire_date, expire_time) in time_map[CONDITIONS].items():
        # the date it expires has not yet happened (and it is not today),
        # so the condition is still active, skip to next one
        if expire_date > time_map[DATE]:
            continue

        elif expire_date == time_map[DATE]:  # same date but the time might not have happened
            if expire_time > time_map[TIME]:  # if the time hasn't happened yet, then we continue
                continue

        # it has expired, now handle this
        on_condition_expire(con_name)  # call the on_condition_expire handler
        all_expired.append(con_name)

    # this extra loop is because the size of the dict cannot change while iterating through it
    for name in all_expired:
        del time_map[CONDITIONS][name]  # delete the condition name, and continue to next one


def get_conditions() -> Dict[str, Tuple[int, int]]:
    """Returns a mapping of time the event expires to its name"""
    return time_map[CONDITIONS]


def get_food() -> int:
    """Returns the amount of food the players currently have"""
    return time_map[FOOD]


def add_food(amount: int) -> int:
    """Adds food to the players amount, and returns the amount of food"""
    time_map[FOOD] += amount
    write_states()
    return time_map[FOOD]


def nearest_minute(value: int) -> int:
    """rounds up the rounds unless the round is 0"""
    return int(ceil(value / 10)) * 10


def get_time() -> Tuple[int, int]:
    """Returns the current date and time formatted as a tuple such that it is (date, time)"""
    return time_map[DATE], time_map[TIME]


def advance_time(amount: int, length: Duration, correct: bool = True) -> int:
    """Advances time the given amount of lengths. Then returns the number of days that have passed
    if correct is true and if the length is not a round, it will automatically update rounds to the nearest minute"""
    real_amount = amount * length.value

    if correct and length != Duration.ROUND:
        time_map[TIME] = nearest_minute(time_map[TIME])

    days, time_map[TIME] = divmod(real_amount + time_map[TIME], Duration.DAY.value)
    time_map[DATE] += days
    check_conditions()
    write_states()
    return days


# Sets the handler used on a condition expire
def set_on_condition_expire(handler):
    global on_condition_expire
    on_condition_expire = handler


read_states()
