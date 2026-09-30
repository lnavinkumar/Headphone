"""
Motorola HX550 Ear Hook Overlay Generator
Creates a curved tube sleeve that slides over the broken ear hook for repair.
Dimensions estimated from photos; adjust inner_r if needed for your hook diameter.
"""
import math
import struct

# ── Geometry helpers ──────────────────────────────────────────────────────────

def cross3(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def normalize3(v):
    m = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    return (v[0]/m, v[1]/m, v[2]/m) if m > 1e-12 else (0.0, 0.0, 1.0)

def vadd(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def vscale(v, s): return (v[0]*s, v[1]*s, v[2]*s)

def face_normal(p1, p2, p3):
    e1 = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    e2 = (p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2])
    return normalize3(cross3(e1, e2))

# ── Core mesh builder ─────────────────────────────────────────────────────────

def build_hollow_arc_tube(arc_r, start_deg, end_deg, outer_r, inner_r,
                           n_arc=28, n_ring=16):
    """
    Hollow tube swept along a circular arc in the XY-plane.
    arc_r     : radius of the arc centerline (mm)
    start_deg : start angle of arc
    end_deg   : end angle of arc
    outer_r   : outer radius of tube cross-section
    inner_r   : inner radius of tube cross-section (bore)
    """
    tris = []

    def frame(t):
        """Return (center, radial, binormal) at normalised param t in [0,1]."""
        ang = math.radians(start_deg + t * (end_deg - start_deg))
        c = (arc_r * math.cos(ang), arc_r * math.sin(ang), 0.0)
        rad = (math.cos(ang), math.sin(ang), 0.0)   # outward radial
        bi  = (0.0, 0.0, 1.0)                        # binormal = Z
        return c, rad, bi

    def ring(t, r):
        c, rad, bi = frame(t)
        pts = []
        for k in range(n_ring):
            phi = 2*math.pi * k / n_ring
            p = vadd(c, vadd(vscale(rad, r*math.cos(phi)),
                             vscale(bi,  r*math.sin(phi))))
            pts.append(p)
        return pts

    def emit(p1, p2, p3):
        tris.append((face_normal(p1,p2,p3), p1, p2, p3))

    def quad(p1, p2, p3, p4):   # ccw quad → two tris
        emit(p1, p2, p3)
        emit(p1, p3, p4)

    # Pre-build all rings
    ro = [ring(i/n_arc, outer_r) for i in range(n_arc+1)]
    ri = [ring(i/n_arc, inner_r) for i in range(n_arc+1)]

    # Outer wall  (normals face outward → ccw when seen from outside)
    for i in range(n_arc):
        for j in range(n_ring):
            j1 = (j+1) % n_ring
            quad(ro[i][j], ro[i][j1], ro[i+1][j1], ro[i+1][j])

    # Inner wall  (normals face inward → reversed winding)
    for i in range(n_arc):
        for j in range(n_ring):
            j1 = (j+1) % n_ring
            quad(ri[i][j], ri[i+1][j], ri[i+1][j1], ri[i][j1])

    # Start end-cap  (normal faces backward along arc)
    for j in range(n_ring):
        j1 = (j+1) % n_ring
        quad(ro[0][j1], ro[0][j], ri[0][j], ri[0][j1])

    # End end-cap  (normal faces forward along arc)
    for j in range(n_ring):
        j1 = (j+1) % n_ring
        quad(ro[-1][j], ro[-1][j1], ri[-1][j1], ri[-1][j])

    return tris


def write_stl(path, tris, header=b''):
    hdr = (header + b'\x00'*80)[:80]
    with open(path, 'wb') as f:
        f.write(hdr)
        f.write(struct.pack('<I', len(tris)))
        for n, p1, p2, p3 in tris:
            f.write(struct.pack('<3f', *n))
            f.write(struct.pack('<3f', *p1))
            f.write(struct.pack('<3f', *p2))
            f.write(struct.pack('<3f', *p3))
            f.write(struct.pack('<H', 0))


# ── Dimensions ────────────────────────────────────────────────────────────────
#
#  Motorola HX550 ear hook estimates (from photo analysis):
#    Original hook tube outer diameter ≈ 3.0 mm
#    Overlay inner diameter = 4.2 mm  (2.1 mm radius) — 0.6 mm clearance each side
#    Overlay outer diameter = 7.2 mm  (3.6 mm radius) — 1.5 mm wall thickness
#    Arc centerline radius  ≈ 18 mm
#    Arc span               ≈ 105°  (roughly a 3/4 C-hook shape)
#
#  If the sleeve is too tight/loose, scale inner_r up/down by 0.2 mm increments.

ARC_RADIUS   = 18.0   # mm  – centerline arc radius
START_DEG    =  0.0   # degrees
END_DEG      = 105.0  # degrees
OUTER_R      =  3.6   # mm  – outer tube radius  (7.2 mm OD)
INNER_R      =  2.1   # mm  – inner bore radius  (4.2 mm ID)

tris = build_hollow_arc_tube(
    ARC_RADIUS, START_DEG, END_DEG,
    OUTER_R, INNER_R,
    n_arc=32, n_ring=20
)

stl_path = '/Users/c395616/Downloads/motorola_ear_hook_overlay.stl'
write_stl(stl_path, tris, b'Motorola HX550 ear hook overlay - Claude')
print(f'STL saved → {stl_path}')
print(f'Triangles : {len(tris)}')

arc_len = math.radians(END_DEG - START_DEG) * ARC_RADIUS
print(f'\nDimensions summary:')
print(f'  Arc length (centreline) : {arc_len:.1f} mm')
print(f'  Inner diameter (bore)   : {INNER_R*2:.1f} mm')
print(f'  Outer diameter          : {OUTER_R*2:.1f} mm')
print(f'  Wall thickness          : {OUTER_R-INNER_R:.1f} mm')


# ── Reference JPEG ────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), facecolor='#1a1a2e')
    fig.suptitle('Motorola HX550 — Ear Hook Overlay (3D Print)',
                 color='white', fontsize=14, fontweight='bold', y=0.97)

    # ── Left panel: Top view of curved sleeve ──────────────────────────────
    ax = axes[0]
    ax.set_facecolor('#0f0f23')
    ax.set_aspect('equal')
    ax.set_title('Top View (XY Plane)', color='#aaaaff', fontsize=11)

    theta = np.linspace(np.radians(START_DEG), np.radians(END_DEG), 200)

    def arc_xy(r, angles):
        return r * np.cos(angles), r * np.sin(angles)

    # Outer boundary
    ox, oy = arc_xy(ARC_RADIUS + OUTER_R, theta)
    # Inner boundary (outer face of inner bore)
    ix, iy = arc_xy(ARC_RADIUS - OUTER_R, theta)
    # Arc of bore inner surface
    bx_out, by_out = arc_xy(ARC_RADIUS + INNER_R, theta)
    bx_in,  by_in  = arc_xy(ARC_RADIUS - INNER_R, theta)

    # Fill sleeve body
    xs = np.concatenate([ox, ix[::-1]])
    ys = np.concatenate([oy, iy[::-1]])
    ax.fill(xs, ys, color='#4466cc', alpha=0.7, zorder=2)

    # Fill bore (hollow region)
    xb = np.concatenate([bx_out, bx_in[::-1]])
    yb = np.concatenate([by_out, by_in[::-1]])
    ax.fill(xb, yb, color='#0f0f23', alpha=1.0, zorder=3)

    # Edge lines
    for xv, yv in [(ox, oy), (ix, iy), (bx_out, by_out), (bx_in, by_in)]:
        ax.plot(xv, yv, color='#88aaff', lw=1.2, zorder=4)

    # End-cap lines
    for angle_deg in [START_DEG, END_DEG]:
        ang = np.radians(angle_deg)
        for r1, r2 in [(ARC_RADIUS+INNER_R, ARC_RADIUS+OUTER_R),
                       (ARC_RADIUS-OUTER_R, ARC_RADIUS-INNER_R)]:
            ax.plot([r1*np.cos(ang), r2*np.cos(ang)],
                    [r1*np.sin(ang), r2*np.sin(ang)],
                    color='#88aaff', lw=1.2, zorder=4)

    # Centreline arc (dashed)
    cx, cy = arc_xy(ARC_RADIUS, theta)
    ax.plot(cx, cy, '--', color='#ffcc44', lw=0.8, alpha=0.6, zorder=5)

    # Arc radius dimension
    mid_ang = np.radians((START_DEG + END_DEG) / 2)
    ax.annotate('', xy=(ARC_RADIUS*np.cos(mid_ang), ARC_RADIUS*np.sin(mid_ang)),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle='<->', color='#ffcc44', lw=1.2))
    ax.text(ARC_RADIUS/2*np.cos(mid_ang) - 1, ARC_RADIUS/2*np.sin(mid_ang) + 1,
            f'R={ARC_RADIUS:.0f}mm', color='#ffcc44', fontsize=9, ha='center')

    # Arc angle annotation
    ax.annotate(f'{END_DEG-START_DEG:.0f}°', xy=(5, 5),
                color='#ffaa88', fontsize=10)

    ax.set_xlim(-8, 26)
    ax.set_ylim(-5, 30)
    ax.tick_params(colors='#888888', labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor('#444466')
    ax.set_xlabel('mm', color='#888888', fontsize=8)
    ax.set_ylabel('mm', color='#888888', fontsize=8)

    # ── Right panel: Cross-section ─────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor('#0f0f23')
    ax2.set_aspect('equal')
    ax2.set_title('Cross-Section (at mid-arc)', color='#aaaaff', fontsize=11)

    phi = np.linspace(0, 2*np.pi, 300)
    ox2 = OUTER_R * np.cos(phi)
    oy2 = OUTER_R * np.sin(phi)
    ix2 = INNER_R * np.cos(phi)
    iy2 = INNER_R * np.sin(phi)

    ax2.fill(ox2, oy2, color='#4466cc', alpha=0.8)
    ax2.fill(ix2, iy2, color='#0f0f23', alpha=1.0)
    ax2.plot(ox2, oy2, color='#88aaff', lw=1.5)
    ax2.plot(ix2, iy2, color='#88aaff', lw=1.5)

    # Original hook (dashed) inside the bore
    orig_r = 1.5   # ~3mm original OD
    ox3 = orig_r * np.cos(phi)
    oy3 = orig_r * np.sin(phi)
    ax2.plot(ox3, oy3, '--', color='#88ffaa', lw=1.2, label='Original hook')

    # Dimension arrows
    def dim_arrow(ax, x0, y0, x1, y1, label, lc='#ffcc44', offset=(0,0.3)):
        ax.annotate('', xy=(x1,y1), xytext=(x0,y0),
                    arrowprops=dict(arrowstyle='<->', color=lc, lw=1.2))
        mx, my = (x0+x1)/2 + offset[0], (y0+y1)/2 + offset[1]
        ax.text(mx, my, label, color=lc, fontsize=9, ha='center')

    dim_arrow(ax2, 0, 0, OUTER_R, 0, f'OD {OUTER_R*2:.1f}mm',
              offset=(OUTER_R/2, 0.4))
    dim_arrow(ax2, 0, 0, INNER_R, 0, f'ID {INNER_R*2:.1f}mm',
              lc='#ff8888', offset=(INNER_R/2, -0.6))
    dim_arrow(ax2, INNER_R, 0, OUTER_R, 0, f'Wall\n{OUTER_R-INNER_R:.1f}mm',
              lc='#ffaa44', offset=((INNER_R+OUTER_R)/2, 0.4))

    ax2.legend(loc='lower right', fontsize=8,
               facecolor='#222244', edgecolor='#444466',
               labelcolor='#88ffaa')

    ax2.set_xlim(-5, 6)
    ax2.set_ylim(-5, 5)
    ax2.tick_params(colors='#888888', labelsize=8)
    for spine in ax2.spines.values():
        spine.set_edgecolor('#444466')
    ax2.set_xlabel('mm', color='#888888', fontsize=8)
    ax2.set_ylabel('mm', color='#888888', fontsize=8)

    # ── Notes box ─────────────────────────────────────────────────────────
    notes = (
        'Print notes:  Recommended: TPU/PETG flexible filament  |  '
        'Layer height 0.15 mm  |  30% infill  |  2 perimeters\n'
        'If bore is tight: scale inner_r up by 0.2 mm increments and re-run script.'
    )
    fig.text(0.5, 0.02, notes, ha='center', va='bottom',
             color='#aaaaaa', fontsize=8,
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#222244',
                       edgecolor='#444466', alpha=0.8))

    plt.tight_layout(rect=[0, 0.07, 1, 0.95])
    jpeg_path = '/Users/c395616/Downloads/motorola_ear_hook_reference.jpg'
    plt.savefig(jpeg_path, dpi=150, format='jpeg',
                bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f'JPEG saved → {jpeg_path}')

