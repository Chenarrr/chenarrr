#!/usr/bin/env python3
"""
Docker Moby whale contribution animation — v4 "actually eats them".

The eating moment is the entire point.  In v3 the cell pop happened ~0.2 s
*after* the whale's mouth had already moved on, so the eating looked
disconnected from the whale.

In v4:
  • Cell crushes within 0.07 s of mouth arrival (well inside the 0.12 s the
    whale spends on a cell).  Crush IS the bite.
  • Cell shatters into 4 colour-matched quarter-shards that fly out
    diagonally — clearly destroyed, not just faded.
  • Big white shock-wave flash (radius 28 px) bursts from the cell.
  • Whale body has a swallow-pulse synced with the mouth chomp.
  • Mouth jaws snap shut just as cells crush — looks like an actual bite.
  • Bubbles drift up *after* the eating, like a digestive burp.

Preserved: row flip, tail wag, level-4 glow, fade-in respawn, smooth bob.
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

# ── visual constants ──────────────────────────────────────────────────────────
BG     = "#090f1a"
LEVELS = ["#1e2d45", "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"

CELL  = 11
GAP   = 2
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
PADX  = 18
PADY  = 38
W     = COLS * STEP + PADX * 2
H     = ROWS * STEP + PADY + PADX + 8
DUR   = 45
HALF  = CELL / 2

# Eating phase percentages (of DUR).  Whale spends ~0.275 % per cell.
EAT_JOLT_PCT   = 0.05    # cell pops slightly bigger — anticipation
EAT_CRUSH_PCT  = 0.22    # cell crushed to nothing — well within whale's time
EAT_BURST_PCT  = 0.55    # flash and shards peak
EAT_FADE_PCT   = 2.5     # everything cleared
BUBBLE_END_PCT = 4.0     # bubbles drift up after burst

FADE_IN_END_PCT = 2.5    # cells respawn from invisible at start of loop

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

# ── row-by-row path, uniform straight segments ────────────────────────────────
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)
path_d = "M " + " L ".join(f"{cx(c):.2f},{cy(r):.2f}" for c, r in path_cells)

def kt(p):    return f"{min(max(p / 100, 0), 1):.5f}"
def kts(*ps): return ";".join(kt(p) for p in ps)

# ── cells ──────────────────────────────────────────────────────────────────────
#
#  Per-cell structure:
#    <g translate(ox,oy)>
#      [glow halo (lvl 4 only)]
#      <rect cell>          — pops 1→1.4 then crushes to 0.02
#      <circle flash>       — white shock-wave radiating outward
#      4 × <rect shard>     — quarters of the cell flying diagonally out
#      2 × <circle bubble>  — slow drift upward after the eating
#    </g>
#
#  No more fly-up.  The cell is DESTROYED IN PLACE.

cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    lvl   = level(count)
    color = LEVELS[lvl]
    ox    = cx(pc)
    oy    = cy(pr)

    t0     = idx / n * 100
    t_jolt = min(t0 + EAT_JOLT_PCT,  99.4)
    t_crush= min(t0 + EAT_CRUSH_PCT, 99.6)
    t_burst= min(t0 + EAT_BURST_PCT, 99.8)
    t_fade = min(t0 + EAT_FADE_PCT,  99.9)
    t_bub  = min(t0 + BUBBLE_END_PCT, 99.95)

    idle_period = round(2.0 + (pc % 4) * 0.5, 1)
    idle_begin  = round(((pc * 7 + pr * 13) % 40) / 10, 1)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # GLOW HALO (level 4 only — pulses, then absorbed at crush)
    if lvl == 4:
        parts.append(f"""
  <rect x="-9" y="-9" width="18" height="18" rx="4" fill="{color}" opacity="0.3">
    <animate attributeName="opacity"
      values="0.28; 0.6; 0.3; 0.6; 0.3; 0"
      keyTimes="0; 0.2; 0.4; 0.6; {kt(min(t_jolt - 0.1, 99))}; {kt(t_crush)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </rect>""")

    # idle gentle pulse + cell rect (NO fly-up — crushes in place)
    parts.append(f"""
  <g>
    <animateTransform attributeName="transform" type="scale"
      values="1;1.05;1" keyTimes="0;0.5;1"
      dur="{idle_period}s" begin="{idle_begin}s" repeatCount="indefinite"/>
    <rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">
      <animateTransform attributeName="transform" type="scale"
        values="1; 1; 1.4; 0.02; 0.02"
        keyTimes="{kts(0, t0, t_jolt, t_crush, t_fade)}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .1 .9 .3 1; .3 0 .7 1; 0 0 1 1"/>""")

    # opacity — with optional respawn fade-in
    if t0 > FADE_IN_END_PCT:
        op_v = "0; 1; 1; 1; 0; 0"
        op_k = kts(0, FADE_IN_END_PCT, t0, t_jolt, t_crush, t_fade)
        op_s = (".4 0 .8 1; 0 0 1 1; 0 0 1 1; .4 0 1 1; 0 0 1 1")
    else:
        op_v = "1; 1; 1; 0; 0"
        op_k = kts(0, t0, t_jolt, t_crush, t_fade)
        op_s = "0 0 1 1; 0 0 1 1; .4 0 1 1; 0 0 1 1"

    parts.append(f"""
      <animate attributeName="opacity"
        values="{op_v}" keyTimes="{op_k}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline" keySplines="{op_s}"/>
    </rect>
  </g>""")

    # FLASH SHOCK-WAVE — white, expands from cell centre
    if t0 > 0.3:
        parts.append(f"""
  <circle cx="0" cy="0" r="0" fill="white">
    <animate attributeName="r"
      values="0; 0; 3; 28; 32"
      keyTimes="{kts(0, t0, t_jolt, t_burst, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .3 0 .8 1; 0 0 1 1"/>
    <animate attributeName="opacity"
      values="0; 0; 0.95; 0.25; 0"
      keyTimes="{kts(0, t0, t_jolt, t_burst, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .3 0 1 1; 0 0 1 1"/>
  </circle>""")

    # SHARDS — 4 colour-matched quarters fly out diagonally
    if t0 > 0.3:
        for dx, dy in [(11, -9), (-11, -9), (12, 9), (-12, 9)]:
            parts.append(f"""
  <rect x="-2" y="-2" width="4" height="4" rx="0.5" fill="{color}" opacity="0">
    <animate attributeName="x"
      values="-2; -2; {dx-2}"
      keyTimes="{kts(0, t_jolt, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .15 .6 .3 1"/>
    <animate attributeName="y"
      values="-2; -2; {dy-2}"
      keyTimes="{kts(0, t_jolt, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .15 .6 .3 1"/>
    <animate attributeName="opacity"
      values="0; 0; 1; 0"
      keyTimes="{kts(0, t_jolt, t_burst, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .4 0 1 1"/>
    <animateTransform attributeName="transform" type="scale"
      values="0; 1; 0.3"
      keyTimes="{kts(t_jolt - 0.05 if t_jolt > 0.05 else 0, t_burst, t_fade)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines=".1 .9 .2 1; .4 0 1 1"/>
  </rect>""")

    # BUBBLES — drift up *after* eating, like digestive burp
    if t0 > 0.5:
        for bx_end, by_end, r_start, b_offset in (
            (-4, -28, 1.7, 0),
            ( 5, -34, 1.4, 0.4),
        ):
            b_start = t_burst + b_offset
            b_peak  = min(b_start + 0.4, 99.5)
            b_end   = min(t_bub + b_offset, 99.95)
            parts.append(f"""
  <circle cx="0" cy="-4" r="0" fill="{WBLUE}">
    <animate attributeName="cx"
      values="0; 0; {bx_end}"
      keyTimes="0; {kt(b_start)}; {kt(b_end)}"
      dur="{DUR}s" repeatCount="indefinite"/>
    <animate attributeName="cy"
      values="-4; -4; {by_end}"
      keyTimes="0; {kt(b_start)}; {kt(b_end)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .2 .1 .25 1"/>
    <animate attributeName="r"
      values="0; {r_start}; 0.2"
      keyTimes="0; {kt(b_start)}; {kt(b_end)}"
      dur="{DUR}s" repeatCount="indefinite"/>
    <animate attributeName="opacity"
      values="0; 0.9; 0"
      keyTimes="0; {kt(b_peak)}; {kt(b_end)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </circle>""")

    parts.append("</g>")
    cells_svg.append("".join(parts))

