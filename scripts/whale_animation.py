#!/usr/bin/env python3
"""
Docker Moby-style contribution animation — v13 "polished tiny Moby".

The animation keeps the clear consumed-cell trail from v5, then adds a more
Docker-like Moby silhouette and a controlled crimson bite splash for large
contribution days. Eaten cells now linger for a few whale steps before fading
smoothly into the darker trail, so the wake feels less snappy.
"""

import os, json, urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
USER  = os.environ.get("GITHUB_USERNAME", "chenarrr")

# ── visuals ────────────────────────────────────────────────────────────────────
BG     = "#070d16"
EMPTY  = "#1e2d45"
TRAIL  = "#1a2840"                                  # soft in-between shade for the wake
EATEN  = "#141f33"                                  # darker trail after the whale passes
LEVELS = [EMPTY, "#0e4d8a", "#0077b6", "#0096c7", "#00D4FF"]
WBLUE  = "#2496ED"
WBLUE2 = "#18B8EF"
WBLUE3 = "#0A7FC2"
INK    = "#08111f"
OUTLINE = "#073553"
BELLY = "#83d2f4"
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
EAT_DONE_PCT  = 0.68  # back to normal size after a softer chew

TRAIL_HOLD_CELLS = 1.35  # keep the bitten block bright just behind the whale
TRAIL_SOFT_CELLS = 2.25  # fade through the middle shade
TRAIL_DARK_CELLS = 3.10  # fully dark after about three more blocks

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
PATH_STEP_PCT = 100 / n
path_d = "M " + " L ".join(f"{cx(c):.2f},{cy(r):.2f}" for c, r in path_cells)

def kt(p):    return f"{min(max(p / 100, 0), 1):.5f}"
def kts(*ps): return ";".join(kt(p) for p in ps)

def trail_times(t_eat):
    """Return delayed trail keyframes so a 3-cell wake follows the whale."""
    t_hold = min(t_eat + PATH_STEP_PCT * TRAIL_HOLD_CELLS, 99.935)
    t_soft = min(t_eat + PATH_STEP_PCT * TRAIL_SOFT_CELLS, 99.965)
    t_dark = min(t_eat + PATH_STEP_PCT * TRAIL_DARK_CELLS, 99.990)
    return t_hold, t_soft, t_dark

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
    t_hold, t_soft, t_dark = trail_times(t_eat)

    parts = [f'<g transform="translate({ox:.2f},{oy:.2f})">']

    # GLOW HALO — level-4 cells only.  Nested groups:
    #   outer <g> opacity trails 1→0 after the whale has moved on
    #   inner <rect> opacity pulses on its own 2.5 s loop (independent)
    # The two opacities multiply, so the pulse fades out smoothly when eaten.
    if lvl == 4:
        parts.append(f"""
  <g>
    <animate attributeName="opacity"
      values="1; 1; 1; 0.45; 0; 0"
      keyTimes="0; {kt(t_pop)}; {kt(t_hold)}; {kt(t_soft)}; {kt(t_dark)}; 1"
      dur="{DUR}s" repeatCount="indefinite"
      calcMode="spline"
      keySplines="0 0 1 1; 0 0 1 1; .25 0 .65 1; .35 0 .8 1; 0 0 1 1"/>
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
    #   1. scale  — pop 1 → 1.36 → 1 (the "bite" motion)
    #   2. fill   — colour → TRAIL → EATEN (a delayed 3-cell wake)

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
        values="1; 1; 1.36; 1.03; 1"
        keyTimes="{kts(0, t0, t_pop, t_eat, t_done)}"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; .12 .88 .28 1; .22 0 .62 1; .25 0 .7 1"/>""")

    # fill colour change — only meaningful for non-empty cells.
    # For non-empty cells with t0 > fade-in window, the cell colour fades back
    # from EATEN → its level colour at the start of each loop (respawn).
    if not is_empty:
        if t0 > FADE_IN_END_PCT:
            parts.append(f"""
      <animate attributeName="fill"
        values="{EATEN}; {color}; {color}; {color}; {color}; {color}; {TRAIL}; {EATEN}; {EATEN}"
        keyTimes="0; {kt(FADE_IN_END_PCT)}; {kt(t0)}; {kt(t_pop)}; {kt(t_eat)}; {kt(t_hold)}; {kt(t_soft)}; {kt(t_dark)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines=".4 0 .8 1; 0 0 1 1; 0 0 1 1; 0 0 1 1; 0 0 1 1; .25 0 .65 1; .35 0 .8 1; 0 0 1 1"/>""")
        else:
            parts.append(f"""
      <animate attributeName="fill"
        values="{color}; {color}; {color}; {color}; {color}; {TRAIL}; {EATEN}; {EATEN}"
        keyTimes="0; {kt(t0)}; {kt(t_pop)}; {kt(t_eat)}; {kt(t_hold)}; {kt(t_soft)}; {kt(t_dark)}; 1"
        dur="{DUR}s" repeatCount="indefinite"
        calcMode="spline"
        keySplines="0 0 1 1; 0 0 1 1; 0 0 1 1; 0 0 1 1; .25 0 .65 1; .35 0 .8 1; 0 0 1 1"/>""")

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
WV, WHV = 100, 72
W_RENDER, H_RENDER = 52, 38

