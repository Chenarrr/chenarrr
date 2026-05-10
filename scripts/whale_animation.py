#!/usr/bin/env python3
"""
Docker Moby whale — contribution animation v2.

Layers (added on top of v1, not breaking existing behaviour):
  1. Bubble trail        — 2 small circles float up from each eaten cell
  2. Whale flips         — animateTransform scaleX toggles between rows so the
                           whale always faces the direction it is eating
  3. Cell glow           — level-4 cells (10+ contributions) have a soft halo
                           that pulses, then absorbs at t_pop
  4. Tail wag            — the two fluke paths animate their `d` attribute
                           on a 0.8s loop while the whale swims
  5. Respawn fade-in     — cells with t0 > 2.5% fade in smoothly at start of
                           each loop instead of snapping into existence
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

# ── constants ──────────────────────────────────────────────────────────────────
BG     = "#090f1a"
LEVELS = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"

CELL  = 11
GAP   = 2
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
PADX  = 18
PADY  = 34
W     = COLS * STEP + PADX * 2
H     = ROWS * STEP + PADY + PADX + 4
DUR   = 45
HALF  = CELL / 2

FADE_IN_END_PCT = 2.5   # %  — cells fade in before this point at start of loop
BUBBLE_DUR_PCT  = 4.0   # %  — bubble lifetime relative to total loop

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

weeks = (data["data"]["user"]["contributionsCollection"]
             ["contributionCalendar"]["weeks"])

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

def cx(c): return PADX + c * STEP + HALF
def cy(r): return PADY + r * STEP + HALF

# ── path: row-by-row sweep, pure straight segments → uniform speed ────────────
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)
path_d = "M " + " L ".join(f"{cx(c):.2f},{cy(r):.2f}" for c, r in path_cells)

# ── helpers ────────────────────────────────────────────────────────────────────
def kt(pct):
    return f"{min(max(pct / 100, 0), 1):.5f}"

def kts(*pcts):
    return ";".join(kt(p) for p in pcts)

# ── cells ──────────────────────────────────────────────────────────────────────
#
#  <g transform="translate(ox,oy)">              ← static position
#    [glow rect — only for level 4]
#    <g> idle-pulse scale
#      <g> eating fly-up translate
#        <rect> eating pop+shrink scale + fade
#      </g>
#    </g>
#    [bubble 1, bubble 2 — at top-most z-order]
#  </g>

cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    lvl   = level(count)
    color = LEVELS[lvl]
    ox    = cx(pc)
    oy    = cy(pr)

    # whale arrival / consumption fractions (%)
    t0    = idx / n * 100
    t_pop = min(t0 + 1.8,  99.5)
    t_fly = min(t0 + 3.2,  99.8)
    t_end = min(t0 + 5.0, 100.0)

    # idle pulse — slightly different per cell so they don't sync
    idle_period = round(2.0 + (pc % 4) * 0.5, 1)
    idle_begin  = round(((pc * 7 + pr * 13) % 40) / 10, 1)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # ── (3) glow halo behind level-4 cells ─────────────────────────────────────
    if lvl == 4:
        # halo pulses gently 0.25→0.55→0.25 during idle, fades to 0 at t_pop
        parts.append(f"""
  <rect x="-8" y="-8" width="16" height="16" rx="3.5" fill="{color}" opacity="0.3">
    <animate attributeName="opacity"
      values="0.25; 0.55; 0.25; 0.55; 0.25; 0"
      keyTimes="0; 0.18; 0.36; 0.54; {kt(min(t_pop-0.5, 99))}; {kt(t_pop)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </rect>""")

    # ── (1) idle pulse group + nested eating animations ────────────────────────
    parts.append(f"""
  <g>
    <animateTransform attributeName="transform" type="scale"
      values="1;1.06;1" keyTimes="0;0.5;1"
      dur="{idle_period}s" begin="{idle_begin}s" repeatCount="indefinite"/>
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
          keySplines="0 0 1 1; .2 0 .5 1; .4 0 1 1; 0 0 1 1"/>""")

    # ── (5) opacity with fade-in for cells whose t0 is past FADE_IN_END ────────
    if t0 > FADE_IN_END_PCT:
        # fade-in 0→1 from t=0 to FADE_IN_END_PCT, then full until eaten
        op_vals = "0; 1; 1; 0.55; 0; 0"
        op_kts  = kts(0, FADE_IN_END_PCT, t0, t_pop, t_fly, t_end)
        op_kspl = (".4 0 .8 1; "      # ease-out for fade-in
                   "0 0 1 1; "        # hold flat
                   ".1 0 .9 1; "      # fade to 0.55
                   ".5 0 1 1; "       # fade to 0
                   "0 0 1 1")
    else:
        op_vals = "1; 1; 0.55; 0; 0"
        op_kts  = kts(0, t0, t_pop, t_fly, t_end)
        op_kspl = "0 0 1 1; .1 0 .9 1; .5 0 1 1; 0 0 1 1"

    parts.append(f"""
        <animate attributeName="opacity"
          values="{op_vals}" keyTimes="{op_kts}"
          dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline" keySplines="{op_kspl}"/>
      </rect>
    </g>
  </g>""")

    # ── (1) bubble trail — 2 small circles drift upward when cell eaten ───────
    # Skip bubbles for the very first few cells (t0 ≈ 0) — no room to animate
    if t0 > 0.5:
        b_appear = t0
        b_peak   = min(t0 + BUBBLE_DUR_PCT * 0.15, 99.5)
        b_gone   = min(t0 + BUBBLE_DUR_PCT,         99.9)

        for bx_start, bx_end, by_end, r_start in (
            (-2.5,  -4,  -22, 1.6),
            ( 2.5,   5,  -28, 1.3),
        ):
            parts.append(f"""
  <circle cx="{bx_start}" cy="0" r="0" fill="{WBLUE}">
    <animate attributeName="cx"
      values="{bx_start}; {bx_start}; {bx_end}"
      keyTimes="0; {kt(b_appear)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"/>
    <animate attributeName="cy"
      values="0; 0; {by_end}"
      keyTimes="0; {kt(b_appear)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .25 .1 .25 1"/>
    <animate attributeName="r"
      values="0; {r_start}; 0.2"
      keyTimes="0; {kt(b_appear)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"/>
    <animate attributeName="opacity"
      values="0; 0.85; 0"
      keyTimes="0; {kt(b_peak)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </circle>""")

    parts.append("</g>")
    cells_svg.append("".join(parts))

