#!/usr/bin/env python3
"""Docker whale contribution animation — SMIL-only, cells fly up when eaten."""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

BG         = "#090f1a"
LEVELS     = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WHALE_BLUE = "#2496ED"

CELL  = 11
GAP   = 2
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
PAD   = 16
W     = COLS * STEP + PAD * 2
H     = ROWS * STEP + PAD * 2 + 20
DUR   = 30     # seconds
HALF  = CELL // 2

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

def cx(c): return PAD + c * STEP + HALF
def cy(r): return PAD + 20 + r * STEP + HALF

# ── row-by-row horizontal path ─────────────────────────────────────────────────
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)

# ── smooth motion path — bezier arcs at row turns ─────────────────────────────
def build_path(cells):
    pts  = [(cx(c), cy(r)) for c, r in cells]
    segs = [f"M {pts[0][0]},{pts[0][1]}"]
    for i in range(1, len(pts)):
        r_prev = cells[i - 1][1]
        r_curr = cells[i][1]
        px, py = pts[i - 1]
        x,  y  = pts[i]
        if r_curr != r_prev:
            bulge = STEP * 1.3
            if r_prev % 2 == 0:
                segs.append(f"C {px+bulge},{py} {x+bulge},{y} {x},{y}")
            else:
                segs.append(f"C {px-bulge},{py} {x-bulge},{y} {x},{y}")
        else:
            segs.append(f"L {x},{y}")
    return " ".join(segs)

path_d = build_path(path_cells)

# ── cells: SMIL fly-up + scale + fade when eaten ──────────────────────────────
# Structure per cell:
#   <g transform="translate(ox,oy)">          ← static position
#     <g>                                      ← animated: fly up
#       <animateTransform type="translate" …/>
#       <rect x="-HALF" y="-HALF" …>          ← rect centred at 0,0
#         <animateTransform type="scale" …/>  ← pop then shrink
#         <animate attributeName="opacity" …/>
#       </rect>
#     </g>
#   </g>

def kt(pct):      # keyTime fraction, 5 dp
    return f"{min(max(pct / 100, 0), 1):.5f}"

cells_svg = []
for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    color = LEVELS[level(count)]
    ox    = cx(pc)
    oy    = cy(pr)

    t0    = round(idx / n * 100, 3)           # whale arrives (%)
    t_pop = round(min(t0 + 1.0, 99.5), 3)    # peak pop
    t_end = round(min(t0 + 2.5, 100.0), 3)   # fully gone

    ktimes = f"0;{kt(t0)};{kt(t_pop)};{kt(t_end)};1"

    cells_svg.append(f"""<g transform="translate({ox},{oy})">
  <g>
    <animateTransform attributeName="transform" type="translate"
      values="0,0; 0,0; 0,-5; 0,-20; 0,-20"
      keyTimes="{ktimes}" dur="{DUR}s" repeatCount="indefinite" calcMode="spline"
      keySplines="0 0 1 1; .2 0 .8 1; .4 0 1 1; 0 0 1 1"/>
    <rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">
      <animateTransform attributeName="transform" type="scale"
        values="1; 1; 1.5; 0.15; 0.15"
        keyTimes="{ktimes}" dur="{DUR}s" repeatCount="indefinite" calcMode="spline"
        keySplines="0 0 1 1; .2 0 .6 1; .4 0 1 1; 0 0 1 1"/>
      <animate attributeName="opacity"
        values="1; 1; 0.7; 0; 0"
        keyTimes="{ktimes}" dur="{DUR}s" repeatCount="indefinite" calcMode="spline"
        keySplines="0 0 1 1; .2 0 .8 1; .4 0 1 1; 0 0 1 1"/>
    </rect>
  </g>
</g>""")

# ── Docker Moby whale (facing right) ──────────────────────────────────────────
whale = f"""<symbol id="wh" viewBox="0 0 30 20" overflow="visible">
  <ellipse cx="13" cy="13" rx="12" ry="8" fill="{WHALE_BLUE}"/>
  <path d="M23 10 L30 6  L28 13 Z" fill="{WHALE_BLUE}"/>
  <path d="M23 14 L30 18 L28 11 Z" fill="{WHALE_BLUE}"/>
  <rect x="5"  y="3" width="7" height="7" rx="1.5" fill="white" opacity="0.92"/>
  <rect x="14" y="3" width="7" height="7" rx="1.5" fill="white" opacity="0.92"/>
  <line x1="8.5"  y1="3" x2="8.5"  y2="10" stroke="{WHALE_BLUE}" stroke-width="0.9"/>
  <line x1="17.5" y1="3" x2="17.5" y2="10" stroke="{WHALE_BLUE}" stroke-width="0.9"/>
  <circle cx="3"   cy="12" r="2.2" fill="white"/>
  <circle cx="3.4" cy="12" r="1"   fill="#0d1117"/>
  <path d="M9 1 Q10.5 -3 12 1 Q13.5 -3 15 1"
        stroke="{WHALE_BLUE}" stroke-width="1.8" fill="none" stroke-linecap="round"/>
</symbol>"""

# ── assemble ───────────────────────────────────────────────────────────────────
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>{whale}</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
{"".join(cells_svg)}
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