def _container(x, y, fill):
    """One cargo container: crisp box with two plank lines, Docker-logo style."""
    return f"""
        <rect x="{x}" y="{y}" width="13" height="10" rx="1" fill="{fill}"
          stroke="{OUTLINE}" stroke-width="1.7" stroke-linejoin="round"/>
        <line x1="{x + 4.33:.2f}" y1="{y + 1.2}" x2="{x + 4.33:.2f}" y2="{y + 8.8}"
          stroke="{OUTLINE}" stroke-width="1" opacity="0.75"/>
        <line x1="{x + 8.66:.2f}" y1="{y + 1.2}" x2="{x + 8.66:.2f}" y2="{y + 8.8}"
          stroke="{OUTLINE}" stroke-width="1" opacity="0.75"/>"""

container_rows = f"""
      <g transform="rotate(-3 50 25)">
{_container(44, 12.5, WBLUE2)}{_container(58, 12.5, WBLUE2)}
{_container(30, 24, "#10A3DE")}{_container(44, 24, "#10A3DE")}{_container(58, 24, "#10A3DE")}
      </g>
"""

whale = f"""<symbol id="wh" viewBox="0 0 {WV} {WHV}" overflow="visible">
  <ellipse cx="45" cy="66" rx="31" ry="4.2" fill="#020814" opacity="0.2"/>

  <g transform="translate(48,45)">
    <animateTransform attributeName="transform" type="scale" additive="sum"
      values="1 1; 1.015 0.985; 1 1"
      keyTimes="0; 0.42; 1"
      dur="1.15s" repeatCount="indefinite"
      calcMode="spline" keySplines=".25 .85 .45 1; .25 .85 .45 1"/>
    <g transform="translate(-48,-45)">
      <path d="M22 42 C15 32 8 29 3 20 C13 19 22 26 27 37 Z"
        fill="{WBLUE}" stroke="{OUTLINE}" stroke-width="3" stroke-linejoin="round">
        <animate attributeName="d"
          values="M22 42 C15 32 8 29 3 20 C13 19 22 26 27 37 Z;
                  M22 42 C14 29 8 25 4 16 C15 17 24 26 27 37 Z;
                  M22 42 C15 32 8 29 3 20 C13 19 22 26 27 37 Z;
                  M22 42 C14 45 8 50 3 58 C15 58 24 49 27 37 Z;
                  M22 42 C15 32 8 29 3 20 C13 19 22 26 27 37 Z"
          dur="0.86s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
      </path>
      <path d="M24 43 C18 51 11 56 4 66 C17 66 27 55 29 43 Z"
        fill="{WBLUE2}" stroke="{OUTLINE}" stroke-width="3" stroke-linejoin="round">
        <animate attributeName="d"
          values="M24 43 C18 51 11 56 4 66 C17 66 27 55 29 43 Z;
                  M24 43 C17 48 11 50 5 58 C16 60 25 53 29 43 Z;
                  M24 43 C18 51 11 56 4 66 C17 66 27 55 29 43 Z;
                  M24 43 C17 57 10 62 4 69 C18 69 28 57 29 43 Z;
                  M24 43 C18 51 11 56 4 66 C17 66 27 55 29 43 Z"
          dur="0.86s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".4 0 .6 1; .4 0 .6 1; .4 0 .6 1; .4 0 .6 1"/>
      </path>

      <path d="M22 49 C22 32 38 24 59 25 C80 26 95 38 96 51 C95 64 78 71 55 69 C35 68 22 60 22 49 Z"
        fill="{WBLUE}" stroke="{OUTLINE}" stroke-width="3" stroke-linejoin="round"/>
      <path d="M30 56 C42 66 74 66 93 53 C87 65 70 72 53 70 C39 69 30 62 30 56 Z"
        fill="{BELLY}" opacity="0.82"/>
      <path d="M31 56 C44 64 74 64 91 54" stroke="#5bbfe8" stroke-width="1.5"
        fill="none" opacity="0.65" stroke-linecap="round"/>

{container_rows}

      <g transform="translate(62,47)">
        <ellipse cx="0" cy="0" rx="7.7" ry="7.7" fill="#f7fbff" stroke="{OUTLINE}" stroke-width="1.9">
          <animate attributeName="ry"
            values="7.7; 7.7; 0.9; 7.7; 7.7"
            keyTimes="0; 0.78; 0.82; 0.87; 1"
            dur="3.8s" repeatCount="indefinite"
            calcMode="spline"
            keySplines="0 0 1 1; .2 .8 .3 1; .2 0 .8 1; 0 0 1 1"/>
        </ellipse>
        <g>
          <animateTransform attributeName="transform" type="scale"
            values="1 1; 1 1; 1 0.14; 1 1; 1 1"
            keyTimes="0; 0.78; 0.82; 0.87; 1"
            dur="3.8s" repeatCount="indefinite"
            calcMode="spline"
            keySplines="0 0 1 1; .2 .8 .3 1; .2 0 .8 1; 0 0 1 1"/>
          <circle cx="3" cy="2.3" r="3" fill="{INK}"/>
          <circle cx="1.8" cy="1" r="1.05" fill="#f7fbff" opacity="0.95"/>
        </g>
      </g>
      <circle cx="77" cy="54.5" r="2.4" fill="#ff9fba" opacity="0.66"/>

      <path d="M76 55 C82 61 90 61 95 55" stroke="{OUTLINE}" stroke-width="2"
        fill="none" stroke-linecap="round">
        <animate attributeName="d"
          values="M76 55 C82 61 90 61 95 55;
                  M76 55 C83 62.5 91.5 62 95.5 56.5;
                  M76 55 C82 61 90 61 95 55;
                  M76 55 C83 62.5 91.5 62 95.5 56.5;
                  M76 55 C82 61 90 61 95 55"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <ellipse cx="86.5" cy="58.2" rx="2.7" ry="0.45" fill="#2b1020" opacity="0.16">
        <animate attributeName="ry"
          values="0.35; 1.15; 0.35; 1.15; 0.35"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
        <animate attributeName="rx"
          values="2.5; 3.25; 2.5; 3.25; 2.5"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
        <animate attributeName="opacity"
          values="0.14; 0.42; 0.14; 0.42; 0.14"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </ellipse>
      <path d="M88 56.2 L90.2 56.4 L89.2 58.3 Z" fill="#fff7fb" opacity="0.2">
        <animate attributeName="opacity"
          values="0.18; 0.62; 0.18; 0.62; 0.18"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M84.8 59.1 C86.7 60.1 89 59.8 90.5 58.6" stroke="#ff8fab" stroke-width="1.05"
        fill="none" stroke-linecap="round" opacity="0.34">
        <animate attributeName="d"
          values="M84.8 59.1 C86.7 60.1 89 59.8 90.5 58.6;
                  M84.5 59.5 C86.8 60.6 90 60.1 91.4 58.8;
                  M84.8 59.1 C86.7 60.1 89 59.8 90.5 58.6;
                  M84.5 59.5 C86.8 60.6 90 60.1 91.4 58.8;
                  M84.8 59.1 C86.7 60.1 89 59.8 90.5 58.6"
          dur="1.05s" repeatCount="indefinite"
          calcMode="spline"
          keySplines=".22 .86 .38 1; .28 0 .72 1; .22 .86 .38 1; .28 0 .72 1"/>
      </path>
      <path d="M79 61 C84 64 91 63.5 94 60" stroke="#4fbce7" stroke-width="1.05"
        fill="none" stroke-linecap="round" opacity="0.26"/>

      <path d="M44 13 C43 5 51 5 50 13 C55 3 64 8 57 16"
        transform="translate(31,7)"
        stroke="#bff3ff" stroke-width="2.6" fill="none" stroke-linecap="round">
        <animate attributeName="d"
          values="M44 13 C43 5 51 5 50 13 C55 3 64 8 57 16;
                  M43 13 C38 1 53 1 50 13 C58 0 69 8 58 16;
                  M44 13 C43 5 51 5 50 13 C55 3 64 8 57 16"
          dur="1.25s" repeatCount="indefinite"
          calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
        <animate attributeName="opacity" values="0.45; 1; 0.45" dur="1.25s" repeatCount="indefinite"/>
      </path>
    </g>
  </g>
</symbol>"""

