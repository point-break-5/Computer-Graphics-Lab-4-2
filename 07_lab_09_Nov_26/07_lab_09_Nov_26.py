# Name: Anirban Roy Sourov
# Roll: 32
# Lab: 07 - Cohen-Sutherland Line Clipping

import os  # Select the OpenGL backend before importing OpenGL.
import random  # Generate endpoint coordinates when q is pressed.
from numpy import sign  # Keep the lab's sign-aware rounding for negative values.

os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540  # Actual OpenGL window dimensions.
# Random endpoints may be off-screen; adjust these ranges if needed.
RANDOM_XMIN, RANDOM_XMAX = -WIDTH, WIDTH
RANDOM_YMIN, RANDOM_YMAX = -HEIGHT, HEIGHT
XMIN, XMAX = -250, 249  # Left and right sides of the smaller clipping rectangle.
YMIN, YMAX = -200, 199  # Bottom and top sides of the clipping rectangle.

# Cohen-Sutherland region-code bits. A zero code means inside the rectangle.
LEFT, RIGHT, BOTTOM, TOP = 1, 2, 4, 8
segments = []  # Keep every generated segment so redraws preserve previous lines.

INTERSECTION_COLOR = (1.0, 0.0, 0.0)  # All rectangle-edge intersections are red.
OUTSIDE_GUIDES = (
    ("xmin", 0, XMIN, (1.0, 0.5, 0.0)),  # Orange on the left guide extension.
    ("xmax", 0, XMAX, (0.0, 1.0, 1.0)),  # Cyan on the right guide extension.
    ("ymin", 1, YMIN, (1.0, 0.0, 1.0)),  # Magenta on the bottom guide extension.
    ("ymax", 1, YMAX, (0.3, 0.5, 1.0)),  # Blue on the top guide extension.
)


def init():
    # Black background with the origin at the center of the window.
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)  # Configure the mapping from coordinates to screen.
    glLoadIdentity()  # Start with a fresh projection matrix.
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)  # Switch back to the matrix used for drawing.
    glLoadIdentity()  # Draw with no translation, rotation, or scaling.


def pixel_round(value):
    # Round halves away from zero: 2.5 becomes 3, and -2.5 becomes -3.
    return int(value + 0.5 * sign(value))


def draw_line_bresenham(x0, y0, x1, y1, color_by_region=True):
    # Cohen-Sutherland tells us whether this segment has an accepted inside part.
    clipped = cohen_sutherland(x0, y0, x1, y1) if color_by_region else None
    if color_by_region and clipped is None:
        return  # Reject the entire segment if none of it enters the rectangle.
    x0, y0, x1, y1 = map(pixel_round, (x0, y0, x1, y1))  # Use integer pixels.
    dx = abs(x1 - x0)  # Horizontal distance, independent of direction.
    dy = abs(y1 - y0)  # Vertical distance, independent of direction.
    step_x = 1 if x0 < x1 else -1  # Move right or left toward the endpoint.
    step_y = 1 if y0 < y1 else -1  # Move up or down toward the endpoint.
    decision = dx - dy  # All-octant Bresenham error value.

    while True:
        # Emit each pixel exactly once, in its final color. No yellow underlay.
        if color_by_region:  # Guides keep their gray color instead.
            if clipped is not None and region_code(x0, y0) == 0:
                glColor3f(0.0, 1.0, 0.0)  # Inside the rectangle: green.
            else:
                glColor3f(1.0, 1.0, 0.0)  # Outside portion of an accepted line: yellow.
        glVertex2i(x0, y0)  # Plot the current pixel.
        if x0 == x1 and y0 == y1:  # Include the final endpoint before stopping.
            break

        twice_decision = 2 * decision  # Both tests must use the same old error.
        if twice_decision > -dy:
            decision -= dy  # Adjust the error after a horizontal step.
            x0 += step_x  # Advance one pixel horizontally.
        if twice_decision < dx:
            decision += dx  # Adjust the error after a vertical step.
            y0 += step_y  # Advance one pixel vertically; both steps may happen.


def region_code(x, y):
    # Bit order is TOP BOTTOM RIGHT LEFT, e.g. upper-left is 1001 (9).
    code = 0  # Assume inside until a boundary comparison says otherwise.
    
    if x < XMIN:
        code |= LEFT  # Set the left bit without clearing any other bits.
    elif x > XMAX:
        code |= RIGHT  # Set the right bit.

    if y < YMIN:
        code |= BOTTOM  # Set the bottom bit.
    elif y > YMAX:
        code |= TOP  # Set the top bit.

    return code  # Points exactly on a border count as inside.


