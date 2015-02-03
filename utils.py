import math
from math import sqrt
# From http://stackoverflow.com/q/354038
def is_int (num):
    try:
        int(num)
        return True
    except ValueError:
        return False

def average(x):
    assert len(x) > 0
    return float(sum(x)) / len(x)

def pearson_def(x, y):
    assert len(x) == len(y)
    n = len(x)
    if n == 0:
        return 0
#    assert n > 0
    avg_x = average(x)
    avg_y = average(y)
    diffprod = 0
    xdiff2 = 0
    ydiff2 = 0
    for idx in range(n):
        xdiff = x[idx] - avg_x
        ydiff = y[idx] - avg_y
        diffprod += xdiff * ydiff
        xdiff2 += xdiff * xdiff
        ydiff2 += ydiff * ydiff

    return diffprod / (math.sqrt(xdiff2 * ydiff2) + 0.001) # added 0.001 to avoid division by zero
