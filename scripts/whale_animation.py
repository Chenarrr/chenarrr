#!/usr/bin/env python3
"""Docker whale contribution animation — row sweep, one direction."""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

BG         = "#090f1a"
LEVELS     = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WHALE_BLUE = "#2496ED"
WHITE      = "white"

CELL  = 11
GAP   = 2
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
PAD   = 16          # padding around grid
W     = COLS * STEP + PAD * 2
H     = ROWS * STEP + PAD * 2 + 20
DUR   = 30          # seconds

# ── fetch contributions ────────────────────────────────────────────────────────
query = json.dumps({"query": """{ user(login: "%s") {
  contributionsCollection { contributionCalendar {
    weeks { contributionDays { contributionCount } }
  } } } }""" % USER})

req = urllib.request.Request("https://api.github.com/graphql", data=query.encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

lookup = {}
for ci, week in enumerate(weeks[-COLS:]):
    for ri, day in enumerate(week["contributionDays"]):
        lookup[(ci, ri)] = day["contributionCount"]

def level(n):
    if n == 0: return 0
    if n <= 3: return 1
    if n <= 6: return 2
    if n <= 9: return 3
    return 4

# cell centre coords
def cx(c): return PAD + c * STEP + CELL // 2
def cy(r): return PAD + 20 + r * STEP + CELL // 2

# ── row-by-row path (sweeps horizontally, one direction feel) ─────────────────
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)

# ── smooth SVG motion path — bezier curves only at row-end turns ──────────────
def build_path(cells):
    pts  = [(cx(c), cy(r)) for c, r in cells]
    segs = [f"M {pts[0][0]},{pts[0][1]}"]
    for i in range(1, len(pts)):
        r_prev = cells[i - 1][1]
        r_curr = cells[i][1]
        px, py = pts[i - 1]
        x,  y  = pts[i]
        if r_curr != r_prev:
            # row transition — smooth outward arc
            bulge = STEP * 1.2
            if r_prev % 2 == 0:               # right-side turn
                segs.append(f"C {px+bulge},{py} {x+bulge},{y} {x},{y}")
            else:                              # left-side turn
                segs.append(f"C {px-bulge},{py} {x-bulge},{y} {x},{y}")
        else:
            segs.append(f"L {x},{y}")
    return " ".join(segs)

path_d = build_path(path_cells)

# ── CSS animations: cells pop outward then vanish when eaten ──────────────────
styles = []
rects  = []

for idx, (pc, pr) in enumerate(path_cells):
    count  = lookup.get((pc, pr), 0)
    color  = LEVELS[level(count)]
    rx     = PAD + pc * STEP
    ry     = PAD + 20 + pr * STEP
    ox, oy = rx + CELL // 2, ry + CELL // 2

    name   = f"e{pc}x{pr}"
    t0     = round(idx / n * 100, 3)
    t_pop  = round(min(t0 + 1.0, 99.5), 3)
    t_gone = round(min(t0 + 2.2, 100.0), 3)

    styles.append(
        f"@keyframes {name}{{0%,{t0}%{{opacity:1;transform:scale(1)}}"
        f"{t_pop}%{{opacity:.6;transform:scale(1.5)}}"
        f"{t_gone}%,100%{{opacity:0;transform:scale(0)}}}}"
    )
    rects.append(
        f'<rect x="{rx}" y="{ry}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" '
        f'style="transform-origin:{ox}px {oy}px;'
        f'animation:{name} {DUR}s ease-in-out infinite"/>'
    )

# ── Docker Moby whale (facing right, accurate design) ─────────────────────────
#   head = left, tail flukes = right, containers on top
whale = f"""<symbol id="wh" viewBox="0 0 30 20" overflow="visible">
  <!-- body -->
  <ellipse cx="13" cy="13" rx="12" ry="8" fill="{WHALE_BLUE}"/>
  <!-- tail — two flukes on the right -->
  <path d="M23 10 L30 6  L28 13 Z" fill="{WHALE_BLUE}"/>
  <path d="M23 14 L30 18 L28 11 Z" fill="{WHALE_BLUE}"/>
  <!-- container 1 -->
  <rect x="5"  y="3" width="7" height="7" rx="1.5" fill="{WHITE}" opacity="0.92"/>
  <!-- container 2 -->
  <rect x="14" y="3" width="7" height="7" rx="1.5" fill="{WHITE}" opacity="0.92"/>
  <!-- centre divider lines (Docker container look) -->
  <line x1="8.5"  y1="3" x2="8.5"  y2="10" stroke="{WHALE_BLUE}" stroke-width="0.9"/>
  <line x1="17.5" y1="3" x2="17.5" y2="10" stroke="{WHALE_BLUE}" stroke-width="0.9"/>
  <!-- eye on head (left side) -->
  <circle cx="3"   cy="12" r="2.2" fill="{WHITE}"/>
  <circle cx="3.4" cy="12" r="1"   fill="#0d1117"/>
  <!-- water spout from blow hole -->
  <path d="M9 1 Q10.5 -3 12 1 Q13.5 -3 15 1"
        stroke="{WHALE_BLUE}" stroke-width="1.8" fill="none" stroke-linecap="round"/>
</symbol>"""

# ── assemble ───────────────────────────────────────────────────────────────────
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  {whale}
  <style>{"".join(styles)}</style>
</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
{"".join(rects)}
<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>
<use href="#wh" width="30" height="20" x="-15" y="-10">
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Done — {W}x{H}  {n} cells  {DUR}s")
