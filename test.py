import unittest
from random import random
from geo.shapes import Point, Polygon, Triangle
from geo.spatial import triangulatePolygon
from geo.generator import randomConvexPolygon, randomConcaveTiling
from geo.drawer import plot, plotPoints, show, showPoints
from min_triangle import minTriangle, boundingTriangle
from graph import DirectedGraph, UndirectedGraph
from kirkpatrick import Locator


class TestGeo(unittest.TestCase):
    ANIMATE = False

    def testInside(self):
        A = Point(0, 0)
        B = Point(4, 0)
        C = Point(4, 4)
        D = Point(0, 4)
        poly = Polygon([A, B, C, D])
        points = [Point(1, 1), Point(1, 2), Point(3, 3)]
        for point in points:
            self.assertTrue(poly.contains(point))

    def testConvex(self):
        n = 100
        poly = randomConvexPolygon(n, k=50)
        self.assertTrue(poly.isConvex())

        p1, p2 = poly.split()
        c1, c2 = (p1.isConvex(), p2.isConvex())
        self.assertTrue(c1 and c2)

        p1, p2 = poly.split(INTERIOR=True)
        c1, c2 = (p1.isConvex(), p2.isConvex())
        self.assertTrue((c1 and not c2) or (c2 and not c1))

    def testInterior(self):
        n = 100
        k = 1000
        poly = randomConvexPolygon(n, k=50)
        points = [poly.smartInteriorPoint() for i in range(k)]
        for point in points:
            self.assertTrue(poly.contains(point))

        if self.ANIMATE:
            plot(poly)
            showPoints(points, style='bo')

    def testExterior(self):
        n = 100
        k = 1000
        poly = randomConvexPolygon(n, k=50)
        points = [poly.exteriorPoint() for i in range(k)]
        for point in points:
            self.assertTrue(not poly.contains(point))

        if self.ANIMATE:
            plot(poly)
            showPoints(points, style='ro')

    def testTriangleInside(self):
        A = Point(1, 1)
        B = Point(3, 1)
        C = Point(3, 3)
        tri = Triangle(A, B, C)
        points = [Point(2, 1.1), Point(2.8, 2.2)]
        for point in points:
            self.assertTrue(tri.contains(point))

    @unittest.skipIf(not ANIMATE, "No animations")
    def testSplit(self):
        poly = randomConvexPolygon(20, k=20)
        show(poly)

        p1, p2 = poly.split()
        show([p1, p2])

    @unittest.skipIf(not ANIMATE, "No animations")
    def testConcaveSplit(self):
        poly = randomConvexPolygon(20, k=20)
        polygons = set([poly])

        for t in range(10):
            poly = polygons.pop()
            poly1, poly2 = poly.split(INTERIOR=True)
            polygons.add(poly1)
            polygons.add(poly2)

        show(list(polygons))

    @unittest.skipIf(not ANIMATE, "No animations")
    def testMinTriangle(self):
        points = randomConvexPolygon(10, k=20).points
        interior = minTriangle(points)
        exterior = boundingTriangle(points)

        # Plot points
        plotPoints(points, style='ro')

        # Plot bounding triangle
        plot(interior, style='go-')
        show(exterior, style='bo-')


