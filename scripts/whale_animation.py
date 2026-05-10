#!/usr/bin/env python3
"""
Docker Moby whale — perfect contribution animation.

Design goals:
- Uniform speed across every row (pure straight-line path, all segments equal length)
- Whale opens/closes mouth continuously (chomping effect)
- Whale bobs up-down as it moves (separate animateTransform)
- Cells pop outward then fly upward when eaten (nested SMIL groups)
- Empty cells breathe/pulse with staggered timing (idle life)
- Everything SMIL — works in SVG-as-img on GitHub
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

# ── constants ──────────────────────────────────────────────────────────────────
BG     = "#090f1a"
LEVELS = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"

CELL  = 11          # px per cell
GAP   = 2           # px between cells
STEP  = CELL + GAP  # 13 px — same for X and Y so all path segments are equal length
COLS  = 52
ROWS  = 7
PADX  = 18          # left/right padding
PADY  = 34          # top padding (room for spout above row 0)
W     = COLS * STEP + PADX * 2
H     = ROWS * STEP + PADY + PADX + 4
DUR   = 45          # seconds — slow, deliberate, satisfying
HALF  = CELL / 2    # 5.5 — used to centre rect at group origin

# ── fetch contribution data ────────────────────────────────────────────────────
query = json.dumps({"query": """{ user(login: "%s") {
  contributionsCollection { contributionCalendar {
    weeks { contributionDays { contributionCount } }
  } } } }""" % USER})

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=query.encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

weeks = (
    data["data"]["user"]["contributionsCollection"]
    ["contributionCalendar"]["weeks"]
)

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

# cell-centre pixel coords — STEP is identical in X and Y, so every consecutive
# pair of path points (horizontal or vertical) is exactly STEP px apart.
# animateMotion with calcMode="linear" then moves at perfectly constant speed.
def cx(c): return PADX + c * STEP + HALF
def cy(r): return PADY + r * STEP + HALF

# ── path: row-by-row horizontal sweep, pure straight lines ────────────────────
# Even rows → left to right.  Odd rows → right to left.
# Column turns are single vertical steps (same distance as horizontal steps).
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)

path_d = "M " + " L ".join(
    f"{cx(c):.2f},{cy(r):.2f}" for c, r in path_cells
)

# ── helper: SMIL keyTimes string ───────────────────────────────────────────────
def kts(*pcts):
    """Convert list of percentage values to SMIL keyTimes string (0–1)."""
    return ";".join(f"{min(max(p / 100, 0), 1):.5f}" for p in pcts)

# ── cells ──────────────────────────────────────────────────────────────────────
#
#  Structure (4 layers):
#   <g transform="translate(ox,oy)">           ← static position
#     <g>                                       ← idle-pulse scale (life before eaten)
#       <animateTransform type=scale …/>
#       <g>                                     ← eating: fly upward
#         <animateTransform type=translate …/>
#         <rect centred at 0,0>                 ← eating: pop+shrink scale & fade
#           <animateTransform type=scale …/>
#           <animate opacity …/>
#         </rect>
#       </g>
#     </g>
#   </g>
#
#  Animations on different elements avoid additive-stacking conflicts.

cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    color = LEVELS[level(count)]
    ox    = cx(pc)
    oy    = cy(pr)

    # fraction along the path when the whale arrives at this cell
    t0    = idx / n * 100                     # %
    t_pop = min(t0 + 1.8,  99.5)             # peak pop (scale 1.45×)
    t_fly = min(t0 + 3.2,  99.8)             # halfway up
    t_end = min(t0 + 5.0, 100.0)             # fully gone

    # idle pulse: each cell breathes independently
    # period varies slightly (2.0–3.5 s), begin offset is pseudo-random
    idle_period = round(2.0 + (pc % 4) * 0.5, 1)
    idle_begin  = round(((pc * 7 + pr * 13) % 40) / 10, 1)

    cells_svg.append(f"""
