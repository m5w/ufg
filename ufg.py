# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import deque
from enum import Enum
import logging

import numpy as np

from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import Polygon
from shapely.ops import linemerge

import matplotlib.pyplot as plt


logging.basicConfig()
logger = logging.getLogger(__name__)


def linewise(points):
    for point1_index, point1 in enumerate(points):
        point2_index = point1_index + 1
        point2_index %= len(points)
        yield point1_index, (point1, points[point2_index])


def linewise3(points, start_point_index, stop_point_index, step):
    point_metaindex_stop = (stop_point_index - start_point_index) // step % len(points)
    if point_metaindex_stop == 0:
        point_metaindex_stop = len(points)
    for point_metaindex in range((stop_point_index - start_point_index) // step % len(points)):
        point1_index = start_point_index + step * point_metaindex
        point2_index = point1_index + 1
        point1_index %= len(points)
        point2_index %= len(points)
        yield point1_index, ((points[point1_index], points[point2_index]))


N_DIMENSIONS = 2


class Direction(Enum):
    EAST = (+1, 0)
    WEST = (-1, 0)
    NORTH = (0, +1)
    SOUTH = (0, -1)

    def is_perpendicular_to(self, other):
        if other is None:
            return False
        for dimension in range(N_DIMENSIONS):
            if self.value[dimension] != 0:
                return other.value[dimension] == 0


def is_proj_zero(l, direction):
    for dimension in range(N_DIMENSIONS):
        if direction.value[dimension] != 0:
            return l[1][dimension] - l[0][dimension] == 0


def is_proj_negative_to(m, direction, l):
    for dimension in range(N_DIMENSIONS):
        if direction.value[dimension] != 0:
            return (m[1][dimension] - m[0][dimension]) / (l[1][dimension] - l[0][dimension]) < 0


def find_last_positive_proj_line(points, directions, pad, line_index, line, step):
    last_positive_proj_line_index = line_index
    next_last_positive_proj_line_index = line_index
    _debug_next_last_positive_proj_line = line
    already_found_perpendicular_line = False
    logger.debug(
        #
        f"searching { {+1: 'counter-clockwise', -1: 'clockwise'}[step] } for "
        f"last line positive to {line} with respect to {pad.bounds} "
        f"({pad.direction.name})"
    )
    for forward_line_index, forward_line in linewise3(points, line_index + step, line_index, step):
        if pad.direction.is_perpendicular_to(directions[forward_line_index]):
            logger.debug(
                #
                f"{forward_line} is perpendicular to {pad.bounds} "
                f"({pad.direction.name})"
            )
            already_found_perpendicular_line = True
            continue
        if is_proj_zero(forward_line, pad.direction):
            logger.debug(
                #
                f"{forward_line} is zero to {pad.bounds} "
                f"({pad.direction.name})"
            )
            continue
        if is_proj_negative_to(forward_line, pad.direction, line):
            logger.debug(
                #
                f"{forward_line} is negative to {line} with respect to {pad.bounds} "
                f"({pad.direction.name})"
            )
            logger.debug(f"selecting {_debug_next_last_positive_proj_line}")
            last_positive_proj_line_index = next_last_positive_proj_line_index
            if already_found_perpendicular_line:
                break
            continue
        if already_found_perpendicular_line:
            logger.debug(f"already found perpendicular line, so ignoring {forward_line}")
            continue
        logger.debug(f"marking {forward_line}")
        next_last_positive_proj_line_index = forward_line_index
        _debug_next_last_positive_proj_line = forward_line
    logger.debug("done")
    return last_positive_proj_line_index


def is_line_string_valid(points, line_index, first_positive_proj_line_index, last_positive_proj_line_index):
    return 1 + (line_index - first_positive_proj_line_index) % len(points) + (
        last_positive_proj_line_index - line_index
    ) % len(points) < len(points)


def get_expand_direction(line, direction):
    for dimension, expand_direction in zip(range(N_DIMENSIONS), (Direction.SOUTH, Direction.EAST)):
        if direction.value[dimension] != 0:
            proj = line[1][dimension] - line[0][dimension]
            return Direction(tuple(proj / abs(proj) * x for x in expand_direction.value))


def _expand(points, directions, pads):
    for line_index, line in linewise(points):
        for pad in pads:
            line_string = LineString(line)
            if not (line_string.intersects(pad) and not line_string.touches(pad)):
                continue
            if pad.direction.is_perpendicular_to(directions[line_index]):
                continue
            if is_proj_zero(line, pad.direction):
                continue
            first_positive_proj_line_index = find_last_positive_proj_line(
                points, directions, pad, line_index, line, -1
            )
            last_positive_proj_line_index = find_last_positive_proj_line(
                points, directions, pad, line_index, line, +1
            )
            if not is_line_string_valid(
                points, line_index, first_positive_proj_line_index, last_positive_proj_line_index
            ):
                continue
            expand_direction = get_expand_direction(line, pad.direction)
            for dimension in range(N_DIMENSIONS):
                if expand_direction.value[dimension] != 0:
                    break
            translation = (
                pad.bounds[N_DIMENSIONS * (expand_direction.value[dimension] > 0) + dimension]
                - line_string.bounds[N_DIMENSIONS * (expand_direction.value[dimension] < 0) + dimension]
            )
            logger.debug(
                f"translating {points[first_positive_proj_line_index]} through "
                f"{points[(last_positive_proj_line_index + 1) % len(points)]}, inclusive, "
                f"{translation} {expand_direction.name}"
            )
            if translation < 0:
                logger.debug(
                    #
                    "note: WEST and SOUTH translations are negative.  "
                    "'-1.0 WEST' means '1.0 to the west'."
                )
            new_points = points.copy()
            new_directions = directions.copy()
            for point_metaindex in range(
                ((last_positive_proj_line_index + 2) - first_positive_proj_line_index) % len(new_points)
            ):
                point_index = first_positive_proj_line_index + point_metaindex
                point_index %= len(new_points)
                new_points[point_index] = tuple(
                    x + translation if point_dimension == dimension else x
                    for point_dimension, x in enumerate(new_points[point_index])
                )
            insert_point_queue = deque(
                (
                    (
                        first_positive_proj_line_index,
                        points[first_positive_proj_line_index],
                        0,
                    ),
                    (
                        last_positive_proj_line_index + 2,
                        points[(last_positive_proj_line_index + 1) % len(points)],
                        1,
                    ),
                )
            )
            while len(insert_point_queue) > 0:
                index, point, append = insert_point_queue.popleft()
                index %= len(new_points)
                if index == 0:
                    index = len(new_points) * append
                new_points.insert(index, point)
                for queue_index, (future_index, future_point, future_append) in enumerate(insert_point_queue):
                    if future_index < index:
                        continue
                    insert_point_queue[queue_index] = (future_index + 1, future_point, future_append)
            insert_direction_queue = deque(
                (
                    first_positive_proj_line_index,
                    last_positive_proj_line_index + 1,
                )
            )
            while len(insert_direction_queue) > 0:
                index = insert_direction_queue.popleft()
                index %= len(new_directions)
                new_directions.insert(index, None)
                for queue_index, future_index in enumerate(insert_direction_queue):
                    if future_index < index:
                        continue
                    insert_direction_queue[queue_index] = future_index + 1
            return (True, new_points, new_directions)
    return (False,)


def _make_valid(points, directions):
    for line_index, line in linewise(points):
        for other_line_index, other_line in linewise3(points, line_index + 2, line_index - 1, +1):
            if not LineString(line).intersects(LineString(other_line)):
                continue
            perpendicular_vector = np.cross(
                np.concatenate((np.array(line[1]) - np.array(line[0]), (0,))),
                np.concatenate((np.zeros(N_DIMENSIONS), (1,))),
            )
            dot = np.dot(np.array(other_line[1]) - np.array(other_line[0]), perpendicular_vector[:-1])
            if dot == 0:
                continue
            if dot > 0:
                start_index, stop_index = line_index, other_line_index
            else:
                start_index, stop_index = other_line_index, line_index
            new_points = points.copy()
            new_directions = directions.copy()
            new_directions[start_index] = None
            start_index += 1
            stop_index += 1
            start_index %= len(new_points)
            stop_index %= len(new_points)
            for index in sorted(
                (
                    (start_index + metaindex) % len(new_points)
                    for metaindex in range((stop_index - start_index) % len(new_points))
                ),
                reverse=True,
            ):
                del new_points[index]
                del new_directions[index]
            if len(new_points) < 3:
                continue
            new_body = Polygon(new_points)
            if not new_body.is_valid:
                continue
            if not new_body.covers(Polygon(points)):
                continue
            return (True, new_points, new_directions)
    return (False,)


def _debug_plot(points, directions, pads):
    fig, ax = plt.subplots()
    for pad in pads:
        x, y = zip(*pad.exterior.coords)
        plt.plot(x, y, "r")
    for line_index, line in linewise(points):
        if directions[line_index] is None:
            color = "k"
        else:
            for dimension, color in zip(range(N_DIMENSIONS), ("y", "c")):
                if directions[line_index].value[dimension] != 0:
                    break
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), color)
    ax.set_aspect("equal")


