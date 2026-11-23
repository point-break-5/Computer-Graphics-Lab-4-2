# Name: Anirban Roy Sourov
# Roll: 32
# Lab: 08 - Cyrus-Beck Line Clipping

import math
import os
import struct
import tempfile
import zlib
from pathlib import Path

# Select the Linux OpenGL backend before importing PyOpenGL.
os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D

WIDTH, HEIGHT = 960, 540  # Logical canvas and initial window size.
# Use the same clipping rectangle as Lab 07.
XMIN, XMAX = -250, 249
YMIN, YMAX = -200, 199
EPSILON = 1e-9
PINK = (1.0, 0.4, 0.7)
REJECTED_LINE_COLOR = (0.12, 0.12, 0.12)
REJECTED_POINT_COLOR = (0.20, 0.20, 0.20)

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
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Clear each frame to black.
    reshape(WIDTH, HEIGHT)


def reshape(width, height):
    global window_width, window_height
    # Keep the viewport and mouse conversion in sync after a resize.
    window_width, window_height = max(1, width), max(1, height)
    glViewport(0, 0, window_width, window_height)
    # Map the centered logical coordinates onto the full viewport.
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-WIDTH // 2, WIDTH // 2 - 1, -HEIGHT // 2, HEIGHT // 2 - 1)
    # Leave the drawing coordinates untransformed.
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def pixel_round(value):
    # Same half-away-from-zero rounding used in earlier labs.
    return int(value + 0.5 * (1 if value > 0 else -1 if value < 0 else 0))


def inside(x, y):
    # A pixel on a clipping edge counts as inside.
    return XMIN <= x <= XMAX and YMIN <= y <= YMAX


def cyrus_beck(p0, p1):
    # P(t) = P0 + t*D, with 0 <= t <= 1 for the ORIGINAL segment.
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    entering, leaving = [], []
    edge_ts = {}  # Keep each boundary's raw t for the terminal and display.
    parallel_outside = False

    for name, edge_point, normal in EDGES:
        nx, ny = normal
        # Inside means n dot (P(t) - edge_point) <= 0.
        numerator = nx * (edge_point[0] - p0[0]) + ny * (edge_point[1] - p0[1])
        denominator = nx * dx + ny * dy

        if abs(denominator) < EPSILON:
            edge_ts[name] = None
            # Parallel: no finite t. Negative numerator means outside this edge.
            if numerator < -EPSILON:
                parallel_outside = True
            continue

        t = numerator / denominator  # Intersection with the infinite edge line.
        edge_ts[name] = t
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
    # An empty interval or an outside parallel edge rejects the segment.
    accepted = not parallel_outside and t_enter <= t_leave
    clipped = None

    if accepted:
        # Evaluate P(t) at both bounds and guard against roundoff at the edges.
        clipped = (
            (max(XMIN, min(XMAX, p0[0] + t_enter * dx)),
             max(YMIN, min(YMAX, p0[1] + t_enter * dy))),
            (max(XMIN, min(XMAX, p0[0] + t_leave * dx)),
             max(YMIN, min(YMAX, p0[1] + t_leave * dy))),
        )

    return {
        "edge_ts": edge_ts,
        "te_min": te_min, "te_max": te_max,
        "tl_min": tl_min, "tl_max": tl_max,
        "t_enter": t_enter, "t_leave": t_leave,
        "accepted": accepted, "parallel_outside": parallel_outside,
        "clipped": clipped,
    }


def draw_line_bresenham(p0, p1, outside_only=False):
    # Round only for drawing. Keep the clipping coordinates at full precision.
    x0, y0 = map(pixel_round, p0)
    x1, y1 = map(pixel_round, p1)
    # Distances and signed steps let the same routine draw in every octant.
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    decision = dx - dy  # Initial integer error used to pick the next pixel.

    while True:
        # Outside pieces must not emit yellow pixels on or inside the rectangle.
        if not outside_only or not inside(x0, y0):
            glVertex2i(x0, y0)
        if x0 == x1 and y0 == y1:  # Stop after processing the final pixel.
            break
        twice_decision = 2 * decision  # Both tests use the old error.
        if twice_decision > -dy:
            # A horizontal step reduces the accumulated error by dy.
            decision -= dy
            x0 += sx
        if twice_decision < dx:
            # A vertical step adds dx. Both steps can happen on a diagonal.
            decision += dx
            y0 += sy


