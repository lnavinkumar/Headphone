"""
Adjustable Ear Loop — Connected Single-Piece STL
=================================================
C-ring (gear teeth, 10 mm wide) + Ear strap attached at ring top.
Both parts share the same origin and merge at the 90° connection point.

Coordinate layout (XY plane, top view):
  - C-ring centred at origin, gap at lower-right (~315°)
  - Strap arc centre below origin; strap outer edge touches ring at 90° (12 o'clock)
  - Strap sweeps 270° CCW, tip tapers at end
"""
import math, struct

# ── tiny helpers ─────────────────────────────────────────────────────────────
def cross3(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def norm3(v):
    m = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
    return (v[0]/m,v[1]/m,v[2]/m) if m > 1e-12 else (0.,0.,1.)

def fnorm(p1,p2,p3):
    e1 = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    e2 = (p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2])
    return norm3(cross3(e1,e2))

tris = []
def emit(p1,p2,p3): tris.append((fnorm(p1,p2,p3), p1, p2, p3))
def quad(p1,p2,p3,p4): emit(p1,p2,p3); emit(p1,p3,p4)

def stitch(secs):
    """Connect adjacent rect cross-sections [inner-bot, inner-top, outer-top, outer-bot]."""
    for i in range(len(secs)-1):
        a, b = secs[i], secs[i+1]
        quad(a[0],a[1],b[1],b[0])  # inner face
        quad(a[2],a[3],b[3],b[2])  # outer face
        quad(a[1],a[2],b[2],b[1])  # top  (+Z)
        quad(a[0],b[0],b[3],a[3])  # bottom (−Z)

def end_caps(secs):
    s = secs[0];  quad(s[0],s[3],s[2],s[1])   # start cap
    s = secs[-1]; quad(s[0],s[1],s[2],s[3])   # end cap

def rsec(cx, cy, rx, ry, half_t, half_w):
    """Rect cross-section: [inner-bot, inner-top, outer-top, outer-bot]."""
    ht, hw = half_t, half_w
    return [
        (cx-rx*ht, cy-ry*ht, -hw),
        (cx-rx*ht, cy-ry*ht,  hw),
        (cx+rx*ht, cy+ry*ht,  hw),
        (cx+rx*ht, cy+ry*ht, -hw),
    ]


# ═══════════════════════════════════════════════════════════════════
# PART 1 — ADJUSTABLE C-RING
#   Centre: origin (0, 0)
#   Gap: 40° gap centred at 315° (lower-right, ~4-5 o'clock)
#   Ring spans: 335° → 655° (= 295°) CCW — 320° of arc
#   Connection to strap: at 90° (12 o'clock), outer surface = (0, ROUT)
# ═══════════════════════════════════════════════════════════════════
R_IN_BASE = 11  # mm  inner radius (tooth valley)
R_OUT     = 19.5   # mm  outer radius
RING_W    = 10.0   # mm  ← USER SPECIFIED ring width
RING_S    = 335.0  # °   ring start (just past gap)
RING_E    = 655.0  # °   ring end   (= 295°, just before gap)
N_RING    = 84     # arc segments
N_TEETH   = 22     # inner gear teeth
TOOTH_H   =  1.3   # mm  tooth height

def ring_ri(ang_deg):
    t = (ang_deg - RING_S) / (RING_E - RING_S)   # 0..1
    bump = (1.0 + math.cos(t * N_TEETH * 2*math.pi)) / 2.0
    return R_IN_BASE + TOOTH_H * bump

ring_secs = []
for i in range(N_RING + 1):
    ang  = RING_S + i/N_RING * (RING_E - RING_S)
    a    = math.radians(ang)
    ri   = ring_ri(ang)
    hw   = RING_W / 2
    ring_secs.append([
        (ri*math.cos(a),    ri*math.sin(a),    -hw),
        (ri*math.cos(a),    ri*math.sin(a),     hw),
        (R_OUT*math.cos(a), R_OUT*math.sin(a),  hw),
        (R_OUT*math.cos(a), R_OUT*math.sin(a), -hw),
    ])

stitch(ring_secs)
end_caps(ring_secs)


