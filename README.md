point-location
==============

Kirkpatrick's Algorithm for Log(n) point location in planar subdivisions. The original paper is freely available as [[Kirkpatrick 83](http://www.cs.princeton.edu/courses/archive/fall05/cos528/handouts/Optimal%20Search%20In%20Planar.pdf)], with a more accessible walkthrough available [here](http://cgm.cs.mcgill.ca/~athens/cs507/Projects/2002/PaulSandulescu/).

# Usage

An example can be found in [PointLocation.ipynb](http://nbviewer.ipython.org/github/crm416/point-location/blob/master/PointLocation.ipynb).

All shape primitives (including points and polygons) can be found in `geo.shapes`, while the implementation of Kirkpatrick's Algorithm is in `kirkpatrick`.

```
from geo.generator import randomConvexTiling, randomPoint
from kirkpatrick import Locator

# generate a convex subdivison
subdivision = randomConcaveTiling(randomConvexPolygon(100))

# run Kirkpatrick's
locator = Locator(subdivision)
point = randomPoint()
region = locator.locate(point)
```

# Minimum Enclosing Triangle

In addition, an implementation of a Theta(n) algorithm for computing the bounding triangle of minimum area on a convex point set is implemented in `min_triangle`. For more detail, see the original paper on which it is based: [[O'Rourke 86](http://prografix.narod.ru/source/orourke1986.pdf)].

As an example case:

```
from geo.generator import randomConvexPolygon
from geo.drawer import plot, show
from min_triangle import minTriangle

polygon = randomConvexPolygon(100)
triangle = minTriangle(polygon)
plot(polygon, style='g-')
show(triangle, style='ro--')
```

While [OpenCV](http://docs.opencv.org/master/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html#minenclosingtriangle) includes an existing implementation of this algorithm in C++, this is the first of its kind in Python.

# Dependencies

- [Numpy](http://www.numpy.org), [Scipy](http://scipy.org): for computing convex hulls and more.
- [Poly2Tri](http://code.google.com/p/poly2tri/): for computing triangulations of polygons (with holes).
- [matplotlib](http://matplotlib.org): for visualizations.