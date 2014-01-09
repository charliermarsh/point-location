import numpy as np
import scipy.spatial as sp
from p2t import CDT

import shapes


def toNumpy(points):
    return np.array(map(lambda p: p.np(), points), np.float32)


def triangulatePolygon(poly, hole=None):
    # Triangulate poly with hole
    cdt = CDT(poly.points)
    if hole:
        cdt.add_hole(hole)
    triangles = cdt.triangulate()

    # Frustratingly, CDT sometimes returns points that are not
    # EXACTLY the same as the input points, so we use a KDTree
    valid_points = [shapes.Point(p.x, p.y) for p in poly.points]
    if hole:
        valid_points += [shapes.Point(p.x, p.y) for p in hole]
    tree = sp.KDTree(toNumpy(valid_points))

    def convert(t):
        def findClosest(point):
            idx = tree.query(toNumpy([point]))[1]
            return valid_points[idx]
        A = findClosest(shapes.Point(t.a.x, t.a.y))
        B = findClosest(shapes.Point(t.b.x, t.b.y))
        C = findClosest(shapes.Point(t.c.x, t.c.y))
        return shapes.Triangle(A, B, C)
    return map(convert, triangles)


def triangulatePoints(points):
    points = toNumpy(points)
    triangulation = sp.Delaunay(points)
    triangles = []
    for i in range(len(triangulation.simplices)):
        verts = map(lambda p: shapes.Point(p[0], p[1]),
                    points[triangulation.simplices[i, :]])
        triangle = shapes.Triangle(
            verts[0], verts[1], verts[2])
        triangles.append(triangle)
    return triangles


def convexHull(points):
    points = toNumpy(points)
    verts = sp.ConvexHull(points).vertices
    hull = map(lambda idx: shapes.Point(points[idx, 0], points[idx, 1]), verts)
    return shapes.Polygon(hull)