# ── whale flip keyTimes ────────────────────────────────────────────────────────
def flip_keytimes_and_values():
    flips_t = [0.0]; flips_v = [1]
    total_segs = n - 1
    for r in range(ROWS - 1):
        end_idx   = (r + 1) * COLS - 1
        trans_idx = (r + 1) * COLS
        flips_t.append(end_idx / total_segs); flips_v.append(flips_v[-1])
        flips_t.append(trans_idx / total_segs)
        flips_v.append(1 if (r + 1) % 2 == 0 else -1)
    flips_t.append(1.0); flips_v.append(flips_v[-1])
    return flips_t, flips_v

flip_t, flip_v = flip_keytimes_and_values()
flip_kts  = ";".join(f"{x:.5f}" for x in flip_t)
flip_vals = "; ".join(f"{v} 1" for v in flip_v)

# ── Docker Moby whale symbol ──────────────────────────────────────────────────
#
#  viewBox 0 0 44 24.  Mouth at (42, 16).
#  Body wrapped in a swallow-pulse group that scales (1.05, 0.92) on a 0.55 s
#  loop — synced with the mouth chomp.  Tail flukes stay outside the pulse
#  group (they have their own wag animation).
#
WV, WHV = 44, 24

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WHV}" overflow="visible">

  <!-- UPPER tail fluke (wags) -->
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

  <!-- LOWER tail fluke (wags in sync) -->
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

  <!-- BODY GROUP: scales around (24,14) for swallow-pulse -->
  <g transform="translate(24,14)">
    <animateTransform attributeName="transform" type="scale" additive="sum"
      values="1 1; 1.05 0.92; 1 1"
      keyTimes="0; 0.4; 1"
      dur="0.55s" repeatCount="indefinite"
      calcMode="spline" keySplines=".3 .8 .5 1; .3 .8 .5 1"/>
    <g transform="translate(-24,-14)">

      <!-- body -->
      <ellipse cx="24" cy="14" rx="16" ry="10" fill="{WBLUE}"/>

      <!-- containers -->
      <rect x="13" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
      <rect x="24" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
      <line x1="17.5" y1="2" x2="17.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>
      <line x1="28.5" y1="2" x2="28.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>

      <!-- eye -->
      <circle cx="38"   cy="12" r="2.8" fill="white"/>
      <circle cx="37.5" cy="12" r="1.2" fill="#080d17"/>

      <!-- UPPER JAW (chomp) -->
      <path stroke="#080d17" stroke-width="0.8" fill="#080d17" opacity="0.95"
            d="M37 16 Q40 16 43 16 L42 16 Z">
        <animate attributeName="d"
          values="M37 16 Q40 16 43 16 L42 16 Z;
                  M37 16 Q40 11 43 14 L42 16 Z;
                  M37 16 Q40 16 43 16 L42 16 Z;
                  M37 16 Q40 11 43 14 L42 16 Z;
                  M37 16 Q40 16 43 16 L42 16 Z"
          dur="0.55s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1"/>
      </path>
      <!-- LOWER JAW (chomp) -->
      <path stroke="#080d17" stroke-width="0.8" fill="#080d17" opacity="0.95"
            d="M37 17 Q40 17 43 17 L42 17 Z">
        <animate attributeName="d"
          values="M37 17 Q40 17 43 17 L42 17 Z;
                  M37 17 Q40 22 43 19 L42 17 Z;
                  M37 17 Q40 17 43 17 L42 17 Z;
                  M37 17 Q40 22 43 19 L42 17 Z;
                  M37 17 Q40 17 43 17 L42 17 Z"
          dur="0.55s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1; .3 .8 .5 1"/>
      </path>

      <!-- blow-hole spout -->
      <path d="M21 -1 Q22.5 -6 24 -1 Q25.5 -6 27 -1"
        stroke="{WBLUE}" stroke-width="2.4" fill="none" stroke-linecap="round">
        <animate attributeName="opacity" values="0.5; 1; 0.5" dur="1.1s" repeatCount="indefinite"/>
        <animate attributeName="stroke-width" values="2; 3.6; 2" dur="1.1s" repeatCount="indefinite"/>
      </path>

    </g>
  </g>