def expand(points, directions, pads, debug=False):
    logger.debug(f"points = {points}")
    logger.debug(f"directions = {directions}")
    body = Polygon(points)
    if not body.exterior.is_ccw:
        logger.debug("reversing clockwise points")
        points.reverse().rotate()
        directions.reverse()
        directions = deque((Direction(tuple(-np.array(direction.value))) if direction is not None else direction))
        logger.debug(f"points = {points}")
        logger.debug(f"directions = {directions}")
    if debug:
        _debug_plot(points, directions, pads)
    while True:
        status, *optional = _expand(points, directions, pads)
        if not status:
            break
        points, directions = optional
        logger.debug(f"points = {points}")
        logger.debug(f"directions = {directions}")
        if debug:
            _debug_plot(points, directions, pads)
        while True:
            status, *optional = _make_valid(points, directions)
            if not status:
                break
            points, directions = optional
            logger.debug(f"points = {points}")
            logger.debug(f"directions = {directions}")
            if debug:
                _debug_plot(points, directions, pads)
    return points


def _cut(points, pads):
    for _, line in linewise(points):
        lines = LineString(line)
        for pad in pads:
            if lines.intersects(pad) and not lines.touches(pad):
                lines = lines.difference(pad)
            if lines.is_empty:
                break
        else:
            if hasattr(lines, "geoms"):
                yield from lines.geoms
            else:
                yield lines


def cut(points, pads):
    lines = linemerge(_cut(points, pads))
    if not hasattr(lines, "geoms"):
        lines = MultiLineString((lines,))
    return lines


def plot(points, directions, pads, debug=False):
    silkscreen = cut(expand(points, directions, pads, debug=debug), pads)
    fig, ax = plt.subplots()
    for pad in pads:
        x, y = zip(*pad.exterior.coords)
        plt.plot(x, y, "r")
    for line_index, line in linewise(points):
        plt.plot((line[0][0], line[1][0]), (line[0][1], line[1][1]), "g")
    for silkscreen_line_string in silkscreen.geoms:
        x, y = zip(*silkscreen_line_string.coords)
        plt.plot(x, y, "k")
    ax.set_aspect("equal")
    plt.show()
