#!/usr/bin/env python3
"""Build Velocidrone .trk files for RaceGOW6 Track2 (BetaFPV / Sabj) from the layout
published by GeddyV's RaceGOW 6 track visualizer (https://racegow.geddyv.lt/track-visualizer/,
file /track-configurations/track-2.json, saved in source/).

Two files are written:
  * "RaceGOW6 Track2 fan build.trk"            Sports Hall (scene 21), desktop only
  * "RaceGOW6 Track2 fan build PolyWorld.trk"  Empty Polyworld (scene 42), works on desktop and,
                                               once uploaded to the online track database, on mobile

Visualizer units: 1 = one 24" PVC section, z up, gate position = centre, gate
rotation [0,0,90] = plane normal along x, [90,0,0] = horizontal (dive) gate.
Mapping to Velocidrone (verified against the official RaceGOW6 Track1 file):
  1 unit = 0.88 m,  Unity x = X0 + 88*y_vis,  Unity y = floor + 88*z_vis,
  Unity z = Z0 - 88*(x_vis - 0.5)   (the visualizer is mirrored relative to Unity).
Gate conventions copied from IGOW's official files: rotation (w,x,y,z)*1000, pivot at
the gate's base centre, DefaultNeonSquare at 44 % (0.88 m), DefaultSquare for invisible passes.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import vdcrypt

SRC = json.load(open(os.path.join(HERE, 'source', 'racegow6-track-2.visualizer.json')))
# Widen the last two air checkpoints to 3 sections, extending outward from the tower,
# so pilots taking a wide line round the left side / behind the flag still get the pass.
SRC['gates'][12].update({'position': [-2.5, 2, 1], 'width': 3})   # left side: x from -4 to -1
SRC['gates'][13].update({'position': [0, 3.5, 1], 'width': 3})    # behind tower: y from 2 to 5
S = 88  # cm per section

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

# ------------------------------------------------- gate directions from the flight path
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
def pass_dirs():
    """Gate i is crossed at the first matching crossing after gate i-1's crossing (lap order)."""
    cursor, dirs = 0, []
    for order in range(len(SRC['gates'])):
        for j in range(cursor, len(CROSS)):
            seg, t, gi, d = CROSS[j]
            if gi == order:
                cursor = j + 1; dirs.append((d, seg)); break
        else:
            raise RuntimeError(f'no crossing found for gate {order}')
    return dirs
DIRS = pass_dirs()

# ------------------------------------------------------------- scene configs
def pipe_cube(p1, p2, thick=2):
    """PVC tube as a thin DefaultCubeBarrier (54): native 2 m cube, pivot at base centre. Desktop."""
    (x1,y1,z1), (x2,y2,z2) = p1, p2
    L = round(math.dist(p1, p2)/2)
    if abs(y2-y1) > 1:   pos, sc = [x1, min(y1,y2), z1], [thick, L, thick]
    elif abs(x2-x1) > 1: pos, sc = [(x1+x2)/2, y1 - thick, z1], [L, thick, thick]
    else:                pos, sc = [x1, y1 - thick, (z1+z2)/2], [thick, thick, L]
    return {"prefab": 54, "trans": {"pos": [round(v) for v in pos], "rot": [1000,0,0,0], "scale": sc}}

def pipe_poly(p1, p2, thick=4):
    """PVC tube as PolyCylinder1 (863): native 1 m cylinder, pivot at its centre, PolyWorld set
    (used by IGOW's own Empty Polyworld tracks, so it is safe for mobile)."""
    (x1,y1,z1), (x2,y2,z2) = p1, p2
    L = round(math.dist(p1, p2)); c = [(x1+x2)/2, (y1+y2)/2, (z1+z2)/2]
    if abs(y2-y1) > 1:   rot = [1000,0,0,0]       # upright
    elif abs(x2-x1) > 1: rot = [707,0,0,707]      # 90 deg about z: length along x
    else:                rot = [707,707,0,0]      # 90 deg about x: length along z
    return {"prefab": 863, "trans": {"pos": [round(v) for v in c], "rot": rot, "scale": [thick, L, thick]}}