# ═══════════════════════════════════════════════════════════════════
# PART 2 — EAR STRAP
#   Connects at ring top (90°) — strap outer edge flush with ring outer surface
#   Arc centre: (0, R_OUT − T/2 − R_STRAP) = (0, −17)  so outer edge at (0,18) ✓
#   Sweeps 270° CCW: 90° → 360°
#   Width blends from RING_W (10 mm) at join → W_STRAP (6.5 mm) after 20°
#   Tip tapers from 6.5 mm → 2 mm over last 35°
# ═══════════════════════════════════════════════════════════════════
R_STRAP   = 60.0   # mm  strap arc radius (flatter than original 34 mm)
T_STRAP   =  2.0   # mm  strap thickness (radial)
W_STRAP   =  6.5   # mm  strap width at full width
S_START   = 90.0   # °   start = ring top connection
S_END     = 233.0  # °   143° sweep → arc length ≈ 150 mm
N_STRAP   = 56     # arc segments
BLEND_DEG = 22.0   # °   width blend zone at connection
TAPER_DEG = 35.0   # °   taper zone at tip

# Arc centre: positioned so strap OUTER edge starts exactly on ring outer surface
#   Outer edge condition: ACY + R_STRAP + T_STRAP/2 = R_OUT  →  ACY = R_OUT - R_STRAP - T/2
ACX = 0.0
ACY = R_OUT - R_STRAP - T_STRAP/2          # = 18 - 34 - 1 = −17.0

def strap_w(ang):
    w = W_STRAP
    # Blend from ring width at connection
    if ang < S_START + BLEND_DEG:
        t = (ang - S_START) / BLEND_DEG
        w = RING_W + (W_STRAP - RING_W) * t    # 10 mm → 6.5 mm
    # Taper at tip
    t0 = S_END - TAPER_DEG
    if ang > t0:
        t = (ang - t0) / TAPER_DEG
        w = max(2.0, w*(1-t) + 2.0*t)
    return w

strap_secs = []
for i in range(N_STRAP + 1):
    t   = i / N_STRAP
    ang = S_START + t * (S_END - S_START)
    a   = math.radians(ang)
    cx  = ACX + R_STRAP * math.cos(a)
    cy  = ACY + R_STRAP * math.sin(a)
    rx  = math.cos(a)
    ry  = math.sin(a)
    strap_secs.append(rsec(cx, cy, rx, ry, T_STRAP/2, strap_w(ang)/2))

stitch(strap_secs)
end_caps(strap_secs)


# ═══════════════════════════════════════════════════════════════════
# WRITE STL
# ═══════════════════════════════════════════════════════════════════
def write_stl(path, triangles):
    hdr = (b'Adjustable Ear Loop Connected - Claude Code' + b'\x00'*80)[:80]
    with open(path, 'wb') as f:
        f.write(hdr)
        f.write(struct.pack('<I', len(triangles)))
        for n, p1, p2, p3 in triangles:
            f.write(struct.pack('<3f', *n))
            f.write(struct.pack('<3f', *p1))
            f.write(struct.pack('<3f', *p2))
            f.write(struct.pack('<3f', *p3))
            f.write(struct.pack('<H', 0))

out = '/Users/c395616/GitHub/Test/adjustable_ear_loop_connected.stl'
write_stl(out, tris)

arc_strap = math.radians(S_END - S_START) * R_STRAP
arc_ring  = math.radians(RING_E - RING_S) * ((R_IN_BASE + R_OUT) / 2)

print(f'STL saved  → {out}')
print(f'Triangles  : {len(tris)}')
print()
print('─── C-Ring ─────────────────────────────────')
print(f'  Width (specified) : {RING_W} mm')
print(f'  Inner dia          : {R_IN_BASE*2:.1f} mm  (tooth valley)')
print(f'  Outer dia          : {R_OUT*2:.1f} mm')
print(f'  Arc                : {RING_E-RING_S:.0f}°  ({360-(RING_E-RING_S):.0f}° gap at lower-right)')
print(f'  Teeth              : {N_TEETH}  ×  {TOOTH_H} mm')
print()
print('─── Ear Strap ──────────────────────────────')
print(f'  Arc radius         : {R_STRAP} mm')
print(f'  Sweep              : {S_END-S_START:.0f}° CCW from ring top')
print(f'  Arc length         : {arc_strap:.1f} mm')
print(f'  Width              : {RING_W} mm at join → {W_STRAP} mm → 2 mm tip')
print(f'  Thickness          : {T_STRAP} mm')
print(f'  Connection         : outer edge flush with ring at 90° (12 o\'clock)')
print()
print('Connection arc centre: (0, {:.1f}) mm — strap outer edge at (0, {:.1f}) ✓'.format(ACY, R_OUT))
print()
print('Slicing: TPU/PETG recommended. 0.15 mm layers, 30% infill.')
print('Both parts overlap at connection zone — slicer will union them correctly.')
