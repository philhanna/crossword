def get_elapsed_time(stime, etime):
    diff = etime - stime
    seconds = diff.seconds + diff.microseconds / 1000000
    return seconds