def cohen_sutherland(x0, y0, x1, y1):
    # Work on local copies so the original random endpoints remain unchanged.
    while True:
        code0 = region_code(x0, y0)  # Recompute after each endpoint replacement.
        code1 = region_code(x1, y1)

        # OR is zero only when neither endpoint has an outside bit.
        if (code0 | code1) == 0:
            return x0, y0, x1, y1  # Both endpoints are inside: accept.
        if code0 & code1:  # A shared bit puts both points outside the same side.
            return None  # Both lie outside the same boundary: reject.

        outside = code0 if code0 else code1  # Pick an endpoint that needs clipping.
        # Intersect with one boundary selected by its outside bit.
        # Use x=x0+t*(x1-x0), y=y0+t*(y1-y0) to find the other coordinate.
        if outside & TOP:
            x = x0 + (x1 - x0) * (YMAX - y0) / (y1 - y0)
            y = YMAX  # Fix y at the top edge.
        elif outside & BOTTOM:
            x = x0 + (x1 - x0) * (YMIN - y0) / (y1 - y0)
            y = YMIN  # Fix y at the bottom edge.
        elif outside & RIGHT:
            y = y0 + (y1 - y0) * (XMAX - x0) / (x1 - x0)
            x = XMAX  # Fix x at the right edge.
        else:
            y = y0 + (y1 - y0) * (XMIN - x0) / (x1 - x0)
            x = XMIN  # Fix x at the left edge.

        # Replace only the chosen endpoint and repeat acceptance/rejection tests.
        # Parallel lines outside an edge are already handled by trivial rejection.
        if outside == code0:
            x0, y0 = x, y
        else:
            x1, y1 = x, y


def boundary_intersections(x0, y0, x1, y1):
    # Only accepted clipping endpoints on the actual rectangle edges are marked.
    clipped = cohen_sutherland(x0, y0, x1, y1)
    if clipped is None:
        return []  # A rejected line has no visible clipping markers.

    hits = []  # At most two distinct boundary endpoints per accepted segment.
    for x, y in ((clipped[0], clipped[1]), (clipped[2], clipped[3])):
        # A small tolerance avoids missing a border due to floating-point error.
        on_edge = (abs(x - XMIN) < 1e-7 or abs(x - XMAX) < 1e-7
                   or abs(y - YMIN) < 1e-7 or abs(y - YMAX) < 1e-7)
        # Interior endpoints aren't intersections; a corner touch gets one marker.
        if on_edge and not any(abs(x - hx) < 1e-7 and abs(y - hy) < 1e-7
                               for hx, hy in hits):
            hits.append((x, y))  # Save one marker for this actual rectangle edge hit.
    return hits


def outside_intersections(x0, y0, x1, y1):
    # Find crossings of the ORIGINAL segment with extended boundary guide lines.
    hits = []
    for name, axis, boundary, color in OUTSIDE_GUIDES:
        start = (x0, y0)[axis]
        delta = (x1 - x0, y1 - y0)[axis]
        if delta == 0:
            continue  # A parallel or coincident segment has no unique crossing.

        t = (boundary - start) / delta
        if not 0.0 <= t <= 1.0:
            continue  # Don't extend the segment itself beyond its endpoints.

        x = boundary if axis == 0 else x0 + t * (x1 - x0)
        y = boundary if axis == 1 else y0 + t * (y1 - y0)
        # Actual rectangle-edge hits are handled separately and remain red.
        outside = (y < YMIN - 1e-7 or y > YMAX + 1e-7) if axis == 0 else (
            x < XMIN - 1e-7 or x > XMAX + 1e-7)
        if outside:
            hits.append((name, x, y, color))
    return hits


