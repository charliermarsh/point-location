from random import random
from math import sqrt
import spatial
from drawer import *


def ccw(A, B, C):
    """Tests whether the line formed by A, B, and C is ccw"""
    return (B.x - A.x) * (C.y - A.y) > (B.y - A.y) * (C.x - A.x)


def intersect(a1, b1, a2, b2):
    """Returns True if the line segments a1b1 and a2b2 intersect."""
    return (ccw(a1, b1, a2) != ccw(a1, b1, b2)
            and ccw(a2, b2, a1) != ccw(a2, b2, b1))


class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __rmul__(self, c):
        return Point(c * self.x, c * self.y)

    def close(self, that, epsilon=0.01):
        return self.dist(that) < epsilon

    def dist(self, that):
        return sqrt(self.sqrDist(that))

    def sqrDist(self, that):
        dx = self.x - that.x
        dy = self.y - that.y
        return dx * dx + dy * dy

    def np(self):
        """Returns the point's Numpy point representation"""
        return [self.x, self.y]


class Line(object):

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

        if p1.x == p2.x:
            self.slope = None
            self.intercept = None
            self.vertical = True
        else:
            self.slope = float(p2.y - p1.y) / (p2.x - p1.x)
            self.intercept = p1.y - self.slope * p1.x
            self.vertical = False

    def __str__(self):
        if self.vertical:
            return "x = " + str(self.p1.x)
        return "y = " + str(self.slope) + "x + " + str(self.intercept)

    def __eq__(self, other):
        if self.vertical != other.vertical:
            return False

        if self.vertical:
            return self.p1.x == other.p1.x

        return self.slope == other.slope and self.intercept == other.intercept

    def atX(self, x):
        if self.vertical:
            return None

        return Point(x, self.slope * x + self.intercept)

    def sqrDistance(self, p):
        numerator = float(self.p2.x - self.p1.x) * (self.p1.y - p.y) - \
            (self.p1.x - p.x) * (self.p2.y - self.p1.y)
        numerator *= numerator
        denominator = float(self.p2.x - self.p1.x) * (self.p2.x - self.p1.x) + \
            (self.p2.y - self.p1.y) * (self.p2.y - self.p1.y)
        return numerator / denominator

    def distance(self, p):
        """Returns the distance of p from the line"""
        return sqrt(self.sqrDistance(p))

    def intersection(self, that):
        if that.slope == self.slope:
            return None

        if self.vertical:
            return that.atX(self.p1.x)
        elif that.vertical:
            return self.atX(that.p1.x)

        x = float(self.intercept - that.intercept) / (that.slope - self.slope)
        return self.atX(x)

    def midpoint(self):
        x = float(self.p1.x + self.p2.x) / 2
        y = float(self.p1.y + self.p2.y) / 2
        return Point(x, y)


