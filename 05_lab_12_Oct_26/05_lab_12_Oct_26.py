# Name: Anirban Roy Sourov
# Roll: 32
# Lab: 05 - Bouncing Circle
# Zone: 32 % 8 = 0

import os

# Use the Linux OpenGL backend.
os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

# Change these to adjust the circle's size and starting center.
RADIUS = 100
XC = 0
YC = 0
# Smaller delay means more frequent animation updates (milliseconds).
DELAY_MS = 1
# Movement per update: negative x goes left, positive y goes up.
dx = -2
dy = 1


def init():
    # Black background, with (0, 0) in the middle of the window.
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def draw8way(x, y, xc, yc):
    # One calculated point gives us eight points using circle symmetry.
    # Add the center AFTER reflecting the offsets so the circle moves together.
    glVertex2i(xc + x, yc + y)
    glVertex2i(xc + y, yc + x)
    glVertex2i(xc - y, yc + x)
    glVertex2i(xc - x, yc + y)
    glVertex2i(xc - x, yc - y)
    glVertex2i(xc - y, yc - x)
    glVertex2i(xc + y, yc - x)
    glVertex2i(xc + x, yc - y)


def draw_circle_0(radius, xc, yc):
    # Start at the rightmost point and work upward toward the 45-degree line.
    x = radius
    y = 0
    decision = 3 - 2 * radius  # Initial Bresenham decision value.

    while y <= x:
        # Calculate just octant 0; symmetry fills in the rest of the circle.
        draw8way(x, y, xc, yc)

        if decision < 0:
            # Go straight up: keep x and update the decision for the next step. (N)
            decision += 4 * y + 6
        else:
            # Go up and left: use the OLD x and y to update the decision first. (NW)
            decision += 4 * (y - x) + 10
            x -= 1

        y += 1  # Both choices move upward by one pixel.


def display():
    # Start a fresh frame so the previous position doesn't leave a trail.
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(1.0)
    glColor3f(1.0, 1.0, 1.0)

    glBegin(GL_POINTS)

    draw_circle_0(RADIUS, XC, YC) # 32 % 8 = 0

    glEnd()
    # The drawing is ready; swap the back buffer onto the screen.
    glutSwapBuffers()


def update_position(_):
    # Update the shared center and velocity, rather than making local copies.
    global XC, YC, dx, dy

    # Move the whole circle by the current velocity.
    XC += dx
    YC += dy

    # These are limits for the CENTER, leaving room for the circle's radius.
    left = -WIDTH // 2 + RADIUS
    right = WIDTH // 2 - 1 - RADIUS
    bottom = -HEIGHT // 2 + RADIUS
    top = HEIGHT // 2 - 1 - RADIUS

    # At a side wall, keep the circle inside and reverse horizontal movement.
    # Check the direction too, so a circle already moving away won't bounce again.
    if XC <= left and dx < 0:
        XC = left
        dx = -dx
    elif XC >= right and dx > 0:
        XC = right
        dx = -dx

    # Top and bottom walls reverse vertical movement. Corners reverse both.
    if YC <= bottom and dy < 0:
        YC = bottom
        dy = -dy
    elif YC >= top and dy > 0:
        YC = top
        dy = -dy

    # Ask GLUT to draw the new position, then schedule the next update.
    glutPostRedisplay()
    glutTimerFunc(DELAY_MS, update_position, 0)


# Create the window and let GLUT handle drawing, timers, and window events.
glutInit()
# Double buffering lets us finish a frame before showing it.
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(300, 300)
glutCreateWindow(b"Bresenham Circle - First Octant - Lab 05 - 12 Oct 26")

init()
glutDisplayFunc(display)
# Start the animation timer; update_position schedules the following ticks.
glutTimerFunc(DELAY_MS, update_position, 0)
glutMainLoop()
