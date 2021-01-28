# Locations is used to keep track of where buildings and such are stored
# This follows a grid system which consists of two alphanumeric characters. A-R for row, and 0-9, X for column
import json
from typing import Tuple

__all__ = ['location_indices', 'add_location', 'at_location', 'currently_added', 'previously_added']

loc_file_path = "data/locations.json"
loc = None

prev_file_path = "data/previous.json"  # keeps track of all files added the last time it was run

prev = None
# this is set when the state is read, but is never touched again. The values that are being updated is put into new_prev
# and when writeStates() is called, it makes use of new_prev as well.


new_prev = set()  # this is used when things are added


def write_states():
    """Writes the current values to the files"""
    loc_file = open(loc_file_path, 'w')
    prev_file = open(prev_file_path, 'w')

    loc_file.write(json.dumps(loc, indent=2))
    prev_file.write(json.dumps(tuple(new_prev), indent=2))

    loc_file.close()
    prev_file.close()


def read_states():
    """Reads the current values from the file, and replaces the current values with them (only useful on start)"""
    loc_file = open(loc_file_path, 'r')
    prev_file = open(prev_file_path, 'r')

    global loc, prev

    try:
        loc = json.loads(loc_file.read())
        prev = json.loads(prev_file.read())
    except json.decoder.JSONDecodeError:

        # 3d array of strings String[18][11][...] this 3d [] is used for storing which locations are at this address
        loc = [[[] for _ in range(11)] for _ in range(18)]

        prev = []  # empty list
        write_states()

    loc_file.close()
    prev_file.close()


def location_indices(s: str) -> Tuple[int, int]:
    # converts the string to a tuple of indices
    s = s.lower()

    def convert_char(c):
        # returns a tuple with a int 0 if it is row, and 1 if it column and the value to put at that index

        if ord('a') <= ord(c) <= ord('r'):  # if A-R
            return (0, ord(c) - ord('a'))
        try:
            return (1, int(c))  # if 0-9
        except ValueError:
            if c == 'x':
                return (1, 10)  # if X
            raise SyntaxError("Invalid character: %s" % c)

    arr = [None, None]
    t1 = convert_char(s[0])  # 1st char
    arr[t1[0]] = t1[1]

    t1 = convert_char(s[1])  # 2nd char
    arr[t1[0]] = t1[1]

    return tuple(arr)


def add_location(address: Tuple[int, int], s: str) -> None:
    arr = loc[address[0]][address[1]]
    index_of_comma = s.find(', ')

    if index_of_comma < 0:  # if doesn't end have ', ' paste it to the end, else get everything up to ', '
        s += ', '
        index_of_comma = -2 # -2 because of the space

    loc_name = s[:index_of_comma].upper()

    for i, val in enumerate(arr):
        if val[:val.find(', ')].upper() == loc_name:
            arr[i] = s
            break

    else:
        arr.append(s)

    new_prev.add(loc_name.capitalize())

    write_states()


def at_location(address: Tuple[int, int]) -> Tuple[str, ...]:
    return tuple(loc[address[0]][address[1]])


# returns the locations that were added the last time this was run
def previously_added() -> Tuple[str, ...]:
    return tuple(prev)


# returns the locations that were added in this current session (session being currently running)
def currently_added() -> Tuple[str, ...]:
    return tuple(new_prev)


read_states()