class Polygon(object):

    def __init__(self, points):
        if len(points) < 3:
            raise ValueError("Polygon must have at least three vertices.")

        self.points = points
        self.n = len(points)

    def __str__(self):
        s = ""
        for point in self.points:
            if s:
                s += " -> "
            s += str(point)
        return s

    def __hash__(self):
        return hash(tuple(sorted(self.points, key=lambda p: p.x)))

    def contains(self, p):
        """Returns True if p is inside self."""
        if self.isConvex():
            # If convex, use CCW-esque algorithm
            inside = False

            p1 = self.points[0]
            for i in range(self.n + 1):
                p2 = self.points[i % self.n]
                if p.y > min(p1.y, p2.y):
                    if p.y <= max(p1.y, p2.y):
                        if p.x <= max(p1.x, p2.x):
                            if p1.y != p2.y:
                                xints = (p.y - p1.y) * \
                                    (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                            if p1.x == p2.x or p.x <= xints:
                                inside = not inside
                p1 = p2

            return inside
        else:
            # If concave, must triangulate and check individual triangles
            triangles = spatial.triangulatePolygon(self)
            for triangle in triangles:
                if triangle.contains(p):
                    return True
            return False

    def isConvex(self):
        target = None
        for i in range(self.n):
            # Check every triplet of points
            A = self.points[i % self.n]
            B = self.points[(i + 1) % self.n]
            C = self.points[(i + 2) % self.n]

            if not target:
                target = ccw(A, B, C)
            else:
                if ccw(A, B, C) != target:
                    return False

        return True

    def ccw(self):
        """Returns True if the points are provided in CCW order."""
        return ccw(self.points[0], self.points[1], self.points[2])

    def split(self, INTERIOR=False):
        """
            Randomly splits the polygon in two. If INTERIOR, then the split is created
            by introducing a random interior point and connecting two random vertices
            to the interior point. Else, two random vertices are themselves connected.
        """
        def randomSplit():
            def draw():
                # Randomly choose two vertices to connect
                u = int(random() * self.n)
                v = int(random() * self.n)
                if INTERIOR:
                    while u == v:
                        v = int(random() * self.n)
                else:
                    while abs(v - u) < 2 or abs(u - v) > self.n - 2:
                        v = int(random() * self.n)

                # W.L.O.G., set u to be min
                u, v = (min(u, v), max(u, v))
                return (u, v)

            u, v = draw()

            # Split points based on vertices
            p1 = self.points[u:v + 1]
            p2 = self.points[v:] + self.points[:u + 1]

            if INTERIOR:
                # Pick a random interior point
                p = self.smartInteriorPoint()
            else:
                p = None

            while not validChoice(u, v, p):
                u, v = draw()
                # Split points based on vertices
                p1 = self.points[u:v + 1]
                p2 = self.points[v:] + self.points[:u + 1]
                if INTERIOR:
                    p = self.smartInteriorPoint()

            if INTERIOR:
                return Polygon(p1 + [p]), Polygon(p2 + [p])
            else:
                return Polygon(p1), Polygon(p2)

        def validChoice(u, v, p):
            """Returns True if choice u, v, p keeps polygons simple, non-intesecting."""
            p_u = self.points[u]
            p_v = self.points[v]
            for i in range(self.n):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % self.n]

                if p:
                    if p1 != p_u and p2 != p_u:
                        if intersect(p_u, p, p1, p2):
                            return False
                    if p1 != p_v and p2 != p_v:
                        if intersect(p_v, p, p1, p2):
                            return False
                else:
                    if p1 == p_u or p2 == p_u or p1 == p_v or p2 == p_v:
                        continue
                    if intersect(p_v, p_u, p1, p2):
                        return False
            return True

        # No need to check for overflow with a convex split
        if self.isConvex():
            return randomSplit()

        poly1, poly2 = randomSplit()
        # If area has increased, invalid selection
        while poly1.area() + poly2.area() > self.area():
            poly1, poly2 = randomSplit()
        return poly1, poly2

    def area(self):
        """Returns the area of the polygon."""
        triangles = spatial.triangulatePolygon(self)
        areas = [t.area() for t in triangles]
        return sum(areas)

    def interiorPoint(self):
        """Returns a random point interior point via rejection sampling."""
        min_x = min([p.x for p in self.points])
        max_x = max([p.x for p in self.points])
        min_y = min([p.y for p in self.points])
        max_y = max([p.y for p in self.points])

        def x():
            return min_x + random() * (max_x - min_x)

        def y():
            return min_y + random() * (max_y - min_y)

        p = Point(x(), y())
        while not self.contains(p):
            p = Point(x(), y())

        return p

    def exteriorPoint(self):
        """Returns a random exterior point near the polygon."""
        min_x = min([p.x for p in self.points])
        max_x = max([p.x for p in self.points])
        min_y = min([p.y for p in self.points])
        max_y = max([p.y for p in self.points])

        def off():
            return 1 - 2 * random()

        def x():
            return min_x + random() * (max_x - min_x) + off()

        def y():
            return min_y + random() * (max_y - min_y) + off()

        p = Point(x(), y())
        while self.contains(p):
            p = Point(x(), y())

        return p

    def smartInteriorPoint(self):
        """Returns a random interior point via triangulation."""
        triangles = spatial.triangulatePolygon(self)
        areas = [t.area() for t in triangles]
        total = sum(areas)
        probabilities = [area / total for area in areas]

        # Sample triangle according to area
        r = random()
        count = 0
        for (triangle, prob) in zip(triangles, probabilities):
            count += prob
            if count >= r:
                return triangle.interiorPoint()


class Triangle(Polygon):

    def __init__(self, A, B, C):
        self.points = [A, B, C]
        self.n = 3

    def area(self):
        A = self.points[0]
        B = self.points[1]
        C = self.points[2]
        return (abs((B.x * A.y - A.x * B.y)
                    + (C.x * B.y - B.x * C.y)
                    + (A.x * C.y - C.x * A.y)) / 2.0)

    def interiorPoint(self):
        A = self.points[0]
        B = self.points[1]
        C = self.points[2]
        r1 = random()
        r2 = random()
        return (1 - sqrt(r1)) * A + sqrt(r1) * (1 - r2) * B + r2 * sqrt(r1) * C