def format_t(value):
    if value is None:
        return "parallel"  # This boundary has no unique intersection parameter.
    if math.isinf(value):
        return "-inf" if value < 0 else "+inf"
    return f"{value:.4f}"


def on_original_segment(t):
    # A candidate belongs to P0--P1 only for a finite parameter in [0, 1].
    return math.isfinite(t) and 0.0 <= t <= 1.0


def mouse(button, state, x, y):
    global pending_point
    # Accept only a left-button press. Ignore the matching release.
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
        # Derive every t and both clipped endpoints from the selected points.
        result = cyrus_beck(p0, p1)
        lines.append((p0, p1, result))
        pending_point = None  # Next click starts another segment.

        print(f"P0 = {p0}, P1 = {p1}")
        for edge, t in result["edge_ts"].items():
            print(f"t_{edge} = {format_t(t)}")
        print(f"tl_min = {format_t(result['tl_min'])}, tl_max = {format_t(result['tl_max'])}")
        print(f"te_min = {format_t(result['te_min'])}, te_max = {format_t(result['te_max'])}")
        if result["accepted"]:
            print(f"Final interval: [{format_t(result['t_enter'])}, {format_t(result['t_leave'])}]")
            for label, (cx, cy) in zip(("P0", "P1"), result["clipped"]):
                print(f"Clipped {label} = ({cx:.4f}, {cy:.4f})")
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
    draw_scene(lines, pending_point)
    glutSwapBuffers()  # Present the completed frame at once.


def draw_scene(scene_lines, selected_point):
    glClear(GL_COLOR_BUFFER_BIT)  # Build a fresh frame in the back buffer.
    glPointSize(1.0)  # Draw line pixels one at a time.
    glBegin(GL_POINTS)

    # Draw rejected segments first so the guides and accepted lines stay visible.
    glColor3f(*REJECTED_LINE_COLOR)
    for p0, p1, result in scene_lines:
        if not result["accepted"]:
            draw_line_bresenham(p0, p1)

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

    for p0, p1, result in scene_lines:
        if not result["accepted"]:
            continue
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

    # Dim rejected endpoints and keep accepted endpoints white.
    glPointSize(7.0)
    glBegin(GL_POINTS)
    for p0, p1, result in scene_lines:
        endpoint_color = (1.0, 1.0, 1.0) if result["accepted"] else REJECTED_POINT_COLOR
        glColor3f(*endpoint_color)
        for x, y in (p0, p1):
            glVertex2i(x, y)
        if result["accepted"]:
            glColor3f(1.0, 0.0, 0.0)
            for x, y in result["clipped"]:
                if any(abs(value - edge) < EPSILON for value, edge in
                       ((x, XMIN), (x, XMAX), (y, YMIN), (y, YMAX))):
                    glVertex2i(pixel_round(x), pixel_round(y))

            # Accepted segments get pink markers for candidates on P0--P1.
            glColor3f(*PINK)
            for name in ("tl_max", "te_min"):
                t = result[name]
                if on_original_segment(t):
                    x = p0[0] + t * (p1[0] - p0[0])
                    y = p0[1] + t * (p1[1] - p0[1])
                    glVertex2i(pixel_round(x), pixel_round(y))
    if selected_point is not None:
        glColor3f(0.0, 1.0, 1.0)
        glVertex2i(*selected_point)
    glEnd()

    glColor3f(1.0, 1.0, 1.0)
    draw_text(10, window_height - 18, "Left click P0, then P1. Each pair adds a segment.")
    if scene_lines:
        p0, p1, result = scene_lines[-1]
        draw_text(10, window_height - 34, f"Latest: P0={p0}, P1={p1}")
        # Color each text item independently, using the same rule as its marker.
        text_x = 10
        for name in ("tl_min", "tl_max", "te_min", "te_max"):
            highlight = (
                result["accepted"]
                and name in ("tl_max", "te_min")
                and on_original_segment(result[name])
            )
            glColor3f(*(PINK if highlight else (1.0, 1.0, 1.0)))
            label = f"{name}={format_t(result[name])}  "
            draw_text(text_x, window_height - 50, label)
            text_x += 8 * len(label)  # GLUT_BITMAP_8_BY_13 has 8-pixel characters.
        glColor3f(1.0, 1.0, 1.0)
        if result["accepted"]:
            status = (f"ACCEPTED: final t interval "
                      f"[{format_t(result['t_enter'])}, {format_t(result['t_leave'])}]")
        else:
            status = "REJECTED: original segment shown in faint gray"
        draw_text(10, window_height - 66, status)
        # Show the four raw candidates in addition to the entering/leaving extrema.
        edge_labels = [f"t_{edge}={format_t(t)}" for edge, t in result["edge_ts"].items()]
        draw_text(10, 42, "  ".join(edge_labels))
    if selected_point is not None:
        draw_text(10, 58, f"P0={selected_point}; select P1.")
    draw_text(10, 26, "Green: inside | Yellow: outside | Red: clip contacts | Pink: tl_max/te_min on P0--P1")
    draw_text(10, 10, "te/tl extrema use all nonparallel edge candidates; -inf/+inf = no bound.")


