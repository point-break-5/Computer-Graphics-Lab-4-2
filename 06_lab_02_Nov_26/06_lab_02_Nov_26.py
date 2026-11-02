# Name: Anirban Roy Sourov
# Roll: 32
# Lab: 06 - Falling Circle and Squeezing Ellipse

import os
import math

os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

# Change these settings to adjust the animation.
RADIUS = 25
XC = 0
GRAVITY = 5.0  # Downward acceleration in pixels/frame^2.
SQUEEZE_ACCELERATION = -1.0  # Deceleration of positive compression speed (px/frame^2).
MAX_AXIS_RATIO = 2.0  # Stop squeezing when a reaches twice b.
DELAY_MS = 50  # Wall-clock delay between frames; physics uses one frame per tick.

TOP = HEIGHT // 2 - 1
BOTTOM = -HEIGHT // 2

# Start as a circle, just touching the top, with zero falling velocity.
a = float(RADIUS)
b = float(RADIUS)
YC = float(TOP - RADIUS)
fall_velocity = 0.0
squeeze_velocity = 0.0
phase = "falling"

# Corrected constraint: a=b=r initially means a^2+b^2 must equal 2r^2.
AXIS_SUM_SQUARED = 2.0 * RADIUS * RADIUS
# At the squeeze limit, a = MAX_AXIS_RATIO*b and a^2+b^2 stays constant.
MIN_B = math.sqrt(AXIS_SUM_SQUARED / (MAX_AXIS_RATIO ** 2 + 1))


def init():
    # Black background, with (0, 0) in the middle of the window.
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def draw4way(x, y, xc, yc):
    # Reflect the offsets, then add the same center to all four points.
    glVertex2i(xc + x, yc + y)
    glVertex2i(xc - x, yc + y)
    glVertex2i(xc - x, yc - y)
    glVertex2i(xc + x, yc - y)


def draw_circle(radius, xc, yc):
    # Bresenham circle: start at (r, 0), then reflect into all eight octants.
    x = radius
    y = 0
    decision = 3 - 2 * radius

    while y <= x:
        draw4way(x, y, xc, yc)
        draw4way(y, x, xc, yc)

        if decision < 0:
            decision += 4 * y + 6
        else:
            decision += 4 * (y - x) + 10
            x -= 1

        y += 1


def draw_ellipse(rx, ry, xc, yc):
    # Even roll (32): start at (a, 0), the rightmost point.
    x = rx
    y = 0
    rx2 = rx * rx
    ry2 = ry * ry

    # Steep region: step upward, choosing N or NW.
    # Test the midpoint (x - 0.5, y + 1).
    decision = rx2 - ry2 * rx + 0.25 * ry2

    while rx2 * y < ry2 * x:
        draw4way(x, y, xc, yc)

        if decision < 0:
            # N: move up, keeping the same x.
            decision += rx2 * (2 * y + 3)
        else:
            # NW: move up and left. Update using the old x and y.
            decision += rx2 * (2 * y + 3) + ry2 * (-2 * x + 2)
            x -= 1

        y += 1

    # Shallow region: step left, choosing NW or W.
    # Test the midpoint (x - 1, y + 0.5).
    decision = ry2 * (x - 1) ** 2 + rx2 * (y + 0.5) ** 2 - rx2 * ry2

    while x >= 0:
        draw4way(x, y, xc, yc)

        if decision < 0:
            # NW: move left and up.
            decision += ry2 * (-2 * x + 3) + rx2 * (2 * y + 2)
            y += 1
        else:
            # W: move straight left.
            decision += ry2 * (-2 * x + 3)

        x -= 1


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(1.0)
    glColor3f(1.0, 1.0, 1.0)

    glBegin(GL_POINTS)
    if phase in ("falling", "rising"):
        draw_circle(RADIUS, XC, round(YC))
    else:
        # Keep physics values as floats; round only for pixel drawing.
        draw_ellipse(round(a), round(b), XC, round(YC))
    glEnd()

    # Show the finished frame using double buffering.
    glutSwapBuffers()


def update_animation(_):
    global YC, a, b, fall_velocity, squeeze_velocity, phase

    if phase == "falling":
        # Positive velocity means downward, but OpenGL's y increases upward.
        # For one frame: distance = v + acceleration/2, then v += acceleration.
        YC -= fall_velocity + 0.5 * GRAVITY
        fall_velocity += GRAVITY

        if YC - RADIUS <= BOTTOM:
            # Land exactly on the floor, without letting the circle go through it.
            YC = float(BOTTOM + RADIUS)
            # Carry the last downward speed into compression before resetting it.
            squeeze_velocity = fall_velocity
            fall_velocity = 0.0
            phase = "squeezing"

    elif phase == "squeezing":
        previous_axes = (round(a), round(b))
        # Positive squeeze speed reduces b; negative acceleration slows that speed.
        # If it stops within this frame, integrate only up to the stopping time.
        dt = min(1.0, squeeze_velocity / -SQUEEZE_ACCELERATION)
        compression = squeeze_velocity * dt + 0.5 * SQUEEZE_ACCELERATION * dt * dt
        squeeze_velocity = max(0.0, squeeze_velocity + SQUEEZE_ACCELERATION * dt)
        b = max(MIN_B, b - compression)

        # As b shrinks, a grows while the corrected constraint stays true.
        a = math.sqrt(AXIS_SUM_SQUARED - b * b)
        YC = BOTTOM + b  # Keep the ellipse's bottom on the floor while squeezing.

        # Bounce as soon as the squeeze hits its limit or stops changing pixels.
        # Don't wait for an invisible speed countdown while the shape is clamped.
        if b <= MIN_B or (round(a), round(b)) == previous_axes or squeeze_velocity == 0.0:
            squeeze_velocity = 0.0
            phase = "expanding"

    elif phase == "expanding":
        # Reverse the squeeze acceleration so b grows back toward the radius.
        b += squeeze_velocity - 0.5 * SQUEEZE_ACCELERATION
        squeeze_velocity -= SQUEEZE_ACCELERATION
        b = min(b, float(RADIUS))
        a = math.sqrt(AXIS_SUM_SQUARED - b * b)
        YC = BOTTOM + b

        if b == RADIUS:
            # The shape is a circle again. Launch it high enough to reach the top.
            # v^2 = 2*g*h; negative velocity means upward in our convention.
            travel_height = TOP - BOTTOM - 2 * RADIUS
            fall_velocity = -math.sqrt(2 * GRAVITY * travel_height)
            squeeze_velocity = 0.0
            phase = "rising"

    elif phase == "rising":
        YC -= fall_velocity + 0.5 * GRAVITY
        fall_velocity += GRAVITY  # Gravity slows the upward motion.

        # A frame can straddle the exact apex, so snap to the top at that moment.
        if fall_velocity >= 0 or YC + RADIUS >= TOP:
            YC = float(TOP - RADIUS)
            fall_velocity = 0.0
            phase = "falling"

    glutPostRedisplay()
    # Always schedule another frame so the bouncing continues forever.
    glutTimerFunc(DELAY_MS, update_animation, 0)


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(300, 300)
    glutCreateWindow(b"Falling Circle and Squeezing Ellipse - Lab 06")

    init()
    glutDisplayFunc(display)
    glutTimerFunc(DELAY_MS, update_animation, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
