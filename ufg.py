# Copyright (C) 2022 Matthew Marting
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import deque
from enum import Enum

from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import Polygon
from shapely.ops import linemerge

import matplotlib.pyplot as plt


def linewise(points):
    for point1_index, point1 in enumerate(points):
        point2_index = point1_index + 1
        point2_index %= len(points)
        yield point1_index, (point1, points[point2_index])


def linewise3(points, start_point_index, stop_point_index, step):
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
    already_found_zero_proj_line = False
    for reverse_line_index, reverse_line in linewise3(points, line_index - step, line_index, -step):
        if pad.direction.is_perpendicular_to(directions[reverse_line_index]) or is_proj_zero(
            reverse_line, pad.direction
        ):
            already_found_zero_proj_line = True
            continue
        if is_proj_negative_to(reverse_line, pad.direction, line):
            break
        if already_found_zero_proj_line:
            break
    last_positive_proj_line_index = line_index
    for forward_line_index, forward_line in linewise3(points, line_index, reverse_line_index, step):
        if pad.direction.is_perpendicular_to(directions[forward_line_index]):
            break
        if is_proj_zero(forward_line, pad.direction):
            continue
        if is_proj_negative_to(forward_line, pad.direction, line):
            continue
        last_positive_proj_line_index = forward_line_index
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
            if not (LineString(line).intersects(pad) and not LineString(line).touches(pad)):
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
                    translation = (
                        pad.bounds[N_DIMENSIONS * (expand_direction.value[dimension] > 0) + dimension]
                        - LineString(line).bounds[
                            N_DIMENSIONS * (expand_direction.value[dimension] < 0) + dimension
                        ]
                    )
                    return (
                        True,
                        first_positive_proj_line_index,
                        last_positive_proj_line_index,
                        expand_direction,
                        translation,
                    )
    return (False,)


def expand(points, directions, pads):
    while True:
        status, *optional = _expand(points, directions, pads)
        if not status:
            break
        first_line_index, last_line_index, expand_direction, translation = optional
        first_point = points[first_line_index]
        last_point = points[(last_line_index + 1) % len(points)]
        for dimension in range(N_DIMENSIONS):
            if expand_direction.value[dimension] != 0:
                for point_metaindex in range(((last_line_index + 2) - first_line_index) % len(points)):
                    point_index = first_line_index + point_metaindex
                    point_index %= len(points)
                    points[point_index] = tuple(
                        x + translation if point_dimension == dimension else x
                        for point_dimension, x in enumerate(points[point_index])
                    )
                insert_point_queue = deque(((first_line_index, first_point), (last_line_index + 2, last_point)))
                while len(insert_point_queue) > 0:
                    index, point = insert_point_queue.popleft()
                    points.insert(index % len(points), point)
                    for queue_index, (future_index, future_point) in enumerate(insert_point_queue):
                        if future_index < index:
                            continue
                        insert_point_queue[queue_index] = (future_index + 1, future_point)
                insert_direction_queue = deque((first_line_index, last_line_index + 1))
                while len(insert_direction_queue) > 0:
                    index = insert_direction_queue.popleft()
                    directions.insert(index % len(directions), None)
                    for queue_index, future_index in enumerate(insert_direction_queue):
                        if future_index < index:
                            continue
                        insert_direction_queue[queue_index] = future_index + 1


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
    return linemerge(_cut(points, pads))


def plot(points, directions, pads):
    fig, ax = plt.subplots()
    for pad in pads:
        x, y = zip(*pad.exterior.coords)
        plt.plot(x, y, "r")
    x, y = zip(*(tuple(points) + (points[0],)))
    plt.plot(x, y, "g")
    expand(points, directions, pads)
    silkscreen = cut(points, pads)
    if not hasattr(silkscreen, "geoms"):
        silkscreen = MultiLineString((silkscreen,))
    for silkscreen_line_string in MultiLineString(silkscreen).geoms:
        x, y = zip(*silkscreen_line_string.coords)
        plt.plot(x, y, "k")
    ax.set_aspect("equal")
    plt.show()
