# Name: Anirban Roy Sourov
# Roll: 32
# Lab: 08 - Cyrus-Beck Line Clipping

import math
import os

os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540
XMIN, XMAX = -250, 249
YMIN, YMAX = -200, 199
EPSILON = 1e-9
PINK = (1.0, 0.4, 0.7)

# Each rectangle edge has a point on it and an OUTWARD normal.
EDGES = (
    ("left", (XMIN, YMIN), (-1, 0)),
    ("right", (XMAX, YMIN), (1, 0)),
    ("bottom", (XMIN, YMIN), (0, -1)),
    ("top", (XMIN, YMAX), (0, 1)),
)

window_width, window_height = WIDTH, HEIGHT
pending_point = None  # First click waits here until the second click.
lines = []  # Preserve completed input pairs and their clipping results.


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    reshape(WIDTH, HEIGHT)


def reshape(width, height):
    global window_width, window_height
    window_width, window_height = max(1, width), max(1, height)
    glViewport(0, 0, window_width, window_height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def pixel_round(value):
    # Same half-away-from-zero rounding used in earlier labs.
    return int(value + 0.5 * (1 if value > 0 else -1 if value < 0 else 0))


def inside(x, y):
    return XMIN <= x <= XMAX and YMIN <= y <= YMAX


def cyrus_beck(p0, p1):
    # P(t) = P0 + t*D, with 0 <= t <= 1 for the ORIGINAL segment.
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    entering, leaving = [], []
    parallel_outside = False

    for name, edge_point, normal in EDGES:
        nx, ny = normal
        # Inside means n dot (P(t) - edge_point) <= 0.
        numerator = nx * (edge_point[0] - p0[0]) + ny * (edge_point[1] - p0[1])
        denominator = nx * dx + ny * dy

        if abs(denominator) < EPSILON:
            # Parallel: no finite t. Negative numerator means outside this edge.
            if numerator < -EPSILON:
                parallel_outside = True
            continue

        t = numerator / denominator
        if denominator < 0:
            entering.append(t)  # Moving into this edge's inside half-plane.
        else:
            leaving.append(t)  # Moving out of this edge's inside half-plane.

    # Empty entering/leaving sets impose no bound: use -inf / +inf.
    te_min = min(entering, default=-math.inf)
    te_max = max(entering, default=-math.inf)
    tl_min = min(leaving, default=math.inf)
    tl_max = max(leaving, default=math.inf)

    t_enter = max(0.0, te_max)  # Latest entry must also lie on the input segment.
    t_leave = min(1.0, tl_min)  # Earliest exit must also lie on the input segment.
    accepted = not parallel_outside and t_enter <= t_leave
    clipped = None

    if accepted:
        # Calculate the two accepted endpoints BEFORE drawing anything.
        clipped = (
            (max(XMIN, min(XMAX, p0[0] + t_enter * dx)),
             max(YMIN, min(YMAX, p0[1] + t_enter * dy))),
            (max(XMIN, min(XMAX, p0[0] + t_leave * dx)),
             max(YMIN, min(YMAX, p0[1] + t_leave * dy))),
        )

    return {
        "te_min": te_min, "te_max": te_max,
        "tl_min": tl_min, "tl_max": tl_max,
        "t_enter": t_enter, "t_leave": t_leave,
        "accepted": accepted, "parallel_outside": parallel_outside,
        "clipped": clipped,
    }


def draw_line_bresenham(p0, p1, outside_only=False):
    x0, y0 = map(pixel_round, p0)
    x1, y1 = map(pixel_round, p1)
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    decision = dx - dy

    while True:
        # Outside pieces must not emit yellow pixels on or inside the rectangle.
        if not outside_only or not inside(x0, y0):
            glVertex2i(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        twice_decision = 2 * decision
        if twice_decision > -dy:
            decision -= dy
            x0 += sx
        if twice_decision < dx:
            decision += dx
            y0 += sy


def format_t(value):
    if math.isinf(value):
        return "-inf" if value < 0 else "+inf"
    return f"{value:.4f}"


def on_original_segment(t):
    # A candidate belongs to P0--P1 only for a finite parameter in [0, 1].
    return math.isfinite(t) and 0.0 <= t <= 1.0


def mouse(button, state, x, y):
    global pending_point
    if button != GLUT_LEFT_BUTTON or state != GLUT_DOWN:
        return

    # GLUT mouse coordinates start at top-left; our logical y points upward.
    logical_x = -WIDTH // 2 + x * (WIDTH - 1) / max(1, window_width - 1)
    logical_y = HEIGHT // 2 - 1 - y * (HEIGHT - 1) / max(1, window_height - 1)
    point = (pixel_round(logical_x), pixel_round(logical_y))

    if pending_point is None:
        pending_point = point
        print(f"\nP0 = {point}; click P1.")
    else:
        p0, p1 = pending_point, point
        result = cyrus_beck(p0, p1)
        lines.append((p0, p1, result))
        pending_point = None  # Next click starts another segment.

        print(f"P0 = {p0}, P1 = {p1}")
        print(f"tl_min = {format_t(result['tl_min'])}, tl_max = {format_t(result['tl_max'])}")
        print(f"te_min = {format_t(result['te_min'])}, te_max = {format_t(result['te_max'])}")
        print(f"Final interval: [{format_t(result['t_enter'])}, {format_t(result['t_leave'])}]")
        if result["accepted"]:
            print(f"Accepted endpoints: {result['clipped']}")
        else:
            reason = "parallel and outside an edge" if result["parallel_outside"] else "empty clipping interval"
            print(f"Rejected: {reason}.")
    glutPostRedisplay()


def draw_text(x, y, message):
    # Window coordinates keep the text readable even when the window is resized.
    glWindowPos2i(x, y)
    for character in message:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(1.0)
    glBegin(GL_POINTS)

    # Keep the previous lab's axes and extended boundary guides.
    glColor3f(0.3, 0.3, 0.3)
    for x in (0, XMIN, XMAX):
        draw_line_bresenham((x, -HEIGHT // 2), (x, HEIGHT // 2 - 1))
    for y in (0, YMIN, YMAX):
        draw_line_bresenham((-WIDTH // 2, y), (WIDTH // 2 - 1, y))

    # Bright white rectangle makes the actual clipping region easy to see.
    glColor3f(1.0, 1.0, 1.0)
    corners = ((XMIN, YMIN), (XMAX, YMIN), (XMAX, YMAX), (XMIN, YMAX))
    for i in range(4):
        draw_line_bresenham(corners[i], corners[(i + 1) % 4])

    for p0, p1, result in lines:
        if not result["accepted"]:
            continue  # Rejected segments have no visible line.
        c0, c1 = result["clipped"]
        # Draw separate outside pieces, never a yellow underlay beneath green.
        glColor3f(1.0, 1.0, 0.0)
        if result["t_enter"] > 0:
            draw_line_bresenham(p0, c0, outside_only=True)
        if result["t_leave"] < 1:
            draw_line_bresenham(c1, p1, outside_only=True)
        glColor3f(0.0, 1.0, 0.0)
        draw_line_bresenham(c0, c1)
    glEnd()

    # White points identify the clicked endpoints; red points mark edge contacts.
    glPointSize(7.0)
    glBegin(GL_POINTS)
    for p0, p1, result in lines:
        glColor3f(1.0, 1.0, 1.0)
        for x, y in (p0, p1):
            glVertex2i(x, y)
        if result["accepted"]:
            glColor3f(1.0, 0.0, 0.0)
            for x, y in result["clipped"]:
                if any(abs(value - edge) < EPSILON for value, edge in
                       ((x, XMIN), (x, XMAX), (y, YMIN), (y, YMAX))):
                    glVertex2i(pixel_round(x), pixel_round(y))

        # Show the extra candidates on the ORIGINAL segment, not its extension.
        glColor3f(*PINK)
        for name in ("tl_max", "te_min"):
            t = result[name]
            if on_original_segment(t):
                x = p0[0] + t * (p1[0] - p0[0])
                y = p0[1] + t * (p1[1] - p0[1])
                glVertex2i(pixel_round(x), pixel_round(y))
    if pending_point is not None:
        glColor3f(0.0, 1.0, 1.0)
        glVertex2i(*pending_point)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    draw_text(10, window_height - 18, "Left click P0, then P1. Each pair adds a segment.")
    if lines:
        p0, p1, result = lines[-1]
        draw_text(10, window_height - 34, f"Latest: P0={p0}, P1={p1}")
        # Color each text item independently, using the same rule as its marker.
        text_x = 10
        for name in ("tl_min", "tl_max", "te_min", "te_max"):
            highlight = name in ("tl_max", "te_min") and on_original_segment(result[name])
            glColor3f(*(PINK if highlight else (1.0, 1.0, 1.0)))
            label = f"{name}={format_t(result[name])}  "
            draw_text(text_x, window_height - 50, label)
            text_x += 8 * len(label)  # GLUT_BITMAP_8_BY_13 has 8-pixel characters.
        glColor3f(1.0, 1.0, 1.0)
        status = "ACCEPTED" if result["accepted"] else "REJECTED"
        draw_text(10, window_height - 66,
                  f"{status}: final t interval [{format_t(result['t_enter'])}, {format_t(result['t_leave'])}]")
    if pending_point is not None:
        draw_text(10, 42, f"P0={pending_point}; select P1.")
    draw_text(10, 26, "Green: inside | Yellow: outside | Red: clip contacts | Pink: tl_max/te_min on P0--P1")
    draw_text(10, 10, "te/tl extrema use all nonparallel edge candidates; -inf/+inf = no bound.")
    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Lab 08 - Cyrus-Beck Clipping - 23 Nov 26")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    print("Left click P0 and then P1. The latest t values appear in the window and terminal.")
    glutMainLoop()


if __name__ == "__main__":
    main()
