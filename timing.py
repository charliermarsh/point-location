import timeit


def run(n):
    setup = """
from geo.generator import randomPoint
from geo.spatial import triangulatePoints, convexHull
from kirkpatrick import Locator
points = [randomPoint() for i in range(%d)]
hull = convexHull(points)
tiling = triangulatePoints(points)
points = [hull.interiorPoint() for i in range(5000)]
l = Locator(tiling)""" % n
    num_trials = 5000
    time = timeit.timeit('p = points.pop(); l.locate(p)',
                         setup=setup, number=num_trials)
    return time / float(num_trials)

if __name__ == "__main__":
    # Time the `Locate` method
    n = 10
    for k in range(10):
        t = run(n)
        print "n = " + str(n) + " : " + str(t) + " seconds per point"

        t = run(n * n)
        print "n = " + str(n * n) + " : " + str(t) + " seconds per point"
        n *= 2