class TestLocator(unittest.TestCase):
    ANIMATE = False

    def runLocator(self, regions):
        # Pre-process regions
        l = Locator(regions)

        if self.ANIMATE:
            show(regions)
            plot(l.boundary, style='g--')
            show(regions)

        # Ensure resulting DAG is acyclic
        self.assertTrue(l.dag.acyclic())

        n = 50
        # Ensure correctness
        for region in regions:
            # Test n random interior points per region
            for k in range(n):
                target = region.smartInteriorPoint()
                target_region = l.locate(target)
                self.assertEqual(region, target_region)
                self.assertTrue(target_region.contains(target))

            # Animate one interior point
            if self.ANIMATE:
                plot(l.regions)
                plot(target_region, style='ro-')
                showPoints(target, style='bo')

            # Test n random exterior points per region
            for k in range(n):
                target = region.exteriorPoint()
                target_region, is_valid = l.annotatedLocate(target)
                self.assertTrue(region != target_region)

                # Point may be outside all regions
                if not is_valid:
                    for region in regions:
                        self.assertTrue(not region.contains(target))

            # Animate one exterior point
            if self.ANIMATE and not is_valid and target_region:
                plot(l.regions)
                plot(target_region, style='ro--')
                showPoints(target, style='bx')

    def testSimple(self):
        # Create distinct regions
        A = Point(0, 0)
        B = Point(1.5, 0)
        C = Point(1, 1)
        D = Point(1, -1)
        E = Point(0, 1)
        t1 = Triangle(A, B, C)
        t2 = Triangle(A, B, D)
        t3 = Triangle(A, C, E)
        regions = [t1, t2, t3]
        self.runLocator(regions)

    def testMedium(self):
        A = Point(0, 0)
        B = Point(5, 0)
        C = Point(4, 2)
        D = Point(5, 4)
        E = Point(0, 4)
        F = Point(5, 7)
        G = Point(8, 4)
        H = Point(7, 2)
        p1 = Polygon([A, B, C, D, E])
        p2 = Polygon([D, E, F, G, H])
        p3 = Polygon([B, C, D, H])
        regions = [p1, p2, p3]
        self.runLocator(regions)

    def testRandomTriangles(self):
        poly = randomConvexPolygon(50)
        regions = triangulatePolygon(poly)
        self.runLocator(regions)

    def testConcavePolygons(self):
        initial = randomConvexPolygon(200, k=100)
        convex = set([initial])
        concave = set([])

        numConvex = 10
        for i in range(numConvex):
            polygon = convex.pop()
            for p in polygon.split(INTERIOR=True):
                if p.isConvex():
                    convex.add(p)
                else:
                    concave.add(p)

        regions = list(convex.union(concave))
        self.runLocator(regions)

    def testRandomConvexPolygons(self):
        initial = randomConvexPolygon(200, k=100)
        polygons = set([initial])

        # Can't split triangles, remove from contention
        triangles = set([])
        for i in range(10):
            if not polygons:
                break
            # Remove, split random polygon
            polygon = polygons.pop()
            for polygon in polygon.split():
                if polygon.n == 3:
                    triangles.add(polygon)
                else:
                    polygons.add(polygon)

        polygons.update(triangles)

        # Run Kirkpatrick's
        polygons = list(polygons)
        self.runLocator(polygons)

    def testRandomConcavePolygons(self):
        initial = randomConvexPolygon(100, k=100)
        polygons = randomConcaveTiling(initial)
        self.runLocator(polygons)


class TestGraph(unittest.TestCase):

    def setUp(self):
        dag = DirectedGraph()
        dag.add_node(0)
        dag.add_node(1)
        dag.add_node(2)
        dag.add_node(3)
        dag.add_node(4)
        dag.add_node(5)
        dag.connect(0, 1)
        dag.connect(0, 2)
        dag.connect(0, 3)
        dag.connect(3, 4)
        dag.connect(4, 5)
        self.dag = dag

        cyclic = DirectedGraph()
        cyclic.add_node(0)
        cyclic.add_node(1)
        cyclic.add_node(2)
        cyclic.add_node(3)
        cyclic.add_node(4)
        cyclic.connect(0, 1)
        cyclic.connect(1, 2)
        cyclic.connect(1, 3)
        cyclic.connect(2, 3)
        cyclic.connect(2, 4)
        cyclic.connect(4, 0)
        self.cyclic = cyclic

    def testRoot(self):
        self.assertEqual(self.dag.root(), 0)

    def testAcyclic(self):
        self.assertTrue(self.dag.acyclic())

    def testCyclic(self):
        self.assertTrue(not self.cyclic.acyclic())

    def testIndependentSet(self):
        n = 100
        e = 5 * n
        g = UndirectedGraph()
        for i in range(e):
            u = int(random() * n)
            v = int(random() * n)
            if u == v:
                continue
            if not g.contains(u):
                g.add_node(u)
            if not g.contains(v):
                g.add_node(v)
            g.connect(u, v)

        ind_set = g.independent_set(8)
        for i in ind_set:
            neighbors = g.e[i]
            self.assertEqual(neighbors.intersection(ind_set), set([]))


if __name__ == '__main__':
    unittest.main()
