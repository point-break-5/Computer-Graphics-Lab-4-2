# Deriving the decision variable in `draw_circle_0`

This derivation matches your code: start at `(x, y) = (r, 0)`, increase `y` each step, and sometimes decrease `x`. Assume `r` is a nonnegative integer.

## 1. Circle equation and candidate pixels

Work with offsets from the center. The circle equation is

$$
F(x,y) = x^2 + y^2 - r^2.
$$

- `F < 0`: inside the circle.
- `F = 0`: on the circle.
- `F > 0`: outside the circle.

Starting from the rightmost point `(r, 0)`, move upward through the 0°–45° octant. At a current pixel `(x, y)`, the next pixel is one of these:

| Choice | Next pixel | Coordinate changes |
| --- | --- | --- |
| North (N) | `(x, y + 1)` | Increase `y` only |
| Northwest (NW) | `(x - 1, y + 1)` | Decrease `x`, increase `y` |

Their midpoint is

$$
M = \left(x - \frac12,\; y + 1\right).
$$

If `F(M) < 0`, the midpoint is inside the circle. The ideal arc is to its right, so choose N. Otherwise, choose NW.

## 2. An integer decision variable

To obtain the exact integer variable used in your code, define

$$
d = F(x,y+1) + F(x-1,y+1).
$$

Expanding gives

$$
\begin{aligned}
d &= x^2 + (y+1)^2 - r^2
   + (x-1)^2 + (y+1)^2 - r^2 \\
  &= 2x^2 - 2x + 1 + 2(y+1)^2 - 2r^2.
\end{aligned}
$$

This has the same sign as the midpoint test because

$$
d = 2F\left(x-\frac12,y+1\right) + \frac12.
$$

For integer `x`, `y`, and `r`, `F(M)` is always an integer plus `1/4`. Its possible values nearest zero are `-3/4` and `1/4`, which become `d = -1` and `d = 1`. Therefore, this transformation preserves the sign exactly. Also, `d` is always odd, so it never equals zero.

The decision rule is consequently:

```python
if decision < 0:
    # Choose N: keep x, increase y.
else:
    # Choose NW: decrease x, increase y.
```

## 3. Initial decision: `3 - 2 * radius`

Substitute the starting pixel `x = r`, `y = 0`:

$$
\begin{aligned}
d_0 &= 2r^2 - 2r + 1 + 2(0+1)^2 - 2r^2 \\
    &= 3 - 2r.
\end{aligned}
$$

Hence:

```python
decision = 3 - 2 * radius
```

## 4. Choosing N: increment by `4 * y + 6`

Let `d(x,y)` denote the expanded expression above. Choosing N changes the current pixel from `(x,y)` to `(x,y+1)`. The next decision is therefore `d(x,y+1)`.

Only the term involving `y` changes:

$$
\begin{aligned}
d_{\text{next}} - d
&= 2(y+2)^2 - 2(y+1)^2 \\
&= 2\left[(y^2+4y+4)-(y^2+2y+1)\right] \\
&= 4y + 6.
\end{aligned}
$$

Thus:

```python
decision += 4 * y + 6
```

Then increase `y` by 1.

## 5. Choosing NW: increment by `4 * (y - x) + 10`

Choosing NW changes `(x,y)` to `(x-1,y+1)`. Both coordinates affect the next decision:

$$
\begin{aligned}
d_{\text{next}} - d
&= \left[2(x-1)^2 - 2(x-1) - (2x^2-2x)\right] \\
&\quad + \left[2(y+2)^2 - 2(y+1)^2\right] \\
&= (-4x+4) + (4y+6) \\
&= 4(y-x) + 10.
\end{aligned}
$$

Thus:

```python
decision += 4 * (y - x) + 10
x -= 1
```

Then increase `y` by 1.

Both update formulas use the **old** `x` and `y`. This is why your code updates `decision` before changing either coordinate.

## 6. Why the loop stops at `y <= x`

The first octant ends at the diagonal `y = x`, corresponding to 45°. Once `y > x`, the points lie in the next octant and are already covered by eight-way symmetry.

`draw8way(x, y, xc, yc)` reflects the offsets `(x,y)` and adds the center `(xc,yc)` to each reflected point. Moving the center changes where the circle is drawn, but does not affect the decision calculations.

## 7. Your complete algorithm

```python
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
```

For `r = 5`, a short trace is:

| Current `(x, y)` | Decision before update | Choice | Next `(x, y)` | Next decision |
| --- | --- | --- | --- | --- |
| `(5, 0)` | `-7` | N | `(5, 1)` | `-1` |
| `(5, 1)` | `-1` | N | `(5, 2)` | `9` |
| `(5, 2)` | `9` | NW | `(4, 3)` | `7` |
| `(4, 3)` | `7` | NW | `(3, 4)` | `13` |

The loop plots `(4,3)` before making the last update, then stops because the next point has `y > x`.