<g transform="translate({ox:.2f},{oy:.2f})">
  <g>
    <animateTransform attributeName="transform" type="scale"
      values="1;1.06;1"
      keyTimes="0;0.5;1"
      dur="{idle_period}s" begin="{idle_begin}s"
      repeatCount="indefinite"/>
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="0,0; 0,0; 0,-7; 0,-24; 0,-24"
        keyTimes="{kts(0, t0, t_pop, t_fly, t_end)}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .15 0 .5 1; .3 0 .8 1; 0 0 1 1"/>
      <rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">
        <animateTransform attributeName="transform" type="scale"
          values="1; 1; 1.45; 0.08; 0.08"
          keyTimes="{kts(0, t0, t_pop, t_fly, t_end)}"
          dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline"
          keySplines="0 0 1 1; .2 0 .5 1; .4 0 1 1; 0 0 1 1"/>
        <animate attributeName="opacity"
          values="1; 1; 0.55; 0; 0"
          keyTimes="{kts(0, t0, t_pop, t_fly, t_end)}"
          dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline"
          keySplines="0 0 1 1; .1 0 .9 1; .5 0 1 1; 0 0 1 1"/>
      </rect>
    </g>
  </g>
</g>""")

# ── Docker Moby whale symbol ───────────────────────────────────────────────────
#
#  Whale faces RIGHT.  viewBox "0 0 36 22".
#  Tail flukes: left side (x ≈ 0–8).
#  Body ellipse: centred at (20, 13).
#  Containers: two white boxes on top (x 10–28, y 2–10).
#  Eye: right/front side at (33, 12).
#  Mouth: animated ellipse at (35, 16) — opens/closes every 0.65 s.
#  Spout: wavy path above body, pulses.
#
#  The <use> element is offset x="-20" y="-13" so that the body centre (20,13)
#  sits exactly on the animateMotion path point.

whale = f"""<symbol id="wh" viewBox="0 0 36 22" overflow="visible">
  <!-- tail: two flukes on the left -->
  <path d="M8 9 L0 4 L3 13 Z"  fill="{WBLUE}"/>
  <path d="M8 14 L0 19 L3 11 Z" fill="{WBLUE}"/>
  <!-- body -->
  <ellipse cx="20" cy="13" rx="14" ry="9" fill="{WBLUE}"/>
  <!-- container 1 -->
  <rect x="10" y="2" width="8" height="8" rx="2" fill="white" opacity="0.93"/>
  <!-- container 2 -->
  <rect x="20" y="2" width="8" height="8" rx="2" fill="white" opacity="0.93"/>
  <!-- centre dividers on containers (Docker look) -->
  <line x1="14" y1="2" x2="14" y2="10" stroke="{WBLUE}" stroke-width="1.1"/>
  <line x1="24" y1="2" x2="24" y2="10" stroke="{WBLUE}" stroke-width="1.1"/>
  <!-- eye on front/right -->
  <circle cx="33"   cy="11" r="2.6" fill="white"/>
  <circle cx="32.6" cy="11" r="1.1" fill="#080d17"/>
  <!-- mouth: animates open–close every 0.65 s (chomp) -->
  <ellipse cx="35.5" cy="15.5" rx="1.4" ry="0.3" fill="#080d17" opacity="0.85">
    <animate attributeName="ry"
      values="0.3; 3.2; 0.3; 3.2; 0.3"
      dur="0.65s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
    <animate attributeName="cy"
      values="15.5; 16.6; 15.5; 16.6; 15.5"
      dur="0.65s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </ellipse>
  <!-- blow-hole spout: pulses in and out -->
  <path d="M17 0 Q18.5 -5 20 0 Q21.5 -5 23 0"
    stroke="{WBLUE}" stroke-width="2.2" fill="none" stroke-linecap="round">
    <animate attributeName="opacity" values="0.5; 1; 0.5" dur="1.1s" repeatCount="indefinite"/>
    <animate attributeName="stroke-width" values="1.8; 3.2; 1.8" dur="1.1s" repeatCount="indefinite"/>
  </path>
</symbol>"""

# ── assemble final SVG ─────────────────────────────────────────────────────────
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>{whale}</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
{"".join(cells_svg)}
<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>
<!--
  <use> layers two animations:
    1. animateMotion  — moves the whale along the grid path at constant speed
    2. animateTransform translate — gentle perpendicular bob (up-down oscillation)
  The two compose: bob happens in local space, motion moves the local origin along path.
-->
<use href="#wh" width="36" height="22" x="-20" y="-13">
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
  <animateTransform attributeName="transform" type="translate"
    values="0,-3; 0,3; 0,-3"
    keyTimes="0;0.5;1"
    dur="1.8s" repeatCount="indefinite" additive="sum"
    calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Generated: {W}x{H}px | {n} cells | {DUR}s loop")
