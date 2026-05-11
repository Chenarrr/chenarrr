#!/usr/bin/env python3
"""
Docker Moby-style contribution animation — v6 "smooth bite trail".

The animation keeps the clear consumed-cell trail from v5, then adds a more
polished whale and a controlled crimson bite mark for large contribution days.
The red effect is intentionally limited to high-value cells so it feels like a
reward moment instead of visual noise.
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("GITHUB_USERNAME", "chenarrr")

# ── visuals ────────────────────────────────────────────────────────────────────
BG     = "#070d16"
EMPTY  = "#1e2d45"                                  # what eaten cells become
LEVELS = [EMPTY, "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"
WBLUE2 = "#39B6FF"
INK    = "#08111f"
CRIMSON = "#ff285a"
CRIMSON_DARK = "#9f1239"

CELL  = 11
GAP   = 3
STEP  = CELL + GAP
COLS  = 52
ROWS  = 7
PADX  = 46
PADY  = 56
W     = COLS * STEP + PADX * 2
H     = ROWS * STEP + PADY + 40
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

def bite_splash(lvl, pc, pr, t_pop, t_eat):
    """Return a smooth crimson bite mark for larger contribution cells."""
    if lvl < 3:
        return ""

    angle = ((pc * 19 + pr * 31) % 76) - 38
    mirror = -1 if (pc + pr) % 2 else 1
    tint = CRIMSON if lvl == 4 else "#ef3155"
    tint_dark = CRIMSON_DARK if lvl == 4 else "#881337"
    peak = 0.82 if lvl == 4 else 0.52
    hold = 0.62 if lvl == 4 else 0.34
    t_set = min(t_eat + 1.45, 99.99)
    drop_a = 7 + (pc % 3)
    drop_b = 5 + (pr % 3)
    drop_c = 4 + ((pc + pr) % 3)

    return f"""
  <g filter="url(#crimsonSoft)" opacity="0">
    <animate attributeName="opacity"
      values="0; 0; {peak}; {hold}; {hold}"
      keyTimes="0; {kt(t_pop)}; {kt(t_eat)}; {kt(t_set)}; 1"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline"
      keySplines="0 0 1 1; .08 .8 .2 1; .35 0 .75 1; 0 0 1 1"/>
    <g transform="rotate({angle}) scale({mirror},1)">
      <animateTransform attributeName="transform" type="scale" additive="sum"
        values="0.22; 0.22; 1.24; 1; 1"
        keyTimes="0; {kt(t_pop)}; {kt(t_eat)}; {kt(t_set)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .12 .92 .22 1; .35 0 .75 1; 0 0 1 1"/>
      <path d="M-5 -2 C-11 -6 -13 2 -8 5 C-4 9 2 6 7 8 C11 9 13 5 10 2 C7 -2 0 1 -5 -2 Z"
        fill="{tint}" opacity="0.74"/>
      <path d="M-2 1 C-6 -1 -8 4 -4 6 C0 8 5 5 7 3 C3 4 1 2 -2 1 Z"
        fill="{tint_dark}" opacity="0.45"/>
      <circle cx="{drop_a}" cy="-7" r="2.2" fill="{tint}" opacity="0.7"/>
      <circle cx="-{drop_b}" cy="8" r="1.7" fill="{tint_dark}" opacity="0.58"/>
      <circle cx="{drop_c}" cy="9" r="1.35" fill="{tint}" opacity="0.5"/>
    </g>
  </g>"""

# ── cells ──────────────────────────────────────────────────────────────────────
cells_svg = []

for idx, (pc, pr) in enumerate(path_cells):
    count = lookup.get((pc, pr), 0)
    lvl   = level(count)
    color = LEVELS[lvl]
    is_empty = (lvl == 0)
    ox    = cx(pc)
    oy    = cy(pr)

    # First cell shifted by 0.01% so its keyTimes don't collide with t=0
    t0     = max(idx / n * 100, 0.01)
    # Caps must stay strictly greater than max(t0)=99.725 for monotonic keyTimes
    t_pop  = min(t0 + EAT_POP_PCT,  99.85)
    t_eat  = min(t0 + EAT_EAT_PCT,  99.92)
    t_done = min(t0 + EAT_DONE_PCT, 99.98)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # GLOW HALO — level-4 cells only.  Nested groups:
    #   outer <g> opacity animates 1→0 at eating time (always monotonic)
    #   inner <rect> opacity pulses on its own 2.5 s loop (independent)
    # The two opacities multiply, so the pulse fades out smoothly when eaten.
    if lvl == 4:
        parts.append(f"""
  <g>
    <animate attributeName="opacity"
      values="1; 1; 0"
      keyTimes="0; {kt(t_pop)}; {kt(t_eat)}"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline" keySplines="0 0 1 1; .4 0 1 1"/>
    <rect x="-9" y="-9" width="18" height="18" rx="4" fill="{color}" opacity="0.4">
      <animate attributeName="opacity"
        values="0.3; 0.6; 0.3"
        keyTimes="0; 0.5; 1"
        dur="2.5s" repeatCount="indefinite"
        calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
    </rect>
  </g>""")

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

    # Smooth crimson bite mark for bigger contribution days.
    parts.append(bite_splash(lvl, pc, pr, t_pop, t_eat))

    # SMALL WHITE FLASH at the moment of bite
    if t0 > 0.3:
        f_t0   = t0
        # Caps must be > max t0 (99.725) for monotonic keyTimes
        f_peak = min(t0 + 0.2, 99.88)
        f_end  = min(t0 + 1.5, 99.97)
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
WV, WHV = 62, 38

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WHV}" overflow="visible">
  <ellipse cx="28" cy="33" rx="24" ry="3.2" fill="#020814" opacity="0.36"/>

  <path d="M14 19 L1 8 L5 20 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M14 19 L1 8 L5 20 Z;
              M14 19 L1 4 L5 20 Z;
              M14 19 L1 8 L5 20 Z;
              M14 19 L1 12 L5 20 Z;
              M14 19 L1 8 L5 20 Z"
      dur="0.82s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>
  <path d="M14 22 L1 30 L5 18 Z" fill="{WBLUE}">
    <animate attributeName="d"
      values="M14 22 L1 30 L5 18 Z;
              M14 22 L1 25 L5 18 Z;
              M14 22 L1 30 L5 18 Z;
              M14 22 L1 34 L5 18 Z;
              M14 22 L1 30 L5 18 Z"
      dur="0.82s" repeatCount="indefinite"
      calcMode="spline"
      keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
  </path>

  <g transform="translate(31,21)">
    <animateTransform attributeName="transform" type="scale" additive="sum"
      values="1 1; 1.08 0.91; 1 1"
      keyTimes="0; 0.42; 1"
      dur="0.62s" repeatCount="indefinite"
      calcMode="spline" keySplines=".25 .85 .45 1; .25 .85 .45 1"/>
    <g transform="translate(-31,-21)">
      <path d="M10 22 C11 12 20 7 34 8 C48 9 57 15 58 22 C55 31 43 35 27 33 C17 32 10 28 10 22 Z"
        fill="{WBLUE}"/>
      <path d="M14 25 C23 32 43 32 55 24 C51 32 39 36 26 34 C17 33 12 29 14 25 Z"
        fill="{WBLUE2}" opacity="0.42"/>
      <path d="M16 14 C23 8 39 8 49 13" stroke="#80d9ff" stroke-width="1.6"
        fill="none" opacity="0.6" stroke-linecap="round"/>

      <g opacity="0.96">
        <rect x="18" y="5" width="7" height="6" rx="1.2" fill="#eaf7ff"/>
        <rect x="26" y="5" width="7" height="6" rx="1.2" fill="#eaf7ff"/>
        <rect x="34" y="5" width="7" height="6" rx="1.2" fill="#eaf7ff"/>
        <rect x="22" y="0" width="7" height="6" rx="1.2" fill="#cdefff"/>
        <rect x="30" y="0" width="7" height="6" rx="1.2" fill="#cdefff"/>
        <line x1="21.5" y1="5" x2="21.5" y2="11" stroke="{WBLUE}" stroke-width="1"/>
        <line x1="29.5" y1="5" x2="29.5" y2="11" stroke="{WBLUE}" stroke-width="1"/>
        <line x1="37.5" y1="5" x2="37.5" y2="11" stroke="{WBLUE}" stroke-width="1"/>
      </g>

      <circle cx="49.8" cy="17.2" r="3.1" fill="white"/>
      <circle cx="50.6" cy="17.5" r="1.22" fill="{INK}"/>
      <path d="M46 14 Q50 11 54 14" stroke="{INK}" stroke-width="1.2"
        fill="none" opacity="0.45" stroke-linecap="round"/>

      <path d="M47 21 Q54 20 61 20 L61 22 Q54 22 47 22 Z" fill="{INK}">
        <animate attributeName="d"
          values="M47 21 Q54 20 61 20 L61 22 Q54 22 47 22 Z;
                  M47 21 Q54 14 61 16 L61 22 Q54 22 47 22 Z;
                  M47 21 Q54 20 61 20 L61 22 Q54 22 47 22 Z;
                  M47 21 Q54 14 61 16 L61 22 Q54 22 47 22 Z;
                  M47 21 Q54 20 61 20 L61 22 Q54 22 47 22 Z"
          dur="0.58s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M47 23 Q54 24 61 24 L61 22 Q54 22 47 22 Z" fill="{INK}">
        <animate attributeName="d"
          values="M47 23 Q54 24 61 24 L61 22 Q54 22 47 22 Z;
                  M47 23 Q54 30 61 27 L61 22 Q54 22 47 22 Z;
                  M47 23 Q54 24 61 24 L61 22 Q54 22 47 22 Z;
                  M47 23 Q54 30 61 27 L61 22 Q54 22 47 22 Z;
                  M47 23 Q54 24 61 24 L61 22 Q54 22 47 22 Z"
          dur="0.58s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M55 22 L58 23 L55 24 Z" fill="#f7fbff" opacity="0.86">
        <animate attributeName="opacity" values="0.25; 0.86; 0.25" dur="0.58s" repeatCount="indefinite"/>
      </path>

      <path d="M29 -1 C28 -6 33 -6 32 -1 C33 -7 39 -5 36 0"
        stroke="#96e7ff" stroke-width="2.2" fill="none" stroke-linecap="round">
        <animate attributeName="d"
          values="M29 -1 C28 -6 33 -6 32 -1 C33 -7 39 -5 36 0;
                  M28 -1 C24 -9 34 -9 32 -1 C35 -10 43 -5 37 0;
                  M29 -1 C28 -6 33 -6 32 -1 C33 -7 39 -5 36 0"
          dur="1.25s" repeatCount="indefinite"
          calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
        <animate attributeName="opacity" values="0.45; 1; 0.45" dur="1.25s" repeatCount="indefinite"/>
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

crimson_filter = """<filter id="crimsonSoft" x="-90%" y="-90%" width="280%" height="280%">
  <feGaussianBlur stdDeviation="0.35" result="soft"/>
  <feMerge>
    <feMergeNode in="soft"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>"""

# ── assemble SVG ───────────────────────────────────────────────────────────────
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
  viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  {whale}
  {glow_filter}
  {crimson_filter}
</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>

{"".join(cells_svg)}

<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>

<use href="#wh" width="{WV}" height="{WHV}" x="-60" y="-24" filter="url(#wglow)">
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
