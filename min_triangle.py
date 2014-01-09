from math import sqrt, ceil, floor

from geo.shapes import Point, Line, Triangle, Polygon, ccw
from geo.spatial import convexHull
from geo.generator import randomConvexPolygon
from geo.drawer import plot, show


def minTriangle(poly):
    """
        Returns the triangle of minimum area enclosing a convex polygon.
        Runs in Theta(n) time for convex polygons, or O(n*log(n)) for
        concave polygons as convex hull must be computed.

        Arguments:
        poly -- the polygon to be enclosed

        Returns: the triangle of minimum area enclosing polygon
    """
    if not poly.isConvex():
        poly = convexHull(poly.points)

    n = poly.n
    points = poly.points

    # Check for degenerate cases
    if n < 3:
        raise ValueError("Polygon must have at least three vertices.")
    elif n == 3:
        return Triangle(poly.points[0], poly.points[1], poly.points[2])

    def side(i):
        """Return the side of polygon formed by vertices (i-1) and i."""
        return Line(points[(i - 1) % n], points[i % n])

    def isValidTriangle(vertex_A, vertex_B, vertex_C, a, b, c):
        """Checks that a triangle composed of the given vertices is a valid local minimum."""
        if not (vertex_A and vertex_B and vertex_C):
            return False

        midpoint_A = Line(vertex_C, vertex_B).midpoint()
        midpoint_B = Line(vertex_A, vertex_C).midpoint()
        midpoint_C = Line(vertex_A, vertex_B).midpoint()

        def validateMidpoint(midpoint, index):
            """Checks that a midpoint touches the polygon on the appropriate side."""
            s = side(index)

            # Account for floating-point errors
            epsilon = 0.01

            if s.vertical:
                if midpoint.x != s.p1.x:
                    return False
                max_y = max(s.p1.y, s.p2.y) + epsilon
                min_y = min(s.p1.y, s.p2.y) - epsilon
                if not (midpoint.y <= max_y and midpoint.y >= min_y):
                    return False

                return True
            else:
                max_x = max(s.p1.x, s.p2.x) + epsilon
                min_x = min(s.p1.x, s.p2.x) - epsilon
                # Must touch polygon
                if not (midpoint.x <= max_x and midpoint.x >= min_x):
                    return False

                if not s.atX(midpoint.x).close(midpoint):
                    return False

                return True

        return (validateMidpoint(midpoint_A, a) and validateMidpoint(midpoint_B, b)
                and validateMidpoint(midpoint_C, c))

    def triangleForIndex(c, a, b):
        """Returns the minimal triangle with edge C flush to vertex c."""
        a = max(a, c + 1) % n
        b = max(b, c + 2) % n
        side_C = side(c)

        def h(point, side):
            """Return the distance from 'point' to 'side'."""
            if type(point) == Point:
                return side.distance(point)
            elif isinstance(point, int):
                return side.distance(points[point])

        def gamma(point, on, base):
            """Calculate the point on 'on' that is twice as far from 'base' as 'point'."""
            intersection = on.intersection(base)
            dist = 2 * h(point, base)
            # Calculate differential change in distance
            if on.vertical:
                ddist = h(Point(intersection.x, intersection.y + 1), base)
                guess = Point(intersection.x, intersection.y + dist / ddist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = Point(intersection.x,
                                  intersection.y - dist / ddist)
                return guess
            else:
                ddist = h(on.atX(intersection.x + 1), base)
                guess = on.atX(intersection.x + dist / ddist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = on.atX(intersection.x - dist / ddist)
                return guess

        def critical(a, b, c, gamma_B):
            return ccw(gamma_B, points[b], points[(b - 1) % n]) == ccw(gamma_B, points[b], points[(b + 1) % n])

        def high(a, b, c, gamma_B):
            # Test if two adjacent vertices are on same side of line (implies
            # tangency)
            if ccw(gamma_B, points[b], points[(b - 1) % n]) == ccw(gamma_B, points[b], points[(b + 1) % n]):
                return False

            # Test if Gamma and B are on same side of line from adjacent
            # vertices
            if ccw(points[(b - 1) % n], points[(b + 1) % n], gamma_B) == ccw(points[(b - 1) % n], points[(b + 1) % n], points[b]):
                return h(gamma_B, side_C) > h(b, side_C)
            else:
                return False

        def low(a, b, c, gamma_B):
            # Test if two adjacent vertices are on same side of line (implies
            # tangency)
            if ccw(gamma_B, points[b], points[(b - 1) % n]) == ccw(gamma_B, points[b], points[(b + 1) % n]):
                return False

            # Test if Gamma and B are on same side of line from adjacent
            # vertices
            if ccw(points[(b - 1) % n], points[(b + 1) % n], gamma_B) == ccw(points[(b - 1) % n], points[(b + 1) % n], points[b]):
                return False
            else:
                return h(gamma_B, side_C) > h(b, side_C)

        def onLeftChain(b):
            return h((b + 1) % n, side_C) >= h(b, side_C)

        def incrementLowHigh(a, b, c):
            gamma_A = gamma(points[a], side(a), side_C)

            if high(a, b, c, gamma_A):
                b = (b + 1) % n
            else:
                a = (a + 1) % n
            return a, b

        def tangency(a, b):
            gamma_B = gamma(points[b], side(a), side_C)
            return h(b, side_C) >= h((a - 1) % n, side_C) and high(a, b, c, gamma_B)

        # Increment b while low
        while onLeftChain(b):
            b = (b + 1) % n

        # Increment a if low, b if high
        while h(b, side_C) > h(a, side_C):
            a, b = incrementLowHigh(a, b, c)

        # Search for b tangency
        while tangency(a, b):
            b = (b + 1) % n

        gamma_B = gamma(points[b], side(a), side_C)
        # Adjust if necessary
        if low(a, b, c, gamma_B) or h(b, side_C) < h((a - 1) % n, side_C):
            side_B = side(b)
            side_A = side(a)
            side_B = Line(side_C.intersection(side_B),
                          side_A.intersection(side_B))

            if h(side_B.midpoint(), side_C) < h((a - 1) % n, side_C):
                gamma_A = gamma(points[(a - 1) % n], side_B, side_C)
                side_A = Line(gamma_A, points[(a - 1) % n])
        else:
            gamma_B = gamma(points[b], side(a), side_C)
            side_B = Line(gamma_B, points[b])
            side_A = Line(gamma_B, points[(a - 1) % n])

        # Calculate final intersections
        vertex_A = side_C.intersection(side_B)
        vertex_B = side_C.intersection(side_A)
        vertex_C = side_A.intersection(side_B)

        # Check if triangle is valid local minimum
        if not isValidTriangle(vertex_A, vertex_B, vertex_C, a, b, c):
            triangle = None
        else:
            triangle = Triangle(vertex_A, vertex_B, vertex_C)

        return triangle, a, b

    triangles = []
    a = 1
    b = 2
    for i in range(n):
        triangle, a, b = triangleForIndex(i, a, b)
        if triangle:
            triangles.append(triangle)

    areas = [triangle.area() for triangle in triangles]
    return triangles[areas.index(min(areas))]


def boundingTriangle(points):
    def expand(poly, factor=10):
        """Expands a polygon, moving the vertices outward ~'factor'."""
        def bisect(A, B, C):
            # Define vector operations
            def magnitude(v):
                    return sqrt(sum([x * x for x in v]))

            def normalize(v):
                mag = magnitude(v)
                return [x / mag for x in v]

            def median(u, v):
                return [(x[0] + x[1]) / 2 for x in zip(u, v)]

            def reverse(v):
                return [-x for x in v]

            # Form vectors
            v_b = [B.x - A.x, B.y - A.y]
            v_c = [C.x - A.x, C.y - A.y]
            v_b = normalize(v_b)
            v_c = normalize(v_c)
            bisector = reverse(median(v_b, v_c))

            x = A.x + factor * bisector[0]
            y = A.y + factor * bisector[1]

            def absRound(n):
                if n < 0:
                    return floor(n)
                return ceil(n)

            x = absRound(x)
            y = absRound(y)

            return Point(x, y)

        def adjust(i):
            A = poly.points[i % poly.n]
            B = poly.points[(i - 1) % poly.n]
            C = poly.points[(i + 1) % poly.n]
            return bisect(A, B, C)

        expanded_points = [adjust(i) for i in range(poly.n)]
        return Polygon(expanded_points)

    return expand(minTriangle(Polygon(points)))

if __name__ == "__main__":
    poly = randomConvexPolygon(10)
    triangle = minTriangle(poly)
    plot(poly)
    show(triangle, style='r--')
