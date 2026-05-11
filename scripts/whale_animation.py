#!/usr/bin/env python3
"""
Docker Moby whale contribution animation — v5 "real eating, clear trail".

The key fix from v4: eaten cells transition to the EMPTY-cell colour
(#1e2d45) instead of going to opacity 0.  Just like the original snake
animation, this leaves a clearly visible trail of consumed contributions
behind the whale, so you can SEE what's been eaten.

Stripped most visual noise (shards, bubbles, shock-wave) — they were
drowning out the actual eating.  Kept only what makes the bite obvious:
  • cell pops to 1.4× briefly when bitten
  • fill colour transitions to empty (visible trail)
  • small white flash at the bite moment
  • everything else (whale flips, jaws, tail wag, body swallow, glow) stays
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("USERNAME", "chenarrr")

# ── visuals ────────────────────────────────────────────────────────────────────
BG     = "#090f1a"
EMPTY  = "#1e2d45"                                  # what eaten cells become
LEVELS = [EMPTY, "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
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
DUR   = 50           # slightly slower so eating is more readable
HALF  = CELL / 2

# Eating phases (% of DUR) — tight, all within whale's mouth window
EAT_POP_PCT   = 0.10  # cell starts popping
EAT_EAT_PCT   = 0.30  # peak pop, colour transitions
EAT_DONE_PCT  = 0.55  # back to normal size, fully empty colour

FADE_IN_END_PCT = 2.0  # respawn colour fade at start of loop

# ── fetch contributions ────────────────────────────────────────────────────────
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

# ── path ───────────────────────────────────────────────────────────────────────
path_cells = []
for ri in range(ROWS):
    cols = range(COLS) if ri % 2 == 0 else range(COLS - 1, -1, -1)
    path_cells.extend((ci, ri) for ci in cols)

n = len(path_cells)
path_d = "M " + " L ".join(f"{cx(c):.2f},{cy(r):.2f}" for c, r in path_cells)

def kt(p):    return f"{min(max(p / 100, 0), 1):.5f}"
def kts(*ps): return ";".join(kt(p) for p in ps)

# ── cells ──────────────────────────────────────────────────────────────────────
cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    lvl   = level(count)
    color = LEVELS[lvl]
    is_empty = (lvl == 0)
    ox    = cx(pc)
    oy    = cy(pr)

    t0     = idx / n * 100
    # Caps must stay strictly greater than max(t0)=99.725 for monotonic keyTimes
    t_pop  = min(t0 + EAT_POP_PCT,  99.85)
    t_eat  = min(t0 + EAT_EAT_PCT,  99.92)
    t_done = min(t0 + EAT_DONE_PCT, 99.98)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # GLOW HALO — only on level-4 cells with enough room for pulse before eating
    if lvl == 4 and t0 > 0.8:
        # last pulse keyTime is 0.6 — t_pop must be > that for monotonicity
        t_glow_fade = max(t_pop - 0.05, 0.65)
        parts.append(f"""
  <rect x="-9" y="-9" width="18" height="18" rx="4" fill="{color}" opacity="0.3">
    <animate attributeName="opacity"
      values="0.25; 0.55; 0.3; 0.55; 0.25; 0"
      keyTimes="0; 0.2; 0.4; 0.6; {kt(t_glow_fade)}; {kt(t_eat)}"
      dur="{DUR}s" repeatCount="indefinite"/>
  </rect>""")

    # ── cell rect ────────────────────────────────────────────────────────────
    # Two animations:
    #   1. scale  — pop 1 → 1.4 → 1 (the "bite" motion)
    #   2. fill   — colour → EMPTY (the trail of consumed cells)

    # idle pulse only on non-empty cells (empty cells stay static)
    idle_open = idle_close = ""
    if not is_empty:
        idle_period = round(2.2 + (pc % 4) * 0.4, 1)
        idle_begin  = round(((pc * 7 + pr * 13) % 40) / 10, 1)
        idle_open = f"""
  <g>
    <animateTransform attributeName="transform" type="scale"
      values="1;1.05;1" keyTimes="0;0.5;1"
      dur="{idle_period}s" begin="{idle_begin}s" repeatCount="indefinite"/>"""
        idle_close = "</g>"

    parts.append(f"""{idle_open}
    <rect x="-{HALF}" y="-{HALF}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">
      <animateTransform attributeName="transform" type="scale"
        values="1; 1; 1.45; 1; 1"
        keyTimes="{kts(0, t0, t_pop, t_eat, t_done)}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .1 .9 .3 1; .3 0 .7 1; 0 0 1 1"/>""")

    # fill colour change — only meaningful for non-empty cells.
    # For non-empty cells with t0 > fade-in window, the cell colour fades back
    # from EMPTY → its level colour at the start of each loop (respawn).
    if not is_empty:
        if t0 > FADE_IN_END_PCT:
            parts.append(f"""
      <animate attributeName="fill"
        values="{EMPTY}; {color}; {color}; {color}; {EMPTY}; {EMPTY}"
        keyTimes="0; {kt(FADE_IN_END_PCT)}; {kt(t0)}; {kt(t_pop)}; {kt(t_eat)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines=".4 0 .8 1; 0 0 1 1; 0 0 1 1; .2 0 .8 1; 0 0 1 1"/>""")
        else:
            parts.append(f"""
      <animate attributeName="fill"
        values="{color}; {color}; {color}; {EMPTY}; {EMPTY}"
        keyTimes="0; {kt(t0)}; {kt(t_pop)}; {kt(t_eat)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; 0 0 1 1; .2 0 .8 1; 0 0 1 1"/>""")

    parts.append(f"    </rect>{idle_close}")

    # SMALL WHITE FLASH at the moment of bite
    if t0 > 0.3:
        f_t0   = t0
        f_peak = min(t0 + 0.2, 99.4)
        f_end  = min(t0 + 1.5, 99.8)
        parts.append(f"""
  <circle cx="0" cy="0" r="0" fill="white">
    <animate attributeName="r"
      values="0; 0; 3; 14"
      keyTimes="0; {kt(f_t0)}; {kt(f_peak)}; {kt(f_end)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .3 0 .8 1"/>
    <animate attributeName="opacity"
      values="0; 0; 0.85; 0"
      keyTimes="0; {kt(f_t0)}; {kt(f_peak)}; {kt(f_end)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .1 .9 .2 1; .3 0 1 1"/>
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

# ── Docker Moby whale ─────────────────────────────────────────────────────────
WV, WHV = 44, 24

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WHV}" overflow="visible">
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
  <g transform="translate(24,14)">
    <animateTransform attributeName="transform" type="scale" additive="sum"
      values="1 1; 1.05 0.92; 1 1"
      keyTimes="0; 0.4; 1"
      dur="0.55s" repeatCount="indefinite"
      calcMode="spline" keySplines=".3 .8 .5 1; .3 .8 .5 1"/>
    <g transform="translate(-24,-14)">
      <ellipse cx="24" cy="14" rx="16" ry="10" fill="{WBLUE}"/>
      <rect x="13" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
      <rect x="24" y="2" width="9" height="9" rx="2" fill="white" opacity="0.94"/>
      <line x1="17.5" y1="2" x2="17.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>
      <line x1="28.5" y1="2" x2="28.5" y2="11" stroke="{WBLUE}" stroke-width="1.2"/>
      <circle cx="38"   cy="12" r="2.8" fill="white"/>
      <circle cx="37.5" cy="12" r="1.2" fill="#080d17"/>
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
      <path d="M21 -1 Q22.5 -6 24 -1 Q25.5 -6 27 -1"
        stroke="{WBLUE}" stroke-width="2.4" fill="none" stroke-linecap="round">
        <animate attributeName="opacity" values="0.5; 1; 0.5" dur="1.1s" repeatCount="indefinite"/>
        <animate attributeName="stroke-width" values="2; 3.6; 2" dur="1.1s" repeatCount="indefinite"/>
      </path>
    </g>
  </g>
</symbol>"""

glow_filter = """<filter id="wglow" x="-30%" y="-30%" width="160%" height="160%">
  <feGaussianBlur stdDeviation="0.9" result="b"/>
  <feMerge>
    <feMergeNode in="b"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>"""

# ── assemble SVG ───────────────────────────────────────────────────────────────
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
