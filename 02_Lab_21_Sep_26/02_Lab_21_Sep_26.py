import os

from numpy import sign
os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

def init():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-48, 47, -27, 26)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glClearColor(1, 1, 1, 1.0)   # background color
    glColor3f(1.0, 0.0, 0.0)   # pixel color


    #########################################
    glPointSize(5.0)
    glBegin(GL_POINTS)


    #Coordinate 

    for i in range(-48, 48):
        for j in range(-27, 27):
            if(i == 0 or j == 0):
                glVertex2i(i, j)
    glEnd()
    
    glPointSize(10.0)
    glBegin(GL_POINTS)


    x0, y0 = -5, 7
    x1, y1 = 6, -8

    # x0, y0 = -2, 3
    # x1, y1 = 2, -3

    steps = max(abs(x1 - x0), abs(y1 - y0))

    x_increment = (x1 - x0) / steps
    y_increment = (y1 - y0) / steps

    x = x0
    y = y0

    for i in range(steps+1):
        glVertex2i(int(x + 0.5 * sign(x)), int(y + 0.5 * sign(y)))
        x += x_increment
        y += y_increment

    #########################################

    glEnd()

    glFlush()


##.....................................
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(300, 300)
glutCreateWindow(b"DDA - Lab 21 Sep 26")

init()
glutDisplayFunc(display)
glutMainLoop()