glow_filter = """<filter id="wglow" x="-30%" y="-30%" width="160%" height="160%">
  <feGaussianBlur stdDeviation="0.55" result="b"/>
  <feMerge>
    <feMergeNode in="b"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>"""

shadow_filter = """<filter id="whaleShadow" x="-90%" y="-90%" width="280%" height="280%">
  <feGaussianBlur stdDeviation="1.7" result="softShadow"/>
  <feMerge>
    <feMergeNode in="softShadow"/>
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
  {shadow_filter}
  {crimson_filter}
</defs>
<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>

{"".join(cells_svg)}

<path id="wp" d="{path_d}" fill="none" visibility="hidden"/>

<g opacity="0.9">
  <ellipse cx="-31" cy="8.8" rx="21" ry="5.2" fill="#02050d" opacity="0.62" filter="url(#whaleShadow)">
    <animate attributeName="rx" values="19.5; 21.5; 19.5" keyTimes="0;0.5;1"
      dur="1.8s" repeatCount="indefinite"
      calcMode="spline" keySplines=".4 0 .6 1; .4 0 .6 1"/>
  </ellipse>
  <ellipse cx="-31" cy="8.2" rx="14.5" ry="2.35" fill="#000207" opacity="0.42"/>
  <animateMotion dur="{DUR}s" repeatCount="indefinite" calcMode="linear">
    <mpath href="#wp"/>
  </animateMotion>
</g>

<use href="#wh" width="{W_RENDER}" height="{H_RENDER}" x="-51" y="-30" filter="url(#wglow)">
  <animateTransform attributeName="transform" type="scale"
    values="{flip_vals}" keyTimes="{flip_kts}"
    dur="{DUR}s" repeatCount="indefinite" additive="sum"/>
  <animateTransform attributeName="transform" type="translate"
    values="0,-0.9; 0,1.1; 0,-0.9" keyTimes="0;0.5;1"
    dur="2.4s" repeatCount="indefinite" additive="sum"
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
