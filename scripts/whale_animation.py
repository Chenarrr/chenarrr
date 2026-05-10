#!/usr/bin/env python3
"""Generate Docker whale contribution animation SVG."""

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
W     = COLS * STEP + 20
H     = ROWS * STEP + 60
DUR   = 28   # seconds — slow and satisfying

# ── fetch contributions ────────────────────────────────────────────────────────
query = json.dumps({"query": """{ user(login: "%s") {
  contributionsCollection { contributionCalendar {
    weeks { contributionDays { contributionCount date } }
  } } } }""" % USER})

req = urllib.request.Request("https://api.github.com/graphql", data=query.encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# ── grid lookup ────────────────────────────────────────────────────────────────
lookup = {}
for ci, week in enumerate(weeks[-COLS:]):
    for ri, day in enumerate(week["contributionDays"]):
        lookup[(ci, ri)] = day["contributionCount"]

def level(count):
    if count == 0: return 0
    if count <= 3: return 1
    if count <= 6: return 2
    if count <= 9: return 3
    return 4

def cx(c): return 10 + c * STEP + CELL // 2
def cy(r): return 30 + r * STEP + CELL // 2

# ── zigzag path ────────────────────────────────────────────────────────────────
path_cells = []
for ci in range(COLS):
    col = range(ROWS) if ci % 2 == 0 else range(ROWS - 1, -1, -1)
    path_cells.extend((ci, ri) for ri in col)

n = len(path_cells)

# ── smooth SVG motion path (bezier at column turns) ───────────────────────────
def build_smooth_path(cells):
    pts = [(cx(c), cy(r)) for c, r in cells]
    d = [f"M {pts[0][0]},{pts[0][1]}"]
    i = 1
    while i < len(pts):
        c_prev, _ = cells[i - 1]
        c_curr, _ = cells[i]
        px, py = pts[i - 1]
        x, y   = pts[i]

        if c_curr != c_prev:
            # column boundary — smooth quarter-circle-ish bezier
            d.append(f"C {px},{py} {x},{py} {x},{y}")
        else:
            # straight vertical segment
            d.append(f"L {x},{y}")
        i += 1
    return " ".join(d)

path_d = build_smooth_path(path_cells)

# ── CSS keyframes: cells pop then vanish when eaten ───────────────────────────
style_parts = []
rect_parts  = []

for idx, (pc, pr) in enumerate(path_cells):
    count  = lookup.get((pc, pr), 0)
    color  = LEVELS[level(count)]
    rx     = 10 + pc * STEP
    ry     = 30 + pr * STEP
    ox, oy = rx + CELL // 2, ry + CELL // 2   # transform-origin centre

    name   = f"e{pc}x{pr}"
    t0     = round(idx / n * 100, 3)           # whale arrives %
    t_pop  = round(min(t0 + 1.2, 99.5), 3)    # pop peak %
    t_gone = round(min(t0 + 2.5, 100), 3)     # fully gone %

    style_parts.append(
        f"@keyframes {name}{{"
        f"0%,{t0}%{{opacity:1;transform:scale(1)}}"
        f"{t_pop}%{{opacity:.7;transform:scale(1.45)}}"
        f"{t_gone}%,100%{{opacity:0;transform:scale(0)}}}}"
    )
    rect_parts.append(
        f'<rect x="{rx}" y="{ry}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" '
        f'style="transform-origin:{ox}px {oy}px;'
        f'animation:{name} {DUR}s cubic-bezier(.4,0,.6,1) infinite"/>'
    )

# ── Docker whale symbol ────────────────────────────────────────────────────────
whale_sym = f"""<symbol id="wh" viewBox="0 0 36 24" overflow="visible">
  <path d="M28 9 L36 4 L36 18 Z" fill="{WHALE_BLUE}"/>
  <ellipse cx="16" cy="14" rx="15" ry="10" fill="{WHALE_BLUE}"/>
  <rect x="4"  y="2" width="8" height="8" rx="2" fill="white" opacity="0.92"/>
  <rect x="15" y="2" width="8" height="8" rx="2" fill="white" opacity="0.92"/>
  <line x1="8"  y1="2" x2="8"  y2="10" stroke="{WHALE_BLUE}" stroke-width="1"/>
  <line x1="19" y1="2" x2="19" y2="10" stroke="{WHALE_BLUE}" stroke-width="1"/>
  <circle cx="3" cy="13" r="2.5" fill="white"/>
  <circle cx="3.5" cy="13" r="1.1" fill="#1a1a2e"/>
  <path d="M12 0 Q13.5 -4 15 0 Q16.5 -4 18 0"
        stroke="{WHALE_BLUE}" stroke-width="2" fill="none" stroke-linecap="round"/>
</symbol>"""

# ── assemble SVG ───────────────────────────────────────────────────────────────
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  {whale_sym}
  <style>{"".join(style_parts)}</style>
</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
{"".join(rect_parts)}
<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>
<use href="#wh" width="36" height="24" x="-18" y="-12">
  <animateMotion dur="{DUR}s" repeatCount="indefinite" rotate="auto" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Done: {W}x{H}  |  {n} cells  |  {DUR}s loop")