def png_chunk(kind, data):
    # Each PNG chunk stores its data length and a checksum.
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def capture_png():
    # Read RGB rows without alignment padding. OpenGL starts at the bottom.
    glReadBuffer(GL_BACK)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    pixels = bytes(glReadPixels(0, 0, window_width, window_height, GL_RGB, GL_UNSIGNED_BYTE))
    stride = window_width * 3
    if len(pixels) != stride * window_height:
        raise RuntimeError("OpenGL returned an incomplete frame")
    rows = b"".join(
        b"\x00" + pixels[offset:offset + stride]
        for offset in range((window_height - 1) * stride, -1, -stride)
    )
    # The leading zero in each row selects PNG's unfiltered row format.
    header = struct.pack(">IIBBBBB", window_width, window_height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(rows)) + png_chunk(b"IEND", b""))


def regenerate_screenshots():
    # Reuse the three submission examples while the closing window still has a GL context.
    examples = (
        ("01_crossing.png", (-400, -240), (400, 240)),
        ("02_inside.png", (-120, -80), (130, 100)),
        ("03_parallel_rejected.png", (-360, 215), (360, 215)),
    )
    output = Path(__file__).resolve().parent / "screenshots"
    try:
        output.mkdir(exist_ok=True)
        # Finish all captures before replacing the existing files.
        with tempfile.TemporaryDirectory(dir=output) as temp:
            staging = Path(temp)
            for filename, p0, p1 in examples:
                draw_scene([(p0, p1, cyrus_beck(p0, p1))], None)
                (staging / filename).write_bytes(capture_png())
            for filename, _, _ in examples:
                (staging / filename).replace(output / filename)
        print(f"Regenerated {len(examples)} screenshots in {output}", flush=True)
    except Exception as error:
        print(f"Could not regenerate screenshots: {error}", flush=True)


def main():
    glutInit()  # Start GLUT before creating a window.
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # Draw in RGB using two buffers.
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Lab 08 - Cyrus-Beck Clipping - 23 Nov 26")
    init()
    # Register the callbacks for redraws, resizing, and endpoint selection.
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    # Keep the C callback alive until FreeGLUT has finished closing the window.
    close_callback = glutCloseFunc(regenerate_screenshots)
    print("Left click P0 and then P1. The latest t values appear in the window and terminal.")
    print("Close the window to regenerate the three Lab 08 screenshots.")
    glutMainLoop()  # Let GLUT process input and redraw events.


if __name__ == "__main__":
    main()
