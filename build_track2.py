#!/usr/bin/env python3
"""Build an unofficial Velocidrone .trk for RaceGOW6 Track2 (BetaFPV / Sabj).

Conventions copied from IGOW's official RaceGOW tracks (decrypted from the
public catalogue): Sports Hall scene 21, floor at y=7 cm, gate pivots at the
base centre of the gate, rotation quaternions stored (w,x,y,z)*1000.
"""
import json, sys, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import vdcrypt

# ---------------------------------------------------------------- quaternions
def qrot(q, v):
    """Rotate v by q=(x,y,z,w) (Hamilton, v' = q v q*)."""
    x, y, z, w = q; vx, vy, vz = v
    tx = 2*(y*vz - z*vy); ty = 2*(z*vx - x*vz); tz = 2*(x*vy - y*vx)
    return (vx + w*tx + (y*tz - z*ty), vy + w*ty + (z*tx - x*tz), vz + w*tz + (x*ty - y*tx))
def stored_to_q(r):  # stored (w,x,y,z)*1000 -> (x,y,z,w)
    w, x, y, z = [v/1000 for v in r]; n = math.sqrt(w*w+x*x+y*y+z*z)
    return (x/n, y/n, z/n, w/n)
def axes(stored):
    q = stored_to_q(stored)
    rx, ry, rz = qrot(q,(1,0,0)), qrot(q,(0,1,0)), qrot(q,(0,0,1))
    fly = tuple(-c for c in rx)       # calibrated: [0,0,-707,-707] is "fly +x"
    return fly, ry, rz                # rz = direction in which the square extends from its pivot
def rnd(v): return tuple(round(c) for c in v)

# candidate rotations seen in official IGOW tracks
CANDS = [(0,0,-707,-707), (-707,707,0,0), (-500,500,-500,-500), (500,-500,-500,-500),
         (500,500,500,500), (500,500,-500,-500), (-500,500,500,-500), (707,0,0,707),
         (0,707,707,0), (0,707,-707,0), (707,707,0,0), (0,0,707,-707)]
print('rotation table (fly dir, square extends along):')
for c in CANDS:
    f, ry, rz = axes(c); print(' ', c, 'fly', rnd(f), 'extent', rnd(rz), 'lateral', rnd(ry))

# sanity check against RaceGOW Track7 (Sports Hall) top-dive pair
for pos, rot, sc in [((1596,218,-71),(500,500,500,500),54), ((1705,219,-72),(500,500,-500,-500),55)]:
    f, ry, rz = axes(rot); size = 2*sc
    centre = tuple(pos[i] + 0.5*size*rz[i] for i in range(3))
    print('  Track7 check: pivot', pos, 'fly', rnd(f), '-> square centre', rnd(centre))

def pick_rot(fly):
    for c in CANDS:
        f, _, _ = axes(c)
        if rnd(f) == tuple(fly): return c
    raise ValueError(fly)

# ------------------------------------------------------------------- layout
S = 88            # cm per 24" PVC section (same scale as official RaceGOW6 Track1: 0.88 m gates)
FLOOR = 7         # Sports Hall floor height (cm), from official Sports Hall tracks
X0, Z0 = 1450, 0  # start gate position in the hall
def U(X, Y, Z):
    """Design units (X right, Y up, Z toward the build-video camera) -> Unity cm."""
    return (round(X0 + (2 - Z)*S), round(FLOOR + Y*S), round(Z0 + (X - 1.5)*S))

gates, barriers = [], []
def gate(prefab, centre, fly, size_pct, order, start=False, finish=False):
    rot = pick_rot(fly); f, ry, rz = axes(rot); size = 2*size_pct
    pivot = tuple(round(centre[i] - 0.5*size*rz[i]) for i in range(3))
    thick = 14 if prefab != 88 else 3
    gates.append({"prefab": prefab, "trans": {"pos": list(pivot), "rot": list(rot),
                  "scale": [thick, size_pct, size_pct]}, "gate": order,
                  "start": start, "finish": finish, "lap1only": False})
def bar(p1, p2, thick=2):
    """PVC tube as a thin DefaultCubeBarrier (native 2 m cube, pivot at base centre)."""
    (x1,y1,z1), (x2,y2,z2) = p1, p2
    L = math.dist(p1, p2); sc = round(L/2)
    if abs(y2-y1) > 1:            # vertical
        pos = [x1, min(y1,y2), z1]; scale = [thick, sc, thick]
    elif abs(x2-x1) > 1:          # along x
        pos = [round((x1+x2)/2), y1 - thick, z1]; scale = [sc, thick, thick]
    else:                          # along z
        pos = [x1, y1 - thick, round((z1+z2)/2)]; scale = [thick, thick, sc]
    barriers.append({"prefab": 54, "trans": {"pos": pos, "rot": [1000,0,0,0], "scale": scale}})

# --- PVC tower: lower cube (X,Z in [0,1], Y 0..1), upper cube (Y 1..2), flag (Y 2..3 at corner X=1,Z=1)
corners = [(0,0),(1,0),(0,1),(1,1)]
for (X,Z) in corners:
    bar(U(X,0,Z), U(X,1,Z))          # lower uprights
    bar(U(X,1,Z), U(X,2,Z))          # upper uprights
