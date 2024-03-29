# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import ArgumentParser
from collections import deque

from shapely.geometry import Polygon

from ufg import Direction
from fuzz import main

"""
deque([(0, 0),
       (1, -2),
       (4, -3),
       (-3, -5),
       (-5, -4),
       (-5, -3),
       (-8, -16),
       (-8, -18),
       (-6, -18),
       (-4, -21),
       (-2, -21),
       (-2, -19),
       (-3, -19),
       (-3, -20),
       (-7, -15),
       (-7, -14),
       (-1, -11),
       (-4, -14),
       (-5, -15),
       (-6, -14),
       (-6, -15),
       (-4, -17),
       (-1, -15),
       (-1, -16),
       (0, -16),
       (0, -15),
       (3, -15),
       (6, -16),
       (4, -13),
       (4, -14),
       (2, -13),
       (19, 0)])
deque([None,
       <Direction.EAST: (1, 0)>,
       None,
       None,
       <Direction.NORTH: (0, 1)>,
       None,
       <Direction.SOUTH: (0, -1)>,
       <Direction.EAST: (1, 0)>,
       <Direction.SOUTH: (0, -1)>,
       None,
       None,
       None,
       None,
       None,
       <Direction.NORTH: (0, 1)>,
       None,
       None,
       <Direction.WEST: (-1, 0)>,
       None,
       None,
       None,
       None,
       None,
       None,
       None,
       None,
       None,
       None,
       None,
       <Direction.NORTH: (0, 1)>,
       <Direction.NORTH: (0, 1)>,
       None])
(((9.0, -1.0, 13.0, 1.0), <Direction.WEST: (-1, 0)>),
 ((17.0, -22.0, 21.0, -20.0), <Direction.WEST: (-1, 0)>),
 ((7.0, 0.0, 9.0, 4.0), <Direction.SOUTH: (0, -1)>),
 ((-1.0, -10.0, 3.0, -8.0), <Direction.WEST: (-1, 0)>),
 ((5.0, -17.0, 9.0, -15.0), <Direction.WEST: (-1, 0)>))
"""
points = deque(
    [
        (0, 0),
        (1, -2),
        (4, -3),
        (-3, -5),
        (-5, -4),
        (-5, -3),
        (-8, -16),
        (-8, -18),
        (-6, -18),
        (-4, -21),
        (-2, -21),
        (-2, -19),
        (-3, -19),
        (-3, -20),
        (-7, -15),
        (-7, -14),
        (-1, -11),
        (-4, -14),
        (-5, -15),
        (-6, -14),
        (-6, -15),
        (-4, -17),
        (-1, -15),
        (-1, -16),
        (0, -16),
        (0, -15),
        (3, -15),
        (6, -16),
        (4, -13),
        (4, -14),
        (2, -13),
        (19, 0),
    ]
)
directions = deque(
    [
        None,
        Direction.EAST,
        None,
        None,
        Direction.NORTH,
        None,
        Direction.SOUTH,
        Direction.EAST,
        Direction.SOUTH,
        None,
        None,
        None,
        None,
        None,
        Direction.NORTH,
        None,
        None,
        Direction.WEST,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        Direction.NORTH,
        Direction.NORTH,
        None,
    ]
)
pads = deque()
for (x1, y1, x2, y2), direction in (
    ((9.0, -1.0, 13.0, 1.0), Direction.WEST),
    ((17.0, -22.0, 21.0, -20.0), Direction.WEST),
    ((7.0, 0.0, 9.0, 4.0), Direction.SOUTH),
    ((-1.0, -10.0, 3.0, -8.0), Direction.WEST),
    ((5.0, -17.0, 9.0, -15.0), Direction.WEST),
):
    pad = Polygon(((x1, y1), (x2, y1), (x2, y2), (x1, y2)))
    pad.direction = direction
    pads.append(pad)
pads = tuple(pads)

parser = ArgumentParser(allow_abbrev=False)
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()
main(points, directions, pads, debug=args.verbose)
