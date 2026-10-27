import cv2 
import numpy as np
import argparse
import potrace
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter 

def image_to_vector(image: np.ndarray):
  """Returns a list of curves making up the svg and the svg"""
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  bmp = potrace.Bitmap(gray)
  plist = bmp.trace()

  parts = []
  for curve in plist:
    start = curve.start_point
    parts.append(f"M {start.x:.2f},{start.y:.2f}")
    for seg in curve.segments:
        if seg.is_corner:
            parts.append(f"L {seg.c.x:.2f},{seg.c.y:.2f}")
            parts.append(f"L {seg.end_point.x:.2f},{seg.end_point.y:.2f}")
        else:
            parts.append(
                f"C {seg.c1.x:.2f},{seg.c1.y:.2f} "
                f"{seg.c2.x:.2f},{seg.c2.y:.2f} "
                f"{seg.end_point.x:.2f},{seg.end_point.y:.2f}"
            )
    parts.append("Z")
    w, h = gray.shape
  svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{h}" height="{w}" '
         f'viewBox="0 0 {h} {w}"><path d="{" ".join(parts)}" '
         f'fill="black" fill-rule="evenodd"/></svg>')
  open("output.svg", "w").write(svg)
  return plist, svg

def bezier(p0, p1, p2, p3, n=12):
    t = np.linspace(0, 1, n)[:, None]
    return ((1-t)**3 * p0 + 3*(1-t)**2*t * p1 +
            3*(1-t)*t**2 * p2 + t**3 * p3)

def to_polylines(plist):
    """Returns x,y points along the curves. The paths output is an array of "stroke" 
    arrays made up of many connected (x,y) points i.e.
    [array([[0,0],[1,0],[2,0]]), array([[0,1],[1,1],[2,1]])"""
    paths = []
    for curve in plist:
        cur = np.array([curve.start_point.x, curve.start_point.y])
        pts = [cur]
        for seg in curve.segments:
            end = np.array([seg.end_point.x, seg.end_point.y])
            if seg.is_corner:
                c = np.array([seg.c.x, seg.c.y])
                pts += [c, end]
            else:
                c1 = np.array([seg.c1.x, seg.c1.y])
                c2 = np.array([seg.c2.x, seg.c2.y])
                pts += list(bezier(cur, c1, c2, end)[1:])
            cur = end
        paths.append(np.array(pts))
    return paths  

def plotting(paths, image_shape, points_per_frame=5, fps=30, save=None):
    """Animate the pen drawing each stroke in order."""
    h, w = image_shape[:2]

    # Makes one big array; NaN row after each stroke breaks the line (pen up)
    nan_row = np.full((1, 2), np.nan)
    pts = np.vstack([np.vstack([p, nan_row]) for p in paths])
    total = len(pts)

    fig, ax = plt.subplots()
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_aspect("equal")
    ax.set_title("Plotting")

    (trace,) = ax.plot([], [], "k-", lw=1)
    (pen,) = ax.plot([], [], "ro", ms=6)

    def update(frame):
        n = min((frame + 1) * points_per_frame, total)
        trace.set_data(pts[:n, 0], pts[:n, 1])
        # Pen sits at the most recent real (non-NaN) point
        recent = pts[max(0, n - 3):n]
        recent = recent[~np.isnan(recent[:, 0])]
        if len(recent):
            pen.set_data([recent[-1, 0]], [recent[-1, 1]])
        return trace, pen

    n_frames = int(np.ceil(total / points_per_frame))
    anim = FuncAnimation(fig, update, frames=n_frames,
                         interval=1000 / fps, blit=True, repeat=False)

    if save:
        anim.save(save, writer=PillowWriter(fps=fps))
    else:
        plt.show()
    return anim

def main():
  parser = argparse.ArgumentParser(description="Image to SVG")
  parser.add_argument("image", help="Path to a JPG/PNG image")
  parser.add_argument("--step", type=int, default=5,
                      help="Points drawn per frame (higher = faster)")
  parser.add_argument("--save", help="Save animation as a GIF, e.g. plot.gif")
  args = parser.parse_args()

  image = cv2.imread(args.image)
  list, vector = image_to_vector(image)
  paths = to_polylines(list)
  print(f"{len(paths)} strokes, {sum(len(p) for p in paths)} points")
  plotting(paths, image.shape, points_per_frame=args.step, save=args.save)


if __name__ == "__main__":
  main()


    