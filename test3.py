# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import ArgumentParser
from collections import deque

from shapely.geometry import Polygon

from ufg import Direction
from fuzz import main

"""
deque([(0, 0), (2, 1), (7, 5), (12, 6), (3, 1), (5, 2), (17, 7), (17, 9), (10, 12)])
deque([<Direction.EAST: (1, 0)>,
       None,
       <Direction.EAST: (1, 0)>,
       <Direction.SOUTH: (0, -1)>,
       <Direction.EAST: (1, 0)>,
       None,
       None,
       None,
       <Direction.SOUTH: (0, -1)>])
((10.0, 1.0, 12.0, 5.0),
 (2.0, 5.0, 6.0, 7.0),
 (13.0, 11.0, 17.0, 13.0),
 (15.0, -2.0, 17.0, 2.0),
 (15.0, -3.0, 17.0, 1.0))
"""
points = deque(
    [
        (0, 0),
        (2, 1),
        (7, 5),
        (12, 6),
        (3, 1),
        (5, 2),
        (17, 7),
        (17, 9),
        (10, 12),
    ]
)
directions = deque(
    [
        Direction.EAST,
        None,
        Direction.EAST,
        Direction.SOUTH,
        Direction.EAST,
        None,
        None,
        None,
        Direction.SOUTH,
    ]
)
pads = deque()
for x1, y1, x2, y2 in (
    (10.0, 1.0, 12.0, 5.0),
    (2.0, 5.0, 6.0, 7.0),
    (13.0, 11.0, 17.0, 13.0),
    (15.0, -2.0, 17.0, 2.0),
    (15.0, -3.0, 17.0, 1.0),
):
    pad = Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))
    if x2 - x1 > y2 - y1:
        pad.direction = Direction.EAST
    else:
        pad.direction = Direction.SOUTH
    pads.append(pad)
pads = tuple(pads)

parser = ArgumentParser(allow_abbrev=False)
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()
main(points, directions, pads, debug=args.verbose)
