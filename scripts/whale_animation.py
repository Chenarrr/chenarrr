#!/usr/bin/env python3
"""
Docker Moby whale contribution animation — production v3.

Critical fixes vs v2:
  • MOUTH is now at the path point (was: body centre).  Cells now visibly
    disappear under the whale's mouth, not behind its body.
  • Eating window tightened from 5% → 3.5% so cells pop *as* the whale passes,
    not 0.8s later.
  • Flash burst at each cell when eaten — white shock-wave that radiates out.
  • Proper articulated jaws (upper/lower) that open and close in chomping
    rhythm, instead of a single ellipse.
  • Slightly larger, more prominent whale.

Existing v2 features preserved:
  ✓ bubble trail        ✓ row-by-row whale flip
  ✓ level-4 cell glow   ✓ tail wag             ✓ cell respawn fade-in
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
PADY  = 36
W     = COLS * STEP + PADX * 2
H     = ROWS * STEP + PADY + PADX + 6
DUR   = 45
HALF  = CELL / 2

# Eating timing — much tighter than v2 (was 1.8/3.2/5.0)
EAT_POP_PCT = 0.45   # cell pops the instant whale's mouth arrives
EAT_FLY_PCT = 1.8    # cell rapidly rises
EAT_END_PCT = 3.5    # fully gone — well before the next cell

FADE_IN_END_PCT = 2.5
BUBBLE_DUR_PCT  = 4.5
FLASH_DUR_PCT   = 2.5

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
def kt(pct):  return f"{min(max(pct / 100, 0), 1):.5f}"
def kts(*ps): return ";".join(kt(p) for p in ps)

# ── cells ──────────────────────────────────────────────────────────────────────
cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    lvl   = level(count)
    color = LEVELS[lvl]
    ox    = cx(pc)
    oy    = cy(pr)

    t0    = idx / n * 100
    t_pop = min(t0 + EAT_POP_PCT, 99.5)
    t_fly = min(t0 + EAT_FLY_PCT, 99.8)
    t_end = min(t0 + EAT_END_PCT, 100.0)

    idle_period = round(2.0 + (pc % 4) * 0.5, 1)
    idle_begin  = round(((pc * 7 + pr * 13) % 40) / 10, 1)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # (3) GLOW HALO  — only level-4 cells, behind everything
    if lvl == 4:
        parts.append(f"""
  <rect x="-9" y="-9" width="18" height="18" rx="4" fill="{color}" opacity="0.3">
    <animate attributeName="opacity"
      values="0.25; 0.6; 0.3; 0.6; 0.25; 0"
      keyTimes="0; 0.2; 0.4; 0.6; {kt(min(t_pop-0.5, 99))}; {kt(t_pop)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </rect>""")

    # idle-pulse → fly-up → rect (pop+shrink+fade)
    parts.append(f"""
  <g>
    <animateTransform attributeName="transform" type="scale"
      values="1;1.06;1" keyTimes="0;0.5;1"
      dur="{idle_period}s" begin="{idle_begin}s" repeatCount="indefinite"/>
    <g>
      <animateTransform attributeName="transform" type="translate"
        values="0,0; 0,0; 0,-6; 0,-22; 0,-22"
        keyTimes="{kts(0, t0, t_pop, t_fly, t_end)}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .15 0 .4 1; .3 0 .8 1; 0 0 1 1"/>
      <rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">
        <animateTransform attributeName="transform" type="scale"
          values="1; 1; 1.6; 0.05; 0.05"
          keyTimes="{kts(0, t0, t_pop, t_fly, t_end)}"
          dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline"
          keySplines="0 0 1 1; .1 .8 .3 1; .4 0 1 1; 0 0 1 1"/>""")

    # (5) Opacity with optional fade-in at start of loop
    if t0 > FADE_IN_END_PCT:
        op_vals = "0; 1; 1; 0.5; 0; 0"
        op_kts  = kts(0, FADE_IN_END_PCT, t0, t_pop, t_fly, t_end)
        op_kspl = (".4 0 .8 1; "
                   "0 0 1 1; "
                   ".1 0 .9 1; "
                   ".4 0 1 1; "
                   "0 0 1 1")
    else:
        op_vals = "1; 1; 0.5; 0; 0"
        op_kts  = kts(0, t0, t_pop, t_fly, t_end)
        op_kspl = "0 0 1 1; .1 0 .9 1; .4 0 1 1; 0 0 1 1"

    parts.append(f"""
        <animate attributeName="opacity"
          values="{op_vals}" keyTimes="{op_kts}"
          dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline" keySplines="{op_kspl}"/>
      </rect>
    </g>
  </g>""")

    # FLASH BURST — white shock-wave at the moment the whale eats this cell
    if t0 > 0.3:
        f_t0    = t0
        f_peak  = min(t0 + FLASH_DUR_PCT * 0.25, 99.4)
        f_end   = min(t0 + FLASH_DUR_PCT, 99.9)
        parts.append(f"""
  <circle cx="0" cy="0" r="0" fill="white">
    <animate attributeName="r"
      values="0; 0; 3; 13"
      keyTimes="0; {kt(f_t0)}; {kt(f_peak)}; {kt(f_end)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .3 0 .8 1"/>
    <animate attributeName="opacity"
      values="0; 0; 0.85; 0"
      keyTimes="0; {kt(f_t0)}; {kt(f_peak)}; {kt(f_end)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .4 0 1 1"/>
    <animate attributeName="stroke-width"
      values="0; 0; 2; 0"
      keyTimes="0; {kt(f_t0)}; {kt(f_peak)}; {kt(f_end)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </circle>""")

    # (1) BUBBLE TRAIL — two small bubbles drift up from each eaten cell
    if t0 > 0.5:
        b_appear = t0
        b_peak   = min(t0 + BUBBLE_DUR_PCT * 0.15, 99.5)
        b_gone   = min(t0 + BUBBLE_DUR_PCT,        99.9)

        for bx_start, bx_end, by_end, r_start in (
            (-2.5, -4.5, -24, 1.7),
            ( 2.5,  5.0, -30, 1.4),
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
      values="0; {r_start}; 0.15"
      keyTimes="0; {kt(b_appear)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"/>
    <animate attributeName="opacity"
      values="0; 0.9; 0"
      keyTimes="0; {kt(b_peak)}; {kt(b_gone)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </circle>""")

    parts.append("</g>")
    cells_svg.append("".join(parts))