# mid-level square (one side open: 7 sections in the lower cube)
bar(U(0,1,1), U(1,1,1))  # front
bar(U(0,1,0), U(1,1,0))  # back
bar(U(0,1,0), U(0,1,1))  # left side
# top square
bar(U(0,2,1), U(1,2,1)); bar(U(0,2,0), U(1,2,0)); bar(U(0,2,0), U(0,2,1)); bar(U(1,2,0), U(1,2,1))
# flag pole
bar(U(1,2,1), U(1,3,1), thick=2)
# --- start/finish gate (X 1..2 at Z=2) + spacer on the floor from the tower's front-right foot
bar(U(1,0,2), U(1,1,2)); bar(U(2,0,2), U(2,1,2)); bar(U(1,1,2), U(2,1,2))
bar(U(1,0,1), U(1,0,2))

# --- race gates (lap order). Sizes: 44% = 0.88 m like official RaceGOW6 Track1
G, I = 44, 44
gate(209, U(1.5,0.5,2),  (1,0,0),  G, 0, start=True, finish=True)  # start/finish (green), fly +x
gate(208, U(1.0,0.5,0.5),(0,0,-1), G, 1)                           # lower cube right face (blue), fly -z
gate(88,  U(0.0,0.5,0.5),(0,0,-1), I, 2)                           # lower cube left face exit (invisible)
gate(210, U(0.0,1.5,0.5),(0,0,1),  G, 3)                           # upper cube left face (purple), fly +z
gate(88,  U(0.5,2.0,0.5),(0,1,0),  I, 4)                           # top square, climb out (invisible, horizontal)
gate(88,  U(1.0,2.5,1.5),(-1,0,0), 60, 5)                          # round the flag: checkpoint just outside the flag pole (invisible)
# start grid 1.5 m behind the start gate
barriers.append({"prefab": 90, "trans": {"pos": [X0-150, FLOOR, Z0], "rot": [-707,707,0,0], "scale": [40,21,40]}})

NAME = 'RaceGOW6 Track2 fan build'
SCENE = 21
js = {"gates": gates, "barriers": barriers}
plain = f"{SCENE}\n{NAME}\n{json.dumps(js, separators=(',',':'))}"
out = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
open(f'{out}/{NAME}.trk','w').write(vdcrypt.encrypt(plain))
open(f'{out}/{NAME}.json','w').write(json.dumps(js, indent=1))
print('gates', len(gates), 'barriers', len(barriers))
for g in gates: print(' ', json.dumps(g))
# round-trip check
back = vdcrypt.decrypt(open(f'{out}/{NAME}.trk').read())
assert back == plain, 'round trip failed'
print('round-trip OK, trk bytes', len(open(f'{out}/{NAME}.trk').read()))

# --------------------------------------------------------------- preview png
from PIL import Image, ImageDraw
W, H = 1000, 560; im = Image.new('RGB', (W, H), (18,18,24)); d = ImageDraw.Draw(im)
def top(p):  return (120 + (p[0]-1250)*2.2, 420 - (p[2]+200)*1.4*1.0)   # top view: x right, z up
def side(p): return (120 + (p[0]-1250)*2.2, 540 - (p[1]-FLOOR)*0.9)        # side view: x right, y up (z ignored)
for v in (top, side):
    for b in barriers:
        if b['prefab'] != 54: continue
        p = b['trans']['pos']; sc = b['trans']['scale']
        ext = [sc[0]*2/2, sc[1]*2, sc[2]*2/2]
        p1 = (p[0]-ext[0]*(sc[0]>5), p[1], p[2]-ext[2]*(sc[2]>5)); p2 = (p[0]+ext[0]*(sc[0]>5), p[1]+ext[1]*(sc[1]>5), p[2]+ext[2]*(sc[2]>5))
        d.line([v(p1), v(p2)], fill=(230,230,230), width=3)
    for g in gates:
        rot = tuple(g['trans']['rot']); f, ry, rz = axes(rot); size = 2*g['trans']['scale'][1]; p = g['trans']['pos']
        c = [p[i] + 0.5*size*rz[i] for i in range(3)]
        col = {209:(80,230,80),208:(80,140,255),210:(220,80,255),88:(255,200,60)}[g['prefab']]
        a = [c[i] + 0.5*size*(ry[i]) for i in range(3)]; b2 = [c[i] - 0.5*size*(ry[i]) for i in range(3)]
        a2 = [c[i] + 0.5*size*(rz[i]) for i in range(3)]; b3 = [c[i] - 0.5*size*(rz[i]) for i in range(3)]
        d.line([v(a), v(b2)], fill=col, width=2); d.line([v(a2), v(b3)], fill=col, width=2)
        e = [c[i] + 40*f[i] for i in range(3)]; d.line([v(c), v(e)], fill=col, width=4)
        d.text((v(c)[0]+6, v(c)[1]-14), str(g['gate']), fill=col)
d.text((20,10), 'TOP VIEW (x right, z up)  gates: 0 start(green) 1 blue 2 inv 3 purple 4 inv top 5 inv flag; thick stub = fly direction', fill=(200,200,200))
d.text((20,330), 'SIDE VIEW (x right, y up)', fill=(200,200,200))
im.save(f'{out}/preview.png'); print('preview saved')