# ── whale flip keyTimes (per row, even = facing right, odd = left) ────────────
#   row r occupies cells [r*52, (r+1)*52 - 1]
#   total path segments = n - 1 = 363
# Flip happens during the brief 1-cell transition between rows.
def flip_keytimes_and_values():
    flips_t = [0.0]
    flips_v = [1]
    cells_per_row = COLS
    total_segs = n - 1   # 363
    for r in range(ROWS - 1):
        # end of row r: cell index (r+1)*COLS - 1
        end_idx   = (r + 1) * COLS - 1
        trans_idx = (r + 1) * COLS
        flips_t.append(end_idx / total_segs)
        flips_v.append(flips_v[-1])
        flips_t.append(trans_idx / total_segs)
        flips_v.append(1 if (r + 1) % 2 == 0 else -1)
    flips_t.append(1.0)
    flips_v.append(flips_v[-1])
    return flips_t, flips_v

flip_t, flip_v = flip_keytimes_and_values()
flip_kts = ";".join(f"{x:.5f}" for x in flip_t)
flip_vals = "; ".join(f"{v} 1" for v in flip_v)   # "scale x y" pairs

# ── Docker Moby whale symbol with tail wag ────────────────────────────────────
#
#  Facing RIGHT.  viewBox 0 0 40 22.  Body centred at (22, 13).
#  Tail flukes (left, x 0–10), body, containers, eye, mouth (right at x 38),
#  spout above the containers, all animated.

