# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from argparse import ArgumentParser
from collections import deque
from itertools import count
import logging
from math import pi, cos, sin, atan2
from random import vonmisesvariate, lognormvariate, choices, randint

import numpy as np

from shapely.geometry import LineString, Polygon

import matplotlib.pyplot as plt

import ufg
from ufg import linewise, Direction, plot


def calc(r, theta):
    dx = int(r * cos(theta))
    dy = int(r * sin(theta))
    theta = atan2(dy, dx)
    return dx, dy, theta


def main(points, directions, pads, debug=False):
    if debug:
        logging.getLogger("ufg").setLevel(logging.DEBUG)
    plot(points, directions, pads, debug=debug)
    plt.show()


if __name__ == "__main__":
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("n_points", type=int)
    parser.add_argument("r_mu", type=float)
    parser.add_argument("r_sigma", type=float)
    parser.add_argument("theta_kappa", type=float)
    parser.add_argument("max_attempts", type=int)
    parser.add_argument("direction_weight", type=float)
    parser.add_argument("n_pads", type=int)
    parser.add_argument("margin", type=int)
    parser.add_argument("pad_dx", type=int)
    parser.add_argument("pad_dy", type=int)
    args = parser.parse_args()

    points = deque(((0, 0),))
    first = True
    for point_index in count(1):
        if point_index >= args.n_points and Polygon(points).is_valid:
            break
        for attempt_index in range(args.max_attempts):
            r = lognormvariate(args.r_mu, args.r_sigma)
            if first:
                next_theta = vonmisesvariate(0, 0)
            else:
                next_theta = vonmisesvariate((theta + 2 * pi / args.n_points) % (2 * pi), args.theta_kappa)
            dx, dy, next_theta = calc(r, next_theta)
            if dx == 0 and dy == 0:
                continue
            next_point = tuple(np.array(points[-1]) + np.array((dx, dy)))
            if LineString(tuple(points) + (next_point,)).is_simple:
                break
        else:
            raise RuntimeError(f"giving up after {attempt_index + 1} attempt(s)")
        points.append(next_point)
        theta = next_theta
    body = Polygon(points)

    directions = deque()
    for line_index, line in linewise(points):
        np_line = np.array(line[1]) - np.array(line[0])
        weights = tuple(
            max((np_line / np.linalg.norm(np_line)).dot(np.array(direction.value)), 0) for direction in Direction
        )
        directions.append(
            choices(
                tuple(Direction) + (None,),
                tuple(args.direction_weight * np.array(weights) / sum(weights)) + (1 - args.direction_weight,),
            )[0]
        )

    pads = deque()
    for pad_index in range(args.n_pads):
        x = randint(body.bounds[0] - args.margin, body.bounds[2] + args.margin)
        y = randint(body.bounds[1] - args.margin, body.bounds[3] + args.margin)
        direction = choices(tuple(Direction))[0]
        if direction in (Direction.EAST, Direction.WEST):
            dx = args.pad_dx
            dy = args.pad_dy
        else:
            dx = args.pad_dy
            dy = args.pad_dx
        pad = Polygon(
            np.array((x, y))
            + np.array(((-dx / 2, -dy / 2), (+dx / 2, -dy / 2), (+dx / 2, +dy / 2), (-dx / 2, +dy / 2)))
        )
        pad.direction = direction
        pads.append(pad)
    pads = tuple(pads)

    print(points)
    print(directions)
    print(tuple((pad.bounds, pad.direction) for pad in pads))

    main(points, directions, pads, debug=args.verbose)
