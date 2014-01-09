from random import random
import Queue

from shapes import Point
from spatial import convexHull


def randomPoint(k=None):
    if k:
        return Point(int(k * random()), int(k * random()))
    return Point(random(), random())


def randomConvexPolygon(sample, k=None, n=3):
    hull = convexHull([randomPoint(k=k) for i in range(sample)])
    while hull.n < n:
        hull = convexHull([randomPoint(k=k) for i in range(sample)])
    return hull


def randomTiling(polygon, n, CONCAVE=False):
    """Generates a random concave tiling of a convex region."""
    class PolygonWithArea(object):

        def __init__(self, polygon):
            self.polygon = polygon
            self.area = polygon.area()

        def __cmp__(self, that):
            return -cmp(self.area, that.area)

    # Start with initial convex region
    initial = PolygonWithArea(polygon)

    # Place in PQ to pop by area
    pq = Queue.PriorityQueue(maxsize=n + 1)
    pq.put(initial)

    # Create some concave regions
    triangles = []
    for i in range(n):
        # Split up largest polygon
        polygon = pq.get().polygon

        for polygon in polygon.split(INTERIOR=CONCAVE):
            if polygon.n == 3:
                triangles.append(polygon)
            else:
                pq.put(PolygonWithArea(polygon))

    polygons = triangles
    while pq.qsize():
        polygons.append(pq.get().polygon)

    return polygons


def randomConcaveTiling(polygon, n=10):
    return randomTiling(polygon, n=n, CONCAVE=True)


def randomConvexTiling(polygon, n=10):
    return randomTiling(polygon, n)
