import os
import math

from numpy import sign

os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

RADIUS = 250
THETA_START = 0
THETA_END = 180
THETA_STEP = 1

errors = []
normalized_errors = []


def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def calculate_line_dda(x0, y0, x1, y1):
    """Return the DDA pixels and their total rasterization error."""
    steps = max(abs(x1 - x0), abs(y1 - y0))

    x_increment = (x1 - x0) / steps
    y_increment = (y1 - y0) / steps

    x = x0
    y = y0

    points = []
    total_error = 0.0

    for i in range(steps + 1):
        pixel_x = int(x + 0.5 * sign(x))
        pixel_y = int(y + 0.5 * sign(y))
        points.append((pixel_x, pixel_y))
        total_error += abs(x - pixel_x) + abs(y - pixel_y)
        x += x_increment
        y += y_increment

    return points, total_error


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    lines = []
    errors.clear()
    normalized_errors.clear()
    theta_values = list(range(THETA_START, THETA_END + 1, THETA_STEP))

    for theta in theta_values:
        angle = math.radians(theta)
        x = RADIUS * math.cos(angle)
        y = RADIUS * math.sin(angle)

        x0 = int(x + 0.5 * sign(x))
        y0 = int(y + 0.5 * sign(y))
        x1 = int(-x + 0.5 * sign(-x))
        y1 = int(-y + 0.5 * sign(-y))

        points, total_error = calculate_line_dda(x0, y0, x1, y1)
        lines.append(points)
        errors.append(total_error)

    max_total_error = max(errors)
    if max_total_error == 0:
        normalized_errors.extend(0.0 for _ in errors)
    else:
        normalized_errors.extend(error / max_total_error for error in errors)

    glPointSize(1.0)
    glBegin(GL_POINTS)

    for points, normalized_error in zip(lines, normalized_errors):
        glColor3d(normalized_error, normalized_error, normalized_error)

        for pixel_x, pixel_y in points:
            glVertex2i(pixel_x, pixel_y)

    glEnd()

    for theta, total_error, normalized_error in zip(
        theta_values, errors, normalized_errors
    ):
        print(
            f"theta = {theta:3d} degrees, "
            f"total error = {total_error:.6f}, "
            f"normalized error = {normalized_error:.6f}"
        )

    glFlush()


##.....................................
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(300, 300)
glutCreateWindow(b"DDA Lines - Lab 28 Sep 26")

init()
glutDisplayFunc(display)
glutMainLoop()
