from time_tracker import Duration

# weekday names in this game
weekday_names = ["Nobis", "Quod", "Populus", "Forma", "Gentem"]


def extract(days, time):
    quint, day = divmod(days, 5)  # a quint is 5 days (and is used to keep track of days)
    hour, time = divmod(time, Duration.HOUR.value)
    minute, time = divmod(time, Duration.MINUTE.value)
    return (quint, day, hour, minute, time)


def format_date(days, time):
    """returns a tuple consisting of the date, time, round, and weekday formatted nicely"""
    split = list(extract(days, time))
    split[0] += 1
    split[1] += 1  # day and week should be +1

    date_str = "%d-%d" % (split[0], split[1])
    time_str = "%02d:%02d" % (split[2], split[3])

    return (date_str, time_str, split[-1], weekday_names[(split[1] - 1) % len(weekday_names)])