# ── whale flip keyTimes per row (alternate facing direction) ──────────────────
def flip_keytimes_and_values():
    flips_t = [0.0]
    flips_v = [1]
    total_segs = n - 1
    for r in range(ROWS - 1):
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
flip_kts  = ";".join(f"{x:.5f}" for x in flip_t)
flip_vals = "; ".join(f"{v} 1" for v in flip_v)

# ── Docker Moby whale (v3 — bigger, with articulated jaws) ────────────────────
#
#  viewBox: 0 0 44 24.  Body centred at (24, 14).  Mouth at (42, 16).
#  In <use> the mouth (42, 16) is offset to (0, 0) of local space so that
#  animateMotion positions the MOUTH directly on each path point.
#
WV = 44   # viewBox width
WH = 24   # viewBox height

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WH}" overflow="visible">

  <!-- (4) UPPER FLUKE — wags up/down -->
  <path d="M11 10 L0 4 L4 14 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M11 10 L0 4 L4 14 Z;
              M11 10 L0 1 L4 14 Z;
              M11 10 L0 4 L4 14 Z;
              M11 10 L0 7 L4 14 Z;
              M11 10 L0 4 L4 14 Z"
      dur="0.8s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>

  <!-- (4) LOWER FLUKE — wags in sync -->
  <path d="M11 16 L0 20 L4 12 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M11 16 L0 20 L4 12 Z;
              M11 16 L0 17 L4 12 Z;
              M11 16 L0 20 L4 12 Z;
              M11 16 L0 23 L4 12 Z;
              M11 16 L0 20 L4 12 Z"
      dur="0.8s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>

  <!-- BODY -->
  <ellipse cx="24" cy="14" rx="16" ry="10" fill="{WBLUE}"/>

  <!-- two CONTAINERS on top -->
  <rect x="13" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
  <rect x="24" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
  <line x1="17.5" y1="2" x2="17.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>
  <line x1="28.5" y1="2" x2="28.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>

  <!-- EYE on front -->
  <circle cx="38" cy="12" r="2.8" fill="white"/>
  <circle cx="37.5" cy="12" r="1.2" fill="#080d17"/>

  <!-- (NEW) ARTICULATED JAWS — upper + lower, open/close chomping -->
  <!-- upper jaw -->
  <path stroke="#080d17" stroke-width="0.8" fill="#080d17" opacity="0.95"
        d="M38 16 Q41 16 43 16 L42 16 Z">
    <animate attributeName="d"
      values="M38 16 Q41 16 43 16 L42 16 Z;
              M38 16 Q41 12 43 14 L42 16 Z;
              M38 16 Q41 16 43 16 L42 16 Z;
              M38 16 Q41 12 43 14 L42 16 Z;
              M38 16 Q41 16 43 16 L42 16 Z"
      dur="0.55s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1"/>
  </path>
  <!-- lower jaw -->
  <path stroke="#080d17" stroke-width="0.8" fill="#080d17" opacity="0.95"
        d="M38 17 Q41 17 43 17 L42 17 Z">
    <animate attributeName="d"
      values="M38 17 Q41 17 43 17 L42 17 Z;
              M38 17 Q41 21 43 19 L42 17 Z;
              M38 17 Q41 17 43 17 L42 17 Z;
              M38 17 Q41 21 43 19 L42 17 Z;
              M38 17 Q41 17 43 17 L42 17 Z"
      dur="0.55s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1"/>
  </path>

  <!-- BLOW-HOLE SPOUT -->
  <path d="M21 -1 Q22.5 -6 24 -1 Q25.5 -6 27 -1"
    stroke="{WBLUE}" stroke-width="2.4" fill="none" stroke-linecap="round">
    <animate attributeName="opacity" values="0.5; 1; 0.5" dur="1.1s" repeatCount="indefinite"/>
    <animate attributeName="stroke-width" values="2; 3.6; 2" dur="1.1s" repeatCount="indefinite"/>
  </path>
