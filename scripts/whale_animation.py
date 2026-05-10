#!/usr/bin/env python3
"""Generate Docker whale contribution animation SVG."""

import os, json, urllib.request, math

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

BG          = "#090f1a"
EMPTY       = "#1e2d45"
LEVELS      = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WHALE_BLUE  = "#2496ED"

CELL  = 11
GAP   = 2
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
W     = COLS * STEP + 20
H     = ROWS * STEP + 60
DUR   = 12  # animation seconds

# ── fetch contributions ────────────────────────────────────────────────────────
query = json.dumps({"query": """{
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}""" % USER})

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=query.encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# ── build grid ─────────────────────────────────────────────────────────────────
grid = []  # (col, row, count)
for ci, week in enumerate(weeks[-COLS:]):
    for ri, day in enumerate(week["contributionDays"]):
        grid.append((ci, ri, day["contributionCount"]))

def level(count):
    if count == 0: return 0
    if count <= 3: return 1
    if count <= 6: return 2
    if count <= 9: return 3
    return 4

# ── snake path: zigzag column by column ───────────────────────────────────────
path_cells = []
for ci in range(COLS):
    col_cells = [(ci, ri) for ri in (range(ROWS) if ci % 2 == 0 else range(ROWS - 1, -1, -1))]
    path_cells.extend(col_cells)

def cx(c): return 10 + c * STEP + CELL // 2
def cy(r): return 30 + r * STEP + CELL // 2

# ── Docker whale SVG symbol ────────────────────────────────────────────────────
WHALE = f"""
  <symbol id="whale" viewBox="0 0 32 22" overflow="visible">
    <!-- tail -->
    <path d="M26 8 L32 4 L32 16 Z" fill="{WHALE_BLUE}"/>
    <!-- body -->
    <ellipse cx="14" cy="12" rx="13" ry="9" fill="{WHALE_BLUE}"/>
    <!-- container 1 -->
    <rect x="4"  y="2" width="7" height="7" rx="1.5" fill="white" opacity="0.92"/>
    <!-- container 2 -->
    <rect x="13" y="2" width="7" height="7" rx="1.5" fill="white" opacity="0.92"/>
    <!-- divider lines on containers -->
    <line x1="7.5" y1="2" x2="7.5" y2="9" stroke="{WHALE_BLUE}" stroke-width="0.8"/>
    <line x1="16.5" y1="2" x2="16.5" y2="9" stroke="{WHALE_BLUE}" stroke-width="0.8"/>
    <!-- eye -->
    <circle cx="3" cy="11" r="2.2" fill="white"/>
    <circle cx="3.4" cy="11" r="1" fill="#1a1a2e"/>
    <!-- water spout -->
    <path d="M10 0 Q11 -3 12 0 Q13 -3 14 0" stroke="{WHALE_BLUE}" stroke-width="1.8"
          fill="none" stroke-linecap="round"/>
  </symbol>
"""

# ── build SVG ─────────────────────────────────────────────────────────────────
lookup = {(c, r): count for c, r, count in grid}
n = len(path_cells)

# Each cell disappears when the whale reaches it.
# Whale position fraction at step i = i / (n-1)
# Cell i disappears at t = i/n * DUR  → animateTransform opacity 1→0

rects_svg = []
for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    color = LEVELS[level(count)]
    x = 10 + pc * STEP
    y = 30 + pr * STEP
    cell_id = f"c{pc}_{pr}"
    eat_t   = round(idx / n * DUR, 3)

    rect = (
        f'<rect id="{cell_id}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
        f'rx="2" fill="{color}">'
        f'<animate attributeName="opacity" values="1;1;0;0" '
        f'keyTimes="0;{eat_t/DUR:.4f};{min(eat_t/DUR+0.02,1):.4f};1" '
        f'dur="{DUR}s" repeatCount="indefinite" fill="freeze"/>'
        f'</rect>'
    )
    rects_svg.append(rect)

# Motion path for whale
path_d = "M " + " L ".join(f"{cx(c)},{cy(r)}" for c, r in path_cells)

whale_svg = f"""
  <path id="wp" d="{path_d}" fill="none" visibility="hidden"/>
  <use href="#whale" width="32" height="22" x="-16" y="-11">
    <animateMotion dur="{DUR}s" repeatCount="indefinite" rotate="auto" calcMode="linear">
      <mpath href="#wp"/>
    </animateMotion>
  </use>
"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>{WHALE}</defs>
  <rect width="{W}" height="{H}" rx="8" fill="{BG}"/>
  {"".join(rects_svg)}
  {whale_svg}
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Generated: {W}x{H}px, {n} cells, {DUR}s loop")
