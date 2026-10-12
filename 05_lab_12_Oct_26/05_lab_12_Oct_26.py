import os

os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

RADIUS = 100
XC = 0
YC = 0
DELAY_MS = 2
dx = -2
dy = 1


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def draw8way(x, y, xc, yc):
    glVertex2i(xc + x, yc + y)
    glVertex2i(xc + y, yc + x)
    glVertex2i(xc - y, yc + x)
    glVertex2i(xc - x, yc + y)
    glVertex2i(xc - x, yc - y)
    glVertex2i(xc - y, yc - x)
    glVertex2i(xc + y, yc - x)
    glVertex2i(xc + x, yc - y)




def draw_circle_0(radius, xc, yc):
    x = radius
    y = 0
    decision = 3 - 2 * radius

    while y <= x:
        
        draw8way(x, y, xc, yc)

        if decision < 0:
            decision += 4 * y + 6
        else:
            decision += 4 * (y - x) + 10
            x -= 1

        y += 1


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(1.0)
    glColor3f(1.0, 1.0, 1.0)

    glBegin(GL_POINTS)

    draw_circle_0(RADIUS, XC, YC) // 32 % 8 = 0

    glEnd()
    glutSwapBuffers()


def update_position(_):
    global XC, YC, dx, dy

    XC += dx
    YC += dy

    left = -WIDTH // 2 + RADIUS
    right = WIDTH // 2 - 1 - RADIUS
    bottom = -HEIGHT // 2 + RADIUS
    top = HEIGHT // 2 - 1 - RADIUS

    if XC <= left and dx < 0:
        XC = left
        dx = -dx
    elif XC >= right and dx > 0:
        XC = right
        dx = -dx

    if YC <= bottom and dy < 0:
        YC = bottom
        dy = -dy
    elif YC >= top and dy > 0:
        YC = top
        dy = -dy

    glutPostRedisplay()
    glutTimerFunc(DELAY_MS, update_position, 0)


##.....................................
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(300, 300)
glutCreateWindow(b"Bresenham Circle - First Octant - Lab 05 - 12 Oct 26")

init()
glutDisplayFunc(display)
glutTimerFunc(DELAY_MS, update_position, 0)
glutMainLoop()