def keyboard(key, mouse_x, mouse_y):
    if key.lower() != b'q':  # GLUT supplies normal keys as bytes; accept q or Q.
        return  # Other keys leave the drawing unchanged.

    # Generate in a larger area, including positions beyond the OpenGL window.
    while True:
        x0 = random.randint(RANDOM_XMIN, RANDOM_XMAX)
        y0 = random.randint(RANDOM_YMIN, RANDOM_YMAX)
        x1 = random.randint(RANDOM_XMIN, RANDOM_XMAX)
        y1 = random.randint(RANDOM_YMIN, RANDOM_YMAX)
        if (x0, y0) != (x1, y1):
            break  # Avoid a zero-length randomly generated line.
    segment = (x0, y0, x1, y1)  # Preserve the original, unclipped endpoints.

    print(f"\nOriginal endpoints: ({x0}, {y0}) -> ({x1}, {y1})")
    clipped = cohen_sutherland(*segment)  # Decide whether any part is accepted.
    if clipped is None:
        print("Rejected: no part lies inside the rectangle. Nothing added.")
        return  # Do not save or display a rejected line or its endpoints.

    segments.append(segment)  # Add the accepted original line without removing older ones.
    print(f"Clipped segment: {clipped}")
    for x, y in boundary_intersections(*segment):
        print(f"  Rectangle-edge intersection: ({x:.2f}, {y:.2f})")
    for name, x, y, _ in outside_intersections(*segment):
        print(f"  Outside {name} guide intersection: ({x:.2f}, {y:.2f})")
    glutPostRedisplay()  # Ask GLUT to redraw all saved lines.


def display():
    glClear(GL_COLOR_BUFFER_BIT)  # Start a clean back buffer on every redraw.
    glColor3f(0.4, 0.4, 0.4)  # Gray axes and clipping guides.
    glPointSize(1.0)  # Lines are one pixel thick.

    left, right = -WIDTH // 2, WIDTH // 2 - 1
    bottom, top = -HEIGHT // 2, HEIGHT // 2 - 1

    glBegin(GL_POINTS)  # Bresenham emits individual pixels, not GL_LINES.

    # Vertical lines: x stays fixed while y spans the window.
    for x in (0, XMAX, XMIN):
        draw_line_bresenham(x, bottom, x, top, color_by_region=False)

    # Horizontal lines: y stays fixed while x spans the window.
    for y in (0, YMAX, YMIN):
        draw_line_bresenham(left, y, right, y, color_by_region=False)

    # Highlight just the small clipping rectangle in bright white.
    glColor3f(1.0, 1.0, 1.0)
    draw_line_bresenham(XMIN, YMIN, XMAX, YMIN, color_by_region=False)
    draw_line_bresenham(XMAX, YMIN, XMAX, YMAX, color_by_region=False)
    draw_line_bresenham(XMAX, YMAX, XMIN, YMAX, color_by_region=False)
    draw_line_bresenham(XMIN, YMAX, XMIN, YMIN, color_by_region=False)

    glEnd()

    # Redraw the saved lines after clearing the back buffer on each frame.
    glPointSize(1.0)
    glBegin(GL_POINTS)
    for segment in segments:
        draw_line_bresenham(*segment)
    glEnd()

    for segment in segments:
        # Draw the two original endpoints as large white points.
        glPointSize(7.0)
        glBegin(GL_POINTS)
        glColor3f(1.0, 1.0, 1.0)
        glVertex2i(segment[0], segment[1])
        glVertex2i(segment[2], segment[3])
        glEnd()

        # Outside guide crossings get a different color for each boundary line.
        glPointSize(9.0)
        glBegin(GL_POINTS)
        for _, x, y, color in outside_intersections(*segment):
            glColor3f(*color)
            glVertex2i(pixel_round(x), pixel_round(y))

        # Keep the actual clipping entry/exit points red.
        glColor3f(*INTERSECTION_COLOR)
        for x, y in boundary_intersections(*segment):
            glVertex2i(pixel_round(x), pixel_round(y))
        glEnd()

    glutSwapBuffers()  # Show the completed back buffer to avoid partial frames.


def main():
    glutInit()  # Initialize GLUT before creating the window.
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # RGB colors and double buffering.
    glutInitWindowSize(WIDTH, HEIGHT)  # Set the 960x540 window dimensions.
    glutInitWindowPosition(300, 300)  # Place the window on the desktop.
    glutCreateWindow(b"Lab 07 - Cohen-Sutherland - 09 Nov 26")

    init()  # Set the background and centered coordinates.
    glutDisplayFunc(display)  # Register the function called for redraws.
    glutKeyboardFunc(keyboard)  # Register q-key endpoint generation.
    print("Press q to add a random segment. Previous lines stay. Outside: yellow; inside: green.")
    print("Segments completely outside the clipping rectangle are rejected.")
    print("Rectangle-edge intersections: red. Original endpoints: white.")
    print("Outside guide hits: xmin orange, xmax cyan, ymin magenta, ymax blue.")
    glutMainLoop()  # Process key presses, redraws, and window events.


if __name__ == "__main__":  # Launch only when this file is run directly.
    main()