whale = f"""<symbol id="wh" viewBox="0 0 40 22" overflow="visible">

  <!-- (4) tail upper fluke — wags up/down with d animation -->
  <path d="M10 9 L0 4 L3 13 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M10 9 L0 4 L3 13 Z;
              M10 9 L0 1 L3 13 Z;
              M10 9 L0 4 L3 13 Z;
              M10 9 L0 7 L3 13 Z;
              M10 9 L0 4 L3 13 Z"
      dur="0.8s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>

  <!-- (4) tail lower fluke — wags in sync with upper fluke -->
  <path d="M10 14 L0 19 L3 11 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M10 14 L0 19 L3 11 Z;
              M10 14 L0 16 L3 11 Z;
              M10 14 L0 19 L3 11 Z;
              M10 14 L0 22 L3 11 Z;
              M10 14 L0 19 L3 11 Z"
      dur="0.8s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>

  <!-- body -->
  <ellipse cx="22" cy="13" rx="15" ry="9" fill="{WBLUE}"/>

  <!-- two containers on top -->
  <rect x="12" y="2" width="8" height="8" rx="2" fill="white" opacity="0.93"/>
  <rect x="22" y="2" width="8" height="8" rx="2" fill="white" opacity="0.93"/>
  <line x1="16" y1="2" x2="16" y2="10" stroke="{WBLUE}" stroke-width="1.1"/>
  <line x1="26" y1="2" x2="26" y2="10" stroke="{WBLUE}" stroke-width="1.1"/>

  <!-- eye on front (right) -->
  <circle cx="35.5" cy="11" r="2.6" fill="white"/>
  <circle cx="35.1" cy="11" r="1.1" fill="#080d17"/>

  <!-- mouth: chomps open–close every 0.65s -->
  <ellipse cx="38" cy="15.5" rx="1.4" ry="0.3" fill="#080d17" opacity="0.85">
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

  <!-- blow-hole spout -->
  <path d="M19 0 Q20.5 -5 22 0 Q23.5 -5 25 0"
    stroke="{WBLUE}" stroke-width="2.2" fill="none" stroke-linecap="round">
    <animate attributeName="opacity" values="0.5; 1; 0.5" dur="1.1s" repeatCount="indefinite"/>
    <animate attributeName="stroke-width" values="1.8; 3.2; 1.8" dur="1.1s" repeatCount="indefinite"/>
  </path>
</symbol>"""

# ── assemble final SVG ─────────────────────────────────────────────────────────
#
#  The <use> stacks three transforms additively:
#    1. animateMotion          — moves whale along path (constant speed)
#    2. translate bob          — ±3 px vertical oscillation (1.8 s)
#    3. scale flip             — mirror horizontally between rows (instant flip)
#
#  Whale body centre (22,13) is offset onto the path point via x="-22" y="-13".

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>{whale}</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>

{"".join(cells_svg)}

<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>

<use href="#wh" width="40" height="22" x="-22" y="-13">
  <!-- (2) flip: mirror horizontally at every row boundary so the whale always
       faces forward.  Done with discrete-style fast spline flip during the
       brief row-transition segment. -->
  <animateTransform attributeName="transform" type="scale"
    values="{flip_vals}"
    keyTimes="{flip_kts}"
    dur="{DUR}s" repeatCount="indefinite" additive="sum"/>

  <!-- gentle vertical bobbing -->
  <animateTransform attributeName="transform" type="translate"
    values="0,-3; 0,3; 0,-3" keyTimes="0;0.5;1"
    dur="1.8s" repeatCount="indefinite" additive="sum"
    calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>

  <!-- path motion (uniform speed) -->
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Generated: {W}x{H}px | {n} cells | {DUR}s loop")
