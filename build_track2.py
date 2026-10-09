#!/usr/bin/env python3
"""Build a Velocidrone .trk for RaceGOW6 Track2 (BetaFPV / Sabj) from the layout
published by GeddyV's RaceGOW 6 track visualizer (https://racegow.geddyv.lt/track-visualizer/,
file /track-configurations/track-2.json, saved in source/).

Visualizer units: 1 = one 24" PVC section, z up, gate position = centre, gate
rotation [0,0,90] = plane normal along x, [90,0,0] = horizontal (dive) gate.
Mapping to Velocidrone (verified against the official RaceGOW6 Track1 file):
  1 unit = 0.88 m,  Unity x = X0 + 88*y_vis,  Unity y = floor + 88*z_vis,
  Unity z = Z0 - 88*(x_vis - 0.5)   (the visualizer is mirrored relative to Unity).
Gate conventions copied from IGOW's official files: Sports Hall (scene 21, floor
y=7 cm), rotation (w,x,y,z)*1000, pivot at the gate's base centre.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vdcrypt

SRC = json.load(open(os.path.join(HERE, 'source', 'racegow6-track-2.visualizer.json')))
S, FLOOR, X0, Z0 = 88, 7, 1450, 0

# ------------------------------------------------------------ quaternion maths
def qrot(q, v):
    x, y, z, w = q; vx, vy, vz = v
    tx = 2*(y*vz - z*vy); ty = 2*(z*vx - x*vz); tz = 2*(x*vy - y*vx)
    return (vx + w*tx + (y*tz - z*ty), vy + w*ty + (z*tx - x*tz), vz + w*tz + (x*ty - y*tx))
def axes(stored):
    w, x, y, z = [v/1000 for v in stored]; n = math.sqrt(w*w+x*x+y*y+z*z)
    q = (x/n, y/n, z/n, w/n)
    rx, ry, rz = qrot(q,(1,0,0)), qrot(q,(0,1,0)), qrot(q,(0,0,1))
    return tuple(-c for c in rx), ry, rz        # fly direction, lateral (width), extent (height)
def rnd(v): return tuple(round(c) for c in v)
CANDS = [(0,0,-707,-707), (-707,707,0,0), (-500,500,-500,-500), (500,-500,-500,-500),
         (500,500,500,500), (500,500,-500,-500)]
def pick_rot(fly):
    for c in CANDS:
        if rnd(axes(c)[0]) == tuple(fly): return c
    raise ValueError(fly)

# ------------------------------------------------------------------ mapping
def U(p):   # visualizer [x,y,z] -> Unity cm
    x, y, z = p
    return (X0 + S*y, FLOOR + S*z, Z0 - S*(x - 0.5))
def fly_u(d):  # visualizer direction -> Unity direction
    x, y, z = d
    return (y, z, -x)

# flight path gives the direction of every pass (gate i is crossed between path
# points; direction is the dominant axis of travel at that gate)
PATH = SRC['flightPath']
def crossings():
    """All plane crossings of the closed flight path, in travel order: (seg, t, gate_index, direction)."""
    out = []
    for i in range(len(PATH)):
        a, b = PATH[i], PATH[(i+1) % len(PATH)]
        for gi, g in enumerate(SRC['gates']):
            gp = g['position']; rot = g.get('rotation', [0,0,0])
            normal = (0,1,0) if rot == [0,0,0] else (1,0,0) if rot == [0,0,90] else (0,0,1)
            da = sum((a[k]-gp[k])*normal[k] for k in range(3)); db = sum((b[k]-gp[k])*normal[k] for k in range(3))
            if da == db or (da > 0) == (db > 0): continue
            t = da/(da-db); hit = [a[k] + t*(b[k]-a[k]) for k in range(3)]
            half = [g['width']/2 if k == (0 if normal[1] else 1 if normal[0] else 0) else g['height']/2 for k in range(3)]
            if all(normal[k] or abs(hit[k]-gp[k]) <= half[k] + 0.35 for k in range(3)):
                out.append((i, t, gi, tuple((1 if db > da else -1)*n for n in normal)))
    return sorted(out)
CROSS = crossings()
def pass_dir(order, gate):
    """Gate `order` is crossed at the first matching crossing after the previous gate's crossing."""
    start = pass_dir.cursor
    for j in range(start, len(CROSS)):
        seg, t, gi, d = CROSS[j]
        if gi == order:
            pass_dir.cursor = j + 1
            return d, 0.0, seg
    raise RuntimeError(f'no crossing found for gate {order} after crossing #{start}')
pass_dir.cursor = 0

