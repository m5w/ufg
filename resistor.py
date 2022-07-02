# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from ufg import *


points = deque(((-4, -2), (+4, -2), (+4, +2), (-4, +2)))
directions = deque((None, Direction.NORTH, None, Direction.SOUTH))
pads = (Polygon(((-5, -3), (-3, -3), (-3, +3), (-5, +3))), Polygon(((+3, -3), (+5, -3), (+5, +3), (+3, +3))))
pads[0].direction = Direction.WEST
pads[1].direction = Direction.EAST


plot(points, directions, pads)
