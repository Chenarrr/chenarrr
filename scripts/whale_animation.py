#!/usr/bin/env python3
"""
Docker Moby-style contribution animation — v7 "Moby bite fade".

The animation keeps the clear consumed-cell trail from v5, then adds a more
Docker-like Moby silhouette and a controlled crimson bite splash for large
contribution days. The red effect blooms at the bite moment, then fades away
smoothly so the graph stays readable.
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("GITHUB_USERNAME", "chenarrr")

# ── visuals ────────────────────────────────────────────────────────────────────
BG     = "#070d16"
EMPTY  = "#1e2d45"                                  # what eaten cells become
LEVELS = [EMPTY, "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"
WBLUE2 = "#5EC9FF"
WBLUE3 = "#0db7ed"
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
    """Return a crimson bite splash that appears, drifts, and fades away."""
    if lvl < 3:
        return ""

    angle = ((pc * 19 + pr * 31) % 76) - 38
    mirror = -1 if (pc + pr) % 2 else 1
    tint = CRIMSON if lvl == 4 else "#ef3155"
    tint_dark = CRIMSON_DARK if lvl == 4 else "#881337"
    peak = 0.78 if lvl == 4 else 0.5
    drift = 0.32 if lvl == 4 else 0.18
    t_drift = min(t_eat + 1.45, 99.965)
    t_fade = min(t_eat + 5.25, 99.995)
    drop_a = 7 + (pc % 3)
    drop_b = 5 + (pr % 3)
    drop_c = 4 + ((pc + pr) % 3)

    return f"""
  <g filter="url(#crimsonSoft)" opacity="0">
    <animate attributeName="opacity"
      values="0; 0; {peak}; {drift}; 0; 0"
      keyTimes="0; {kt(t_pop)}; {kt(t_eat)}; {kt(t_drift)}; {kt(t_fade)}; 1"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline"
      keySplines="0 0 1 1; .08 .8 .2 1; .2 0 .6 1; .35 0 .8 1; 0 0 1 1"/>
    <g transform="rotate({angle}) scale({mirror},1)">
      <animateTransform attributeName="transform" type="scale" additive="sum"
        values="0.14; 0.14; 1.22; 1.06; 0.72; 0.72"
        keyTimes="0; {kt(t_pop)}; {kt(t_eat)}; {kt(t_drift)}; {kt(t_fade)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .1 .92 .22 1; .25 0 .65 1; .35 0 .8 1; 0 0 1 1"/>
      <animateTransform attributeName="transform" type="translate" additive="sum"
        values="0 0; 0 0; 0 0; {mirror * 2.4:.1f} -1.8; {mirror * 4.2:.1f} -4.8; {mirror * 4.2:.1f} -4.8"
        keyTimes="0; {kt(t_pop)}; {kt(t_eat)}; {kt(t_drift)}; {kt(t_fade)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .1 .92 .22 1; .25 0 .65 1; .35 0 .8 1; 0 0 1 1"/>
      <path d="M-5 -2 C-10 -5 -13 1 -9 4 C-5 8 1 5 6 7 C10 8 12 4 9 1 C6 -2 0 1 -5 -2 Z"
        fill="{tint}" opacity="0.66"/>
      <path d="M-2 1 C-6 -1 -8 4 -4 6 C0 8 4 5 7 3 C3 4 1 2 -2 1 Z"
        fill="{tint_dark}" opacity="0.34"/>
      <circle cx="{drop_a}" cy="-7" r="2" fill="{tint}" opacity="0.54"/>
      <circle cx="-{drop_b}" cy="8" r="1.55" fill="{tint_dark}" opacity="0.42"/>
      <circle cx="{drop_c}" cy="9" r="1.25" fill="{tint}" opacity="0.36"/>
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
WV, WHV = 90, 58
W_RENDER, H_RENDER = 76, 49

