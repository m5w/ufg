from ufg import *


points = deque(((-3, -6), (+3, -6), (+6, -3), (+6, +3), (+3, +6), (-3, +6), (-6, +3), (-6, -3)))
directions = deque((Direction.EAST, None, Direction.NORTH, None, Direction.WEST, None, Direction.SOUTH, None))
pads = (
    Polygon(((-4, -9), (-2, -9), (-2, -5), (-4, -5))),
    Polygon(((-1, -9), (+1, -9), (+1, -5), (-1, -5))),
    Polygon(((+2, -9), (+4, -9), (+4, -5), (+2, -5))),
    Polygon(((+5, -4), (+9, -4), (+9, -2), (+5, -2))),
    Polygon(((+5, -1), (+9, -1), (+9, +1), (+5, +1))),
    Polygon(((+5, +2), (+9, +2), (+9, +4), (+5, +4))),
    Polygon(((-4, +5), (-2, +5), (-2, +9), (-4, +9))),
    Polygon(((-1, +5), (+1, +5), (+1, +9), (-1, +9))),
    Polygon(((+2, +5), (+4, +5), (+4, +9), (+2, +9))),
    Polygon(((-9, -4), (-5, -4), (-5, -2), (-9, -2))),
    Polygon(((-9, -1), (-5, -1), (-5, +1), (-9, +1))),
    Polygon(((-9, +2), (-5, +2), (-5, +4), (-9, +4))),
)
for i in range(0, 3):
    pads[i].direction = Direction.SOUTH
for i in range(3, 6):
    pads[i].direction = Direction.EAST
for i in range(6, 9):
    pads[i].direction = Direction.NORTH
for i in range(9, 12):
    pads[i].direction = Direction.WEST


plot(points, directions, pads)
