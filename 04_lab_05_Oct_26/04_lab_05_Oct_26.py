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
THETA_END = 360
THETA_STEP = 1


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def draw_line_bresenham(x0, y0, x1, y1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    decision = dx - dy

    while True:
        glVertex2i(x0, y0)

        if x0 == x1 and y0 == y1:
            break

        twice_decision = 2 * decision

        if twice_decision > -dy:
            decision -= dy
            x0 += step_x

        if twice_decision < dx:
            decision += dx
            y0 += step_y

def draw_line_0(x0, y0, x1, y1):
    glColor3f(1, 0, 0)
    draw_line_bresenham(x0, y0, x1, y1)

def draw_line_1(x0, y0, x1, y1):
    glColor3f(0, 1, 0)
    draw_line_bresenham(x0, y0, x1, y1)

def draw_line_2(x0, y0, x1, y1):
    glColor3f(0, 0, 1)
    draw_line_bresenham(x0, y0, x1, y1)

def draw_line_3(x0, y0, x1, y1):
    glColor3f(0, 1, 1)
    draw_line_bresenham(x0, y0, x1, y1)
    
def draw_line_4(x0, y0, x1, y1):
    glColor3f(1, 0, 1)
    draw_line_bresenham(x0, y0, x1, y1)
    
def draw_line_5(x0, y0, x1, y1):
    glColor3f(1, 1, 0)
    draw_line_bresenham(x0, y0, x1, y1)
    
def draw_line_6(x0, y0, x1, y1):
    glColor3f(1, 1, 1)
    draw_line_bresenham(x0, y0, x1, y1)
    
def draw_line_7(x0, y0, x1, y1):
    glColor3f(0.5, 0.5, 0.5)
    draw_line_bresenham(x0, y0, x1, y1)


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(1.0)
    glBegin(GL_POINTS)

    for theta in range(THETA_START, THETA_END + 1, THETA_STEP):
        angle = math.radians(theta)
        x = RADIUS * math.cos(angle)
        y = RADIUS * math.sin(angle)

        x1 = int(x + 0.5 * sign(x))
        y1 = int(y + 0.5 * sign(y))


        if(abs(x1)>=abs(y1)):
            if(x1 >= 0 and y1 >= 0):
                draw_line_0(0, 0, x1, y1)
            elif(x1 < 0 and y1 >= 0):
                draw_line_3(0, 0, x1, y1)
            elif(x1 < 0 and y1 < 0):
                draw_line_4(0, 0, x1, y1)
            else:
                draw_line_7(0, 0, x1, y1)
        else:
            if(x1 >= 0 and y1 >= 0):
                draw_line_1(0, 0, x1, y1)
            elif(x1 < 0 and y1 >= 0):
                draw_line_2(0, 0, x1, y1)
            elif(x1 < 0 and y1 < 0):
                draw_line_5(0, 0, x1, y1)
            else:
                draw_line_6(0, 0, x1, y1)
            

    glEnd()
    glFlush()


##.....................................
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(300, 300)
glutCreateWindow(b"8 zones, 8 colors - Oct 5 2026, Anirban Roy Sourov, Roll: 32, Reg: 2021311208")

init()
glutDisplayFunc(display)
glutMainLoop()