container_rows = f"""
      <g fill="#dff7ff" stroke="#0b8fca" stroke-width="1.15" opacity="0.98">
        <rect x="28" y="16" width="9" height="8" rx="1.2"/>
        <rect x="38" y="16" width="9" height="8" rx="1.2"/>
        <rect x="48" y="16" width="9" height="8" rx="1.2"/>
        <rect x="58" y="16" width="9" height="8" rx="1.2"/>

        <rect x="23" y="25" width="9" height="8" rx="1.2"/>
        <rect x="33" y="25" width="9" height="8" rx="1.2"/>
        <rect x="43" y="25" width="9" height="8" rx="1.2"/>
        <rect x="53" y="25" width="9" height="8" rx="1.2"/>
        <rect x="63" y="25" width="9" height="8" rx="1.2"/>

        <rect x="38" y="7" width="9" height="8" rx="1.2"/>
      </g>
      <g stroke="{WBLUE}" stroke-width="0.9" opacity="0.72">
        <line x1="32.5" y1="16" x2="32.5" y2="24"/>
        <line x1="42.5" y1="16" x2="42.5" y2="24"/>
        <line x1="52.5" y1="16" x2="52.5" y2="24"/>
        <line x1="62.5" y1="16" x2="62.5" y2="24"/>
        <line x1="27.5" y1="25" x2="27.5" y2="33"/>
        <line x1="37.5" y1="25" x2="37.5" y2="33"/>
        <line x1="47.5" y1="25" x2="47.5" y2="33"/>
        <line x1="57.5" y1="25" x2="57.5" y2="33"/>
        <line x1="67.5" y1="25" x2="67.5" y2="33"/>
        <line x1="42.5" y1="7" x2="42.5" y2="15"/>
      </g>
"""

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WHV}" overflow="visible">
  <ellipse cx="43" cy="52" rx="34" ry="4.2" fill="#020814" opacity="0.34"/>

  <g transform="translate(45,35)">
    <animateTransform attributeName="transform" type="scale" additive="sum"
      values="1 1; 1.035 0.965; 1 1"
      keyTimes="0; 0.42; 1"
      dur="0.7s" repeatCount="indefinite"
      calcMode="spline" keySplines=".25 .85 .45 1; .25 .85 .45 1"/>
    <g transform="translate(-45,-35)">
      <path d="M20 36 C13 29 7 27 1 21 C11 20 18 25 24 31 Z"
        fill="{WBLUE}">
        <animate attributeName="d"
          values="M20 36 C13 29 7 27 1 21 C11 20 18 25 24 31 Z;
                  M20 36 C12 26 6 22 1 15 C12 17 20 25 24 31 Z;
                  M20 36 C13 29 7 27 1 21 C11 20 18 25 24 31 Z;
                  M20 36 C12 32 7 36 1 41 C11 42 19 37 24 31 Z;
                  M20 36 C13 29 7 27 1 21 C11 20 18 25 24 31 Z"
          dur="0.86s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
      </path>
      <path d="M20 39 C13 45 7 47 1 53 C12 53 19 47 24 42 Z"
        fill="{WBLUE3}" opacity="0.94">
        <animate attributeName="d"
          values="M20 39 C13 45 7 47 1 53 C12 53 19 47 24 42 Z;
                  M20 39 C13 42 7 42 1 47 C11 49 18 46 24 42 Z;
                  M20 39 C13 45 7 47 1 53 C12 53 19 47 24 42 Z;
                  M20 39 C12 50 7 53 1 57 C13 57 21 49 24 42 Z;
                  M20 39 C13 45 7 47 1 53 C12 53 19 47 24 42 Z"
          dur="0.86s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
      </path>

      <path d="M17 41 C18 27 33 19 55 20 C73 21 86 30 88 42 C83 52 65 57 43 55 C27 54 17 49 17 41 Z"
        fill="{WBLUE}"/>
      <path d="M21 44 C33 54 64 53 84 42 C78 53 61 58 42 56 C28 54 21 49 21 44 Z"
        fill="{WBLUE2}" opacity="0.5"/>
      <path d="M22 36 C30 23 48 20 66 24" stroke="#9de8ff" stroke-width="2"
        fill="none" opacity="0.7" stroke-linecap="round"/>

{container_rows}

      <circle cx="75" cy="35" r="3.2" fill="#f6fbff"/>
      <circle cx="76.1" cy="35.4" r="1.22" fill="{INK}"/>
      <path d="M70 31 Q75 27 80 31" stroke="{INK}" stroke-width="1.25"
        fill="none" opacity="0.38" stroke-linecap="round"/>

      <path d="M75 42 Q82 41 90 41 L90 43 Q82 43 75 43 Z" fill="{INK}">
        <animate attributeName="d"
          values="M75 42 Q82 41 90 41 L90 43 Q82 43 75 43 Z;
                  M75 42 Q82 34 90 36 L90 43 Q82 43 75 43 Z;
                  M75 42 Q82 41 90 41 L90 43 Q82 43 75 43 Z;
                  M75 42 Q82 34 90 36 L90 43 Q82 43 75 43 Z;
                  M75 42 Q82 41 90 41 L90 43 Q82 43 75 43 Z"
          dur="0.6s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M75 44 Q82 45 90 45 L90 43 Q82 43 75 43 Z" fill="{INK}">
        <animate attributeName="d"
          values="M75 44 Q82 45 90 45 L90 43 Q82 43 75 43 Z;
                  M75 44 Q82 51 90 49 L90 43 Q82 43 75 43 Z;
                  M75 44 Q82 45 90 45 L90 43 Q82 43 75 43 Z;
                  M75 44 Q82 51 90 49 L90 43 Q82 43 75 43 Z;
                  M75 44 Q82 45 90 45 L90 43 Q82 43 75 43 Z"
          dur="0.6s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M85 43 L88 44 L85 45 Z" fill="#f7fbff" opacity="0.82">
        <animate attributeName="opacity" values="0.22; 0.82; 0.22" dur="0.6s" repeatCount="indefinite"/>
      </path>

      <path d="M43 5 C42 -1 48 -1 47 5 C50 -3 57 1 52 7"
        stroke="#bff3ff" stroke-width="2.4" fill="none" stroke-linecap="round">
        <animate attributeName="d"
          values="M43 5 C42 -1 48 -1 47 5 C50 -3 57 1 52 7;
                  M42 5 C37 -5 50 -4 47 5 C53 -6 62 0 53 7;
                  M43 5 C42 -1 48 -1 47 5 C50 -3 57 1 52 7"
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

<use href="#wh" width="{W_RENDER}" height="{H_RENDER}" x="-74" y="-36" filter="url(#wglow)">
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