except ImportError as e:
    print(f'matplotlib not available ({e}), skipping JPEG.')
    # Fallback: PIL
    try:
        from PIL import Image, ImageDraw, ImageFont
        W, H = 900, 500
        img = Image.new('RGB', (W, H), color=(26, 26, 46))
        d = ImageDraw.Draw(img)

        title = 'Motorola HX550 Ear Hook Overlay'
        d.text((W//2, 20), title, fill=(200,200,255), anchor='mt')

        # Draw top-view arc shape (simple)
        cx, cy, scale = 220, 320, 6
        for ang_deg in range(0, 106):
            ang = math.radians(ang_deg)
            for r in [ARC_RADIUS+OUTER_R, ARC_RADIUS-OUTER_R,
                      ARC_RADIUS+INNER_R, ARC_RADIUS-INNER_R]:
                x = int(cx + r*math.cos(ang)*scale)
                y = int(cy - r*math.sin(ang)*scale)
                d.ellipse([x-1, y-1, x+1, y+1], fill=(136, 170, 255))

        # Cross section
        for phi_deg in range(0, 360):
            phi = math.radians(phi_deg)
            for r in [OUTER_R, INNER_R]:
                x = int(650 + r*math.cos(phi)*25)
                y = int(250 - r*math.sin(phi)*25)
                d.ellipse([x-1, y-1, x+1, y+1], fill=(68, 102, 204))

        # Labels
        dims = [
            f'Arc radius: {ARC_RADIUS:.0f} mm',
            f'Arc angle:  {END_DEG-START_DEG:.0f} degrees',
            f'Outer dia:  {OUTER_R*2:.1f} mm',
            f'Inner dia:  {INNER_R*2:.1f} mm',
            f'Wall:       {OUTER_R-INNER_R:.1f} mm',
            f'Arc length: {arc_len:.1f} mm',
        ]
        for i, txt in enumerate(dims):
            d.text((480, 60 + i*22), txt, fill=(255,220,100))

        jpeg_path = '/Users/c395616/Downloads/motorola_ear_hook_reference.jpg'
        img.save(jpeg_path, 'JPEG', quality=92)
        print(f'JPEG saved (PIL fallback) → {jpeg_path}')
    except ImportError:
        print('PIL also not available — JPEG skipped.')

print('\nDone.')