# ---------------------------------------------------------- build the track
gates, barriers = [], []
VISIBLE = {0: 209, 1: 208, 3: 208, 6: 208, 8: 208}  # green start + blue entry faces; exits and air checkpoints invisible
for order, g in enumerate(SRC['gates']):
    d_vis, dist, seg = pass_dir(order, g)
    fly = fly_u(d_vis); rot = pick_rot(fly); f, lat, ext = axes(rot)
    w_pct = 44 if g['width'] <= 1 else 88
    h_pct = 44 if g['height'] <= 1 else 88
    centre = U(g['position']); size_h = 2*h_pct
    pivot = tuple(round(centre[k] - 0.5*size_h*ext[k]) for k in range(3))
    prefab = VISIBLE.get(order, 88)
    gates.append({"prefab": prefab, "trans": {"pos": list(pivot), "rot": list(rot),
                  "scale": [14 if prefab != 88 else 3, w_pct, h_pct]}, "gate": order,
                  "start": order == 0, "finish": order == 0, "lap1only": False})
    print(f"gate {order:2d} vis {g['position']} dir {d_vis} -> unity fly {fly} rot {rot} "
          f"{'NEON' if prefab != 88 else 'inv '} {w_pct}x{h_pct}  (path seg {seg}, miss {dist:.2f})")

THICK = 2
for p in SRC['pipes']:
    (x1,y1,z1), (x2,y2,z2) = U(p['start']), U(p['end'])
    L = round(math.dist((x1,y1,z1),(x2,y2,z2))/2)
    if abs(y2-y1) > 1:   pos, sc = [x1, min(y1,y2), z1], [THICK, L, THICK]
    elif abs(x2-x1) > 1: pos, sc = [round((x1+x2)/2), y1 - THICK, z1], [L, THICK, THICK]
    else:                pos, sc = [x1, y1 - THICK, round((z1+z2)/2)], [THICK, THICK, L]
    barriers.append({"prefab": 54, "trans": {"pos": [round(v) for v in pos], "rot": [1000,0,0,0], "scale": sc}})
barriers.append({"prefab": 90, "trans": {"pos": [X0-150, FLOOR, Z0], "rot": [-707,707,0,0], "scale": [40,21,40]}})

NAME = 'RaceGOW6 Track2 fan build'
js = {"gates": gates, "barriers": barriers}
plain = f"21\n{NAME}\n{json.dumps(js, separators=(',',':'))}"
open(os.path.join(HERE, f'{NAME}.trk'), 'w').write(vdcrypt.encrypt(plain))
open(os.path.join(HERE, f'{NAME}.json'), 'w').write(json.dumps(js, indent=1))
assert vdcrypt.decrypt(open(os.path.join(HERE, f'{NAME}.trk')).read()) == plain
print('gates', len(gates), 'barriers', len(barriers), 'round-trip OK')

# ------------------------------------------------------------------ preview
from PIL import Image, ImageDraw
W, H = 1100, 640; im = Image.new('RGB', (W, H), (18,18,24)); d = ImageDraw.Draw(im)
def top(p):  return (150 + (p[0]-1300)*2.0, 330 - (p[2]+150)*1.2 + 60)
def side(p): return (150 + (p[0]-1300)*2.0, 620 - (p[1]-FLOOR)*0.9)
for v in (top, side):
    for b in barriers:
        if b['prefab'] != 54: continue
        p = b['trans']['pos']; sc = b['trans']['scale']
        p1 = (p[0]-sc[0]*(sc[0]>5), p[1], p[2]-sc[2]*(sc[2]>5)); p2 = (p[0]+sc[0]*(sc[0]>5), p[1]+2*sc[1]*(sc[1]>5), p[2]+sc[2]*(sc[2]>5))
        d.line([v(p1), v(p2)], fill=(225,225,225), width=3)
    for g in gates:
        f, lat, ext = axes(tuple(g['trans']['rot'])); sw, sh = 2*g['trans']['scale'][1], 2*g['trans']['scale'][2]; p = g['trans']['pos']
        c = [p[k] + 0.5*sh*ext[k] for k in range(3)]
        col = {209:(80,230,80),208:(80,140,255),210:(220,80,255),88:(255,200,60)}[g['prefab']]
        d.line([v([c[k]+0.5*sw*lat[k] for k in range(3)]), v([c[k]-0.5*sw*lat[k] for k in range(3)])], fill=col, width=2)
        d.line([v([c[k]+0.5*sh*ext[k] for k in range(3)]), v([c[k]-0.5*sh*ext[k] for k in range(3)])], fill=col, width=2)
        d.line([v(c), v([c[k]+35*f[k] for k in range(3)])], fill=col, width=4)
        d.text((v(c)[0]+5, v(c)[1]-13), str(g['gate']), fill=col)
    # flight path
    pts = [v(U(p)) for p in PATH] ; d.line(pts + [pts[0]], fill=(90,90,110), width=1)
d.text((15,10), 'TOP VIEW (Unity x right, z up) - green start, blue/purple neon gates, yellow invisible checkpoints; stub = fly direction; grey = flight path', fill=(200,200,200))
d.text((15,330), 'SIDE VIEW (x right, height up)', fill=(200,200,200))
im.save(os.path.join(HERE, 'preview.png')); print('preview saved')