CONFIGS = [
    dict(name='RaceGOW6 Track2 fan build', scene=21, floor=7, X0=1450, Z0=0, pipe=pipe_cube,
         grid={"prefab": 90, "trans": {"pos": [1300, 7, 0], "rot": [-707,707,0,0], "scale": [40,21,40]}},
         preview=True),
    dict(name='RaceGOW6 Track2 fan build PolyWorld', scene=42, floor=-1, X0=0, Z0=0, pipe=pipe_poly,
         grid={"prefab": 696, "trans": {"pos": [-176, 0, 0], "rot": [0,0,1000,0], "scale": [15,20,8]}},
         preview=False),
]
VISIBLE = {0: 209, 1: 208, 3: 208, 6: 208, 8: 208}  # green start + blue entry faces; exits and air checkpoints invisible

def build(cfg):
    FLOOR, X0, Z0 = cfg['floor'], cfg['X0'], cfg['Z0']
    def U(p):      # visualizer [x,y,z] -> Unity cm
        x, y, z = p
        return (X0 + S*y, FLOOR + S*z, Z0 - S*(x - 0.5))
    def fly_u(d):  # visualizer direction -> Unity direction
        x, y, z = d
        return (y, z, -x)
    gates, barriers = [], []
    for order, g in enumerate(SRC['gates']):
        d_vis, seg = DIRS[order]
        fly = fly_u(d_vis); rot = pick_rot(fly); f, lat, ext = axes(rot)
        pct = lambda v: 44 if v <= 1 else 88 if v <= 2 else round(v*44)
        w_pct, h_pct = pct(g['width']), pct(g['height'])
        centre = U(g['position']); size_h = 2*h_pct
        pivot = tuple(round(centre[k] - 0.5*size_h*ext[k]) for k in range(3))
        prefab = VISIBLE.get(order, 88)
        gates.append({"prefab": prefab, "trans": {"pos": list(pivot), "rot": list(rot),
                      "scale": [14 if prefab != 88 else 3, w_pct, h_pct]}, "gate": order,
                      "start": order == 0, "finish": order == 0, "lap1only": False})
        if cfg['preview']:
            print(f"gate {order:2d} vis {g['position']} dir {d_vis} -> unity fly {fly} "
                  f"{'NEON' if prefab != 88 else 'inv '} {w_pct}x{h_pct}  (path seg {seg})")
    for p in SRC['pipes']:
        barriers.append(cfg['pipe'](U(p['start']), U(p['end'])))
    barriers.append(cfg['grid'])

    js = {"gates": gates, "barriers": barriers}
    plain = f"{cfg['scene']}\n{cfg['name']}\n{json.dumps(js, separators=(',',':'))}"
    trk = os.path.join(HERE, f"{cfg['name']}.trk")
    open(trk, 'w').write(vdcrypt.encrypt(plain))
    open(os.path.join(HERE, f"{cfg['name']}.json"), 'w').write(json.dumps(js, indent=1))
    assert vdcrypt.decrypt(open(trk).read()) == plain
    print(f"{cfg['name']}: scene {cfg['scene']}, {len(gates)} gates, {len(barriers)} barriers, round-trip OK")
    if cfg['preview']: preview(gates, barriers, U, FLOOR)

def preview(gates, barriers, U, FLOOR):
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
        pts = [v(U(p)) for p in PATH]; d.line(pts + [pts[0]], fill=(90,90,110), width=1)
    d.text((15,10), 'TOP VIEW (Unity x right, z up) - green start, blue neon gates, yellow invisible checkpoints; stub = fly direction; grey = flight path', fill=(200,200,200))
    d.text((15,330), 'SIDE VIEW (x right, height up)', fill=(200,200,200))
    im.save(os.path.join(HERE, 'preview.png')); print('preview saved')

if __name__ == '__main__':
    for cfg in CONFIGS: build(cfg)
