from geo import shapes, spatial
import min_triangle
from graph import UndirectedGraph, DirectedGraph


class Locator(object):

    def __init__(self, regions, outline=None):
        self.preprocess(regions, outline)

    def preprocess(self, regions, outline=None):
        def process_boundary(regions, outline=None):
            """
                Adds an outer triangle and triangulates the interior region. If an outline
                for the region is not provided, uses the convex hull (thus assuming that
                the region itself is convex.

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane
                outline -- the polygonal outline of regions

                Returns: a bounding triangle for regions and a triangulation for the area between
                regions and the bounding triangle.
            """
            def add_bounding_triangle(poly):
                """
                    Calculates a bounding triangle for a polygon

                    Arguments:
                    poly -- a polygon to-be bound

                    Returns: a bounding polygon for 'poly'
                """

                bounding_tri = min_triangle.boundingTriangle(poly.points)
                bounding_regions = spatial.triangulatePolygon(
                    bounding_tri, hole=poly.points)
                return bounding_tri, bounding_regions

            if not outline:
                points = reduce(lambda ps, r: ps + r.points, regions, [])
                outline = spatial.convexHull(points)
            return add_bounding_triangle(outline)

        def triangulate_regions(regions):
            """
                Processes a set of regions (non-overlapping polygons tiling a portion of the plane),
                triangulating any region that is not already a triangle, and storing triangulated
                relationships in a DAG.

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane

                Returns: a triangulation for each individual region in 'regions'
            """
            frontier = []

            for region in regions:
                self.dag.add_node(region)

                # If region is not a triangle, triangulate
                if region.n > 3:
                    triangles = spatial.triangulatePolygon(region)
                    for triangle in triangles:
                        # Connect DAG
                        self.dag.add_node(triangle)
                        self.dag.connect(triangle, region)
                        # Add to frontier
                        frontier.append(triangle)
                else:
                    frontier.append(region)

            return frontier

        def remove_independent_set(regions):
            """
                Processes a set of regions, detecting and removing an independent set
                of vertices from the regions' graph representation, and re-triangulating
                the resulting holes.

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane

                Returns: a new set of regions covering the same subset of the plane, with fewer vertices
            """
            # Take note of which points are in which regions
            points_to_regions = {}
            for idx, region in enumerate(regions):
                for point in region.points:
                    if point in points_to_regions:
                        points_to_regions[point].add(idx)
                        continue

                    points_to_regions[point] = set([idx])

            # Connect graph
            g = UndirectedGraph()
            for region in regions:
                for idx in range(region.n):
                    u = region.points[idx % region.n]
                    v = region.points[(idx + 1) % region.n]
                    if not g.contains(u):
                        g.add_node(u)
                    if not g.contains(v):
                        g.add_node(v)
                    g.connect(u, v)

            # Avoid adding points from outer triangle
            removal = g.independent_set(8, avoid=bounding_triangle.points)

            # Track unaffected regions
            unaffected_regions = set([i for i in range(len(regions))])
            new_regions = []
            for p in removal:
                # Take note of affected regions
                affected_regions = points_to_regions[p]
                unaffected_regions.difference_update(points_to_regions[p])

                def calculate_bounding_polygon(p, affected_regions):
                    edges = []
                    point_locations = {}
                    for j, i in enumerate(affected_regions):
                        edge = set(regions[i].points)
                        edge.remove(p)
                        edges.append(edge)
                        for v in edge:
                            if v in point_locations:
                                point_locations[v].add(j)
                            else:
                                point_locations[v] = set([j])

                    boundary = []
                    edge = edges.pop()
                    for v in edge:
                        point_locations[v].remove(len(edges))
                        boundary.append(v)
                    for k in range(len(affected_regions) - 2):
                        v = boundary[-1]
                        i = point_locations[v].pop()
                        edge = edges[i]
                        edge.remove(v)
                        u = edge.pop()
                        point_locations[u].remove(i)
                        boundary.append(u)

                    return shapes.Polygon(boundary)

                # triangulate hole
                poly = calculate_bounding_polygon(p, affected_regions)
                triangles = spatial.triangulatePolygon(poly)
                for triangle in triangles:
                    self.dag.add_node(triangle)
                    for j in affected_regions:
                        region = regions[j]
                        self.dag.connect(triangle, region)
                    new_regions.append(triangle)

            for i in unaffected_regions:
                new_regions.append(regions[i])

            return new_regions

        self.dag = DirectedGraph()

        # Store copy of regions
        self.regions = regions

        # Calculate, triangulate bounding triangle
        bounding_triangle, boundary = process_boundary(regions, outline)

        # Store copy of boundary
        self.boundary = boundary

        # Iterate until only bounding triangle remains
        frontier = triangulate_regions(regions + boundary)
        while len(frontier) > 1:
            frontier = remove_independent_set(frontier)

    def locate(self, p):
        """Locates the point p in one of the initial regions"""
        polygon, valid = self.annotatedLocate(p)

        # Result might be valid polygon
        if not valid:
            return None

        return polygon

    def annotatedLocate(self, p):
        """
            Locates the point p, returning the region and whether or not
            the region was one of the initial regions (i.e., False if the
            region was a fabricated boundary region).
        """
        curr = self.dag.root()
        if not curr.contains(p):
            return None, False

        children = self.dag.e[curr]
        while children:
            for region in children:
                if region.contains(p):
                    curr = region
                    break

            children = self.dag.e[curr]

        # Is the final region an exterior region?
        return curr, curr in self.regions