</symbol>"""

# Whale glow filter — subtle cyan outer glow so the whale stands out
glow_filter = """<filter id="wglow" x="-30%" y="-30%" width="160%" height="160%">
  <feGaussianBlur stdDeviation="0.9" result="b"/>
  <feMerge>
    <feMergeNode in="b"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>"""

# ── assemble final SVG ─────────────────────────────────────────────────────────
# Use offset positions the MOUTH (viewBox 42, 16) at the path point (0, 0).

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  {whale}
  {glow_filter}
</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>

{"".join(cells_svg)}

<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>

<use href="#wh" width="{WV}" height="{WHV}" x="-42" y="-16" filter="url(#wglow)">
  <animateTransform attributeName="transform" type="scale"
    values="{flip_vals}" keyTimes="{flip_kts}"
    dur="{DUR}s" repeatCount="indefinite" additive="sum"/>
  <animateTransform attributeName="transform" type="translate"
    values="0,-3; 0,3; 0,-3" keyTimes="0;0.5;1"
    dur="1.8s" repeatCount="indefinite" additive="sum"
    calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</use>
</svg>"""

os.makedirs("dist", exist_ok=True)
with open("dist/snake.svg", "w") as f:
    f.write(svg)

print(f"Generated: {W}x{H}px | {n} cells | {DUR}s loop")