</symbol>"""

# ── assemble final SVG ─────────────────────────────────────────────────────────
#  Use offset: x="-42" y="-16"  →  the MOUTH (viewBox 42,16) sits at the local
#  origin (0,0).  animateMotion moves this origin along the path, so the mouth
#  follows the cell centres exactly.  When scale(-1,1) flips the whale, the
#  mouth stays at the origin while body+tail mirror behind it.

MOUTH_OFFSET_X = -42
MOUTH_OFFSET_Y = -16

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>{whale}</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>

{"".join(cells_svg)}

<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>

<use href="#wh" width="{WV}" height="{WH}" x="{MOUTH_OFFSET_X}" y="{MOUTH_OFFSET_Y}">
  <!-- (2) row flip: mirror horizontally so whale always faces forward -->
  <animateTransform attributeName="transform" type="scale"
    values="{flip_vals}" keyTimes="{flip_kts}"
    dur="{DUR}s" repeatCount="indefinite" additive="sum"/>

  <!-- gentle vertical bob -->
  <animateTransform attributeName="transform" type="translate"
    values="0,-3; 0,3; 0,-3" keyTimes="0;0.5;1"
    dur="1.8s" repeatCount="indefinite" additive="sum"
    calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>

  <!-- path motion at constant speed -->
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Generated: {W}x{H}px | {n} cells | {DUR}s loop")
