import spatial
import matplotlib.pyplot as plt


def plotPoints(points, style='bo'):
    if not type(points) == list:
        points = [points]

    points = spatial.toNumpy(points)
    plt.plot(points[:, 0], points[:, 1], style)


def showPoints(points, style='bo'):
    plotPoints(points, style=style)
    plt.show()


def plot(polygons, style='g-'):
    if not type(polygons) == list:
        polygons = [polygons]
    for polygon in polygons:
        points = polygon.points + [polygon.points[0]]
        plotPoints(points, style=style)


def show(polygons, style='g-'):
    plot(polygons, style=style)
    plt.show()
