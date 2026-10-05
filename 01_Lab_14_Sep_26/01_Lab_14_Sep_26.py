import os
os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540

def init():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-480, 479, -270, 269)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glClearColor(0, 0, 0, 1.0)   # black background

    glPointSize(1.0)
    glColor3f(1.0, 1.0, 1.0)   # white

    glBegin(GL_POINTS)

    # for x in range(-480, 480):
    #     for y in range(-270, 270):
    #         if((x and not y) or (not x and y)):
    #             glVertex2i(x, y)

    for x in range(-1, 2):       # -1, 0, 1
        for y in range(-1, 2):   # -1, 0, 1
            glVertex2i(x, y)

    
    # glColor3f(1.0, 0, 0)   # red

    # for x in range(-10, -7):       
    #     for y in range(-10, -7):   
    #         glVertex2i(x, y)

    glEnd()

    glFlush()


##.....................................
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(WIDTH, HEIGHT)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"3x3 Pixel Block")

init()
glutDisplayFunc(display)
glutMainLoop()