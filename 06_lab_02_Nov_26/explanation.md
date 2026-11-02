# Lab 06: Falling Circle and Squeezing Ellipse

## 1. What the program does

A circle starts at the top of the window with zero velocity. It falls under gravity, touches the floor, and squeezes into an ellipse. The ellipse becomes a circle again and bounces upward until it touches the top. This cycle continues forever.

```text
Falling → Squeezing → Expanding → Rising → Falling → ...
```

The program draws the pixels itself: Bresenham's algorithm draws the circle, and the midpoint ellipse algorithm draws the ellipse. OpenGL displays those pixels.

## 2. Settings at the top

| Setting | Current value | Meaning |
| --- | --- | --- |
| `WIDTH, HEIGHT` | `960, 540` | Window size |
| `RADIUS` | `25` | Initial circle radius |
| `XC` | `0` | Horizontal center; it stays fixed |
| `GRAVITY` | `5.0` | Downward acceleration in pixels/frame² |
| `SQUEEZE_ACCELERATION` | `-1.0` | Deceleration of the positive compression speed |
| `MAX_AXIS_RATIO` | `2.0` | Maximum squeeze: `a = 2b` |
| `DELAY_MS` | `50` | Requested delay between animation updates |

Here, `a` and `b` are **semi-axes**, meaning radii rather than full widths:

- `a`: horizontal radius, so the full width is `2a`.
- `b`: vertical radius, so the full height is `2b`.

Initially, `a = b = 25`, so the shape is a circle.

## 3. Coordinates and initial position

The window uses these logical coordinates:

```text
x: -480 to 479
y: -270 to 269
```

The origin is in the middle, and positive y points upward.

The top border is `269`. To place the circle just below it:

```python
YC = TOP - RADIUS  # 269 - 25 = 244
```

The circle's top is therefore `YC + RADIUS = 269`, exactly at the border. Its initial falling velocity is `0`.

## 4. Drawing the circle with Bresenham's algorithm

Start at the rightmost offset:

```python
x = radius
y = 0
decision = 3 - 2 * radius
```

Move upward through one octant. Each step has two choices:

| Decision | Next pixel | Decision update, using old `x` and `y` |
| --- | --- | --- |
| `decision < 0` | N: `(x, y + 1)` | `decision += 4*y + 6` |
| Otherwise | NW: `(x - 1, y + 1)` | `decision += 4*(y - x) + 10` |

In the NW case, decrease `x`. In both cases, increase `y`. Stop after `y > x`, because symmetry covers the rest.

The circle equation is `x² + y² = r²`. The decision variable comes from checking between the two candidate pixels, so the loop needs additions and comparisons instead of calculating square roots for each pixel.

### How the whole circle appears

`draw4way(x, y, xc, yc)` plots:

```text
(xc + x, yc + y)    (xc - x, yc + y)
(xc + x, yc - y)    (xc - x, yc - y)
```

For the circle, calling it again with swapped offsets `(y, x)` supplies the other four symmetric points. Together, the calls give eight-way symmetry. Some axis and diagonal points overlap, which is harmless.

## 5. Falling under gravity

`fall_velocity` uses a convenient convention: **positive means downward**. Since screen y increases upward, downward displacement is subtracted from `YC`.

For each update, the time step is one frame:

```python
YC -= fall_velocity + 0.5 * GRAVITY
fall_velocity += GRAVITY
```

These come from:

```text
distance = v*Δt + ½*g*Δt²
new velocity = v + g*Δt
```

With `Δt = 1`, they become `distance = v + g/2` and `new velocity = v + g`.

For example, starting from rest with `g = 5`:

| Update | Velocity before update | Downward distance | Velocity afterward |
| --- | --- | --- | --- |
| 1 | 0 | 2.5 pixels | 5 |
| 2 | 5 | 7.5 pixels | 10 |
| 3 | 10 | 12.5 pixels | 15 |

The distances increase, so the circle visibly speeds up. `DELAY_MS` changes playback speed; the formulas still use pixels per animation frame, not seconds.

## 6. Detecting the floor

The bottom of the falling circle is `YC - RADIUS`. Contact happens when:

```python
YC - RADIUS <= BOTTOM
```

A frame might move it slightly beyond the floor. The code corrects that by setting:

```python
YC = BOTTOM + RADIUS  # -270 + 25 = -245
```

It copies the last falling velocity into `squeeze_velocity`, resets `fall_velocity` to zero, and changes `phase` to `"squeezing"`. Thus compression starts with the ball's last downward speed, not from rest.

## 7. Squeezing and the axis constraint

During squeezing, a positive compression speed reduces the vertical radius `b`. The speed slows down with acceleration `-1`. These are the actual calculations in the code:

```python
previous_axes = (round(a), round(b))

dt = min(1.0, squeeze_velocity / -SQUEEZE_ACCELERATION)
compression = squeeze_velocity * dt + 0.5 * SQUEEZE_ACCELERATION * dt * dt
squeeze_velocity = max(0.0, squeeze_velocity + SQUEEZE_ACCELERATION * dt)
b = max(MIN_B, b - compression)

a = math.sqrt(AXIS_SUM_SQUARED - b * b)
YC = BOTTOM + b
```

Normally `dt = 1`, meaning a complete animation frame. If the speed would reach zero sooner, `dt` uses only that remaining time. For example, with speed `0.4` and deceleration `-1`, the stopping time is `0.4` frames. This prevents the compression speed from becoming negative and accidentally reversing the squeeze.

For these settings, the last falling velocity is `70` pixels/frame. Without a limit, the compression speed would become `69, 68, 67, ...` until zero. The first requested displacement is `69.5` pixels. The code integrates only the remaining stopping time if the speed reaches zero partway through a frame.

However, the allowed reduction in `b` is only about `9.19` pixels. Therefore the ratio limit is reached on the first compression frame. The code immediately switches to expansion and resets compression speed instead of waiting. It also switches if a squeeze update leaves both rounded pixel radii unchanged. This bounce rule overrides deceleration to zero when deformation is blocked, preventing a visible pause.

### Why the code uses `a² + b² = 2r²`

The teacher's instructions say both `a = b = r` initially and `a² + b² = r²`. These cannot both hold for a nonzero radius.

For the required initial circle with `r = 25`, we use the corrected constant:

```text
a² + b² = 25² + 25² = 1250 = 2r²
```

After updating `b`, calculate:

```python
a = math.sqrt(AXIS_SUM_SQUARED - b * b)
```

As `b` shrinks, `a` grows. This preserves the sum of squared semi-axes; it does not preserve area.

### Keep the shape on the floor

```python
YC = BOTTOM + b
```

Therefore `YC - b = BOTTOM` at every squeezing or expanding step. The center moves down as the ellipse flattens, keeping its bottom on the floor.

## 8. Limiting the squeeze to `a = 2b`

At maximum squeeze, substitute `a = 2b` into the constraint:

```text
(2b)² + b² = 1250
5b² = 1250
b = √250 ≈ 15.81
a = 2b ≈ 31.62
```

The general formula in the code is:

```python
MIN_B = math.sqrt(AXIS_SUM_SQUARED / (MAX_AXIS_RATIO ** 2 + 1))
```

If an update would take `b` below this limit, the code sets it exactly to `MIN_B` and switches to expansion immediately. The continuous axis values satisfy the constraint; their displayed pixel values are rounded.

### Immediate bounce when squeezing stops changing pixels

Before squeezing, the program saves `(round(a), round(b))`. After updating, it compares the new rounded axes with the saved pair:

```python
if b <= MIN_B or (round(a), round(b)) == previous_axes or squeeze_velocity == 0.0:
    squeeze_velocity = 0.0
    phase = "expanding"
```

Any one of these conditions ends compression:

1. The ellipse reaches its maximum permitted squeeze, `a = 2b`.
2. Both pixel radii stay unchanged after the update.
3. Compression speed reaches zero naturally.

The second test compares rendered axis lengths, not the circle's distance from the floor. During squeezing, the bottom is supposed to stay on the floor.

The code no longer waits for the compression speed to count all the way down after the shape reaches its limit. At a limit or unchanged-pixel event, it explicitly resets the speed to zero. Therefore the `-1` deceleration applies during active compression, but the bounce rule can end it early. This is what removes the long stationary pause.

With the current settings, the sequence around contact is:

| Update | What happens |
| --- | --- |
| Contact | Save the last falling speed, `70`, as compression speed. |
| First squeeze update | Request `69.5` pixels of compression, clamp `b` to `15.81`, calculate `a ≈ 31.62`, and switch to expansion. |
| Next update | Expand from zero deformation speed with acceleration `+1`; `b` increases by `0.5`. |
| Following updates | Continue expanding until `a = b = 25`, then launch upward. |

At `DELAY_MS = 50`, each update is requested about 50 ms after the previous one. “Immediate” means the phase switches in the current update and expansion starts on the next scheduled update, without an extra waiting phase.

## 9. Drawing the ellipse for even roll 32

Because my roll is even, the ellipse algorithm starts at `(a, 0)`:

```python
x = rx  # a
y = 0
```

The ellipse equation, using offsets from its center, is:

```text
F(x,y) = b²x² + a²y² - a²b²
```

`F < 0` means inside, and `F > 0` means outside. The midpoint test uses this sign to choose between neighboring pixels.

### First part: move upward through the steep region

Start with the midpoint `(x - ½, y + 1)`. Substituting the starting point `(a, 0)` gives:

```text
decision = a² - b²a + ¼b²
```

Continue while `a²y < b²x`. This condition comes from the slope magnitude of the ellipse, `|dy/dx| = b²x / (a²y)`: this part is steeper than 45°.

| Decision | Choice | Update using old coordinates |
| --- | --- | --- |
| Negative | N: keep `x` | `decision += a²(2y + 3)` |
| Otherwise | NW: decrease `x` | `decision += a²(2y + 3) + b²(-2x + 2)` |

Increase `y` after either choice.

### Second part: move left through the shallow region

At the boundary, initialize the new midpoint test at `(x - 1, y + ½)`:

```text
decision = b²(x - 1)² + a²(y + ½)² - a²b²
```

| Decision | Choice | Update using old coordinates |
| --- | --- | --- |
| Negative | NW: increase `y` | `decision += b²(-2x + 3) + a²(2y + 2)` |
| Otherwise | W: keep `y` | `decision += b²(-2x + 3)` |

Decrease `x` after either choice. Stop once `x < 0`.

Each calculated point goes through `draw4way()` to complete the ellipse. Unlike a circle, a general ellipse does not have symmetry under swapping `x` and `y`, so we use four-way symmetry here.

## 10. Expanding and taking off

When squeezing reaches its limit, stops changing the rendered radii, or reaches zero speed, the program switches to expansion. It resets the deformation speed and reverses the squeeze acceleration. Now `b` grows from rest, while the same constraint makes `a` shrink.

```python
b += squeeze_velocity - 0.5 * SQUEEZE_ACCELERATION
squeeze_velocity -= SQUEEZE_ACCELERATION
b = min(b, float(RADIUS))
a = math.sqrt(AXIS_SUM_SQUARED - b * b)
YC = BOTTOM + b
```

Since `SQUEEZE_ACCELERATION = -1`, subtracting it gives an expansion acceleration of `+1`. During this phase, the variable named `squeeze_velocity` is reused as a positive expansion speed, so it increases `b` instead of decreasing it.

The shape stays on the floor using `YC = BOTTOM + b`. Once `b = RADIUS`, the constraint also gives `a = RADIUS`, so it is a circle again.

The center must rise through:

```text
h = TOP - BOTTOM - 2r
  = 269 - (-270) - 50
  = 489 pixels
```

To reach that height and stop at the top, use the constant-acceleration equation:

```text
v_final² = v_initial² - 2gh
0 = v_initial² - 2gh
upward speed = √(2gh) ≈ 69.93 pixels/frame
```

Since this program uses negative velocity for upward motion:

```python
fall_velocity = -math.sqrt(2 * GRAVITY * travel_height)
```

This is a deliberately controlled bounce: the program chooses the launch speed to reach the top every time, rather than simulating material elasticity or energy loss.

## 11. Rising and repeating

While rising, the same gravity equations apply. Velocity starts negative and increases toward zero, so upward motion slows down.

When the velocity reaches zero or the circle reaches the top border, the code places its center exactly at `TOP - RADIUS`, sets velocity to zero, and switches back to falling. Snapping to the top handles a frame that steps past the exact turning time.

There is no final stopped state, so the cycle repeats forever.

## 12. Timer, drawing, and double buffering

The two main jobs are separate:

- `update_animation()` changes position, velocity, axes, and phase.
- `display()` draws the current shape.

After updating, `glutPostRedisplay()` requests a new drawing. `glutTimerFunc()` schedules the next update. GLUT remains free to handle window events between updates.

`GLUT_DOUBLE` enables two buffers. The program draws a complete frame in the back buffer, then `glutSwapBuffers()` shows it. Clearing each new frame removes the previous position so the shape leaves no trail.

## 13. A short explanation to say to the teacher

“I start with a radius-25 circle at the top, with zero velocity. I draw it using Bresenham's algorithm and eight-way symmetry. Gravity increases its downward speed each frame. At floor contact, I switch to the midpoint ellipse algorithm. Since my roll is 32, I start the ellipse at `(a, 0)` and use four-way symmetry.

“Compression starts at the last falling speed and slows by one pixel/frame each frame. I calculate `a` from the corrected constraint `a² + b² = 2r²`, and keep the bottom on the floor with `YC = BOTTOM + b`. I limit the visible squeeze to `a = 2b`. At the limit, or if squeezing stops changing the pixel radii, I reset the compression speed and expand immediately. Once it becomes a circle, I launch it upward with speed `√(2gh)`, making it touch the top before falling again. A GLUT timer runs the animation, and double buffering displays each completed frame.”

## 14. Screenshots to show

The [screenshots folder](screenshots/) contains the initial position, falling circle, floor contact, maximum squeeze, expansion, rising circle, and top contact.
