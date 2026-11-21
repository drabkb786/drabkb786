#!/usr/bin/env python3
"""Build self-contained profile cards from public GitHub data. Python stdlib only."""

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import textwrap
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BG, PANEL, INK, MUTED = "#0B1120", "#111827", "#E5E7EB", "#94A3B8"
EDGE, GREEN, CYAN, PURPLE = "#263447", "#34D399", "#22D3EE", "#A78BFA"
LEVELS = ["#1D2939", "#164B40", "#1E8061", "#25B582", GREEN]


def esc(value):
    return html.escape(str(value), quote=True)


def text(x, y, value, size=16, color=INK, weight=400, extra=""):
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}" {extra}>{esc(value)}</text>'
    )


def rect(x, y, w, h, fill=PANEL, radius=10, stroke=None, extra=""):
    border = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}"{border} {extra}/>'
    )


def svg(width, height, title, parts, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">'
        f'<title>{esc(title)}</title>'
        '<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,'
        '"Liberation Mono",monospace} '
        '@keyframes typeLine{0%,6%{width:0}32%,92%{width:var(--line-width)}100%{width:0}} '
        '@keyframes blink{50%{opacity:0}} .cursor{animation:blink 1.1s steps(1,end) infinite} '
        '@media(prefers-reduced-motion:reduce){.reveal,.cursor{animation:none!important}}'
        '</style>'
        f'<defs>{defs}</defs>'
        + rect(0.5, 0.5, width - 1, height - 1, BG, 16, EDGE)
        + "".join(parts)
        + "</svg>\n"
    )


def panel_header(width, title):
    return [
        text(29, 33, title, 13, MUTED),
        rect(26, 48, width - 52, 1, EDGE, 0),
    ]


def draw_monogram(x, y, cell=15, animated=True):
    letters = ["01110", "11011", "10001", "11111", "10001", "10001", "10001"]
    letter_b = ["11110", "10001", "10001", "11110", "10001", "10001", "11110"]
    out = []
    for row in range(7):
        for column, value in enumerate(letters[row] + "00" + letter_b[row]):
            if value != "1":
                continue
            anim = (
                '<animate attributeName="opacity" values="0;1" dur="0.35s" '
                f'begin="{(row * 0.07 + column * 0.02):.2f}s" fill="freeze"/>'
                if animated else ""
            )
            out.append(
                f'<rect x="{x+column*cell}" y="{y+row*cell}" '
                f'width="{cell-3}" height="{cell-3}" rx="2" fill="{GREEN}">'
                + anim + "</rect>"
            )
    return "".join(out)


def typing_line(x, y, value, size, color, key, delay):
    width = len(value) * size * .602 + 13
    clip = (
        f'<defs><clipPath id="{key}"><rect x="{x}" y="{y-size-3}" '
        f'width="{width:.2f}" height="{size+10}" class="reveal" '
        f'style="--line-width:{width:.2f}px;animation:typeLine 16s '
        f'steps({len(value)},end) {delay}s infinite"/></clipPath></defs>'
    )
    return clip + f'<g clip-path="url(#{key})">' + text(x, y, value, size, color, 500) + '</g>'


def hero(profile, mobile=False):
    width, height = (460, 490) if mobile else (920, 340)
    out = panel_header(width, f'{profile["username"]} / profile')
    if mobile:
        out += [
            rect(28, 70, 104, 83, PANEL, 10, EDGE),
            draw_monogram(36, 83, 7),
            text(150, 101, profile["name"].split()[0], 29, INK, 700),
            text(150, 137, " ".join(profile["name"].split()[1:]), 29, INK, 700),
            text(30, 190, f'@{profile["username"]}', 15, CYAN),
        ]
        lines = textwrap.wrap(profile["tagline"], 36)
        for i, line in enumerate(lines):
            out.append(typing_line(30, 231 + i * 25, line, 17, GREEN, f'line-{i}', i * 1.4))
        for i, line in enumerate(textwrap.wrap(profile["bio"], 40)):
            out.append(text(30, 309 + i * 23, line, 15, MUTED))
        out += [
            rect(30, 375, 400, 1, EDGE, 0),
            text(30, 409, "tools", 13, MUTED),
            text(113, 409, "Python / Java / TypeScript", 14),
            text(30, 441, "study", 13, MUTED),
            text(113, 441, profile["education"], 14),
            text(30, 473, "based", 13, MUTED),
            text(113, 473, profile["location"], 14),
        ]
    else:
        out += [
            rect(30, 71, 224, 235, PANEL, 12, EDGE),
            draw_monogram(46, 125, 17),
            text(49, 98, "AB", 13, MUTED, 500),
            text(49, 279, "LAW + CODE", 13, GREEN, 600),
            text(288, 114, profile["name"], 42, INK, 700),
            text(290, 146, f'@{profile["username"]}', 15, CYAN),
            rect(386, 134, 8, 15, CYAN, 0, extra='class="cursor"'),
        ]
        for i, line in enumerate(textwrap.wrap(profile["tagline"], 53)):
            out.append(typing_line(290, 185 + i * 25, line, 17, GREEN, f'line-{i}', i * 1.4))
        out.append(text(290, 245, profile["bio"], 14.2, MUTED))
        out += [
            text(290, 278, "study", 13, MUTED),
            text(372, 278, f'{profile["education"]} / {profile["location"]}', 14),
            text(290, 306, "tools", 13, MUTED),
            text(372, 306, "Python / Java / TypeScript", 14),
        ]
    return svg(width, height, profile["name"] + ". " + profile["tagline"], out)


def project_card(profile, project, index):
    width, height = 440, 215
    out = [
        text(25, 33, project["repo"], 12.5, MUTED),
        rect(25, 49, 390, 1, EDGE, 0),
        text(25, 85, project["name"], 21.5 if index == 0 else 24, INK, 700),
    ]
    for i, line in enumerate(textwrap.wrap(project["description"], 42)):
        out.append(text(25, 116 + i * 22, line, 14, MUTED))
    x = 25
    for label in project["tags"]:
        w = len(label) * 7.8 + 22
        out += [
            rect(x, 168, w, 25, "#142D2C" if index == 0 else "#232038", 5),
            text(x + 11, 185, label, 12.5, GREEN if index == 0 else PURPLE),
        ]
        x += w + 8
    return svg(width, height, project["name"] + ". " + project["description"], out)


def stack(profile, mobile=False):
    width, height = (460, 178) if mobile else (920, 99)
    out = []
    x, y = 25, 25
    for i, label in enumerate(profile["skills"]):
        w = len(label) * 10.4 + 49
        if mobile and x + w > width - 25:
            x, y = 25, y + 70
        out += [
            rect(x, y, w, 48, PANEL, 7, EDGE),
            rect(x + 14, y + 19, 8, 8, GREEN if i % 2 == 0 else CYAN, 2),
            text(x + 32, y + 30, label, 17, INK, 500),
        ]
        x += w + 13
    return svg(width, height, "Tools I work with: " + ", ".join(profile["skills"]), out)


def statistics(snapshot):
    days = snapshot["contributions"]
    longest = current = 0
    for day in days:
        current = current + 1 if day["count"] else 0
        longest = max(longest, current)
    return [
        (sum(day["count"] for day in days), "CONTRIBUTIONS"),
        (sum(day["count"] > 0 for day in days), "ACTIVE DAYS"),
        (longest, "LONGEST STREAK"),
        (snapshot["public_repos"], "PUBLIC REPOS"),
    ]


def activity(snapshot, mobile=False):
    width, height = (460, 257) if mobile else (920, 163)
    out = [text(26, 32, "LAST 12 MONTHS", 12, MUTED, 500)]
    for i, (number, label) in enumerate(statistics(snapshot)):
        x = 28 + (i % 2) * 220 if mobile else 28 + i * 224
        y = 84 + (i // 2) * 91 if mobile else 83
        out += [
            text(x, y, f"{number:,}", 32, GREEN if i < 2 else INK, 700),
            text(x, y + 26, label, 11.5, MUTED),
        ]
    note = "Longest streak in the displayed period. Repos are public."
    out.append(text(26, height - 14, "Refreshed " + snapshot["refreshed_date"], 11.5, MUTED))
    return svg(width, height, "GitHub activity. " + ". ".join(
        f"{v:,} {k.lower()}" for v, k in statistics(snapshot)
    ) + ". " + note, out)


def calendar(snapshot, mobile=False):
    days = snapshot["contributions"]
    end = dt.date.fromisoformat(days[-1]["date"])
    if mobile:
        first = end.replace(day=1) - dt.timedelta(days=1)
        start = first.replace(day=1)
        shown = [d for d in days if d["date"] >= start.isoformat()]
        width, height, step, box, left, top = 460, 340, 32, 23, 43, 78
        title = "RECENT CONTRIBUTIONS"
    else:
        shown = days
        width, height, step, box, left, top = 920, 240, 15.9, 11.6, 52, 77
        title = "CONTRIBUTION CALENDAR"
    start_date = dt.date.fromisoformat(shown[0]["date"])
    week_start = start_date - dt.timedelta(days=(start_date.weekday() + 1) % 7)
    out = [text(26, 32, title, 12, MUTED, 500)]
    if not mobile:
        for label, row in [("M", 1), ("W", 3), ("F", 5)]:
            out.append(text(27, top + row * step + 10, label, 9.5, MUTED))
    previous = None
    for day in shown:
        date = dt.date.fromisoformat(day["date"])
        diff = (date - week_start).days
        column, row = divmod(diff, 7)
        if mobile:
            weeks = (end - week_start).days // 7 + 1
            left = (width - ((weeks - 1) * step + box)) / 2
        if date.month != previous:
            if column < (10 if mobile else 51):
                out.append(text(left + column * step, 57 if mobile else 63,
                                date.strftime("%b"), 11.5, MUTED))
            previous = date.month
        x, y = left + column * step, top + row * step
        color = LEVELS[day["level"]]
        count = day["count"]
        anim = (
            '<animate attributeName="opacity" values="0;1" dur="0.5s" '
            f'begin="{min(column * .015, .9):.3f}s" fill="freeze"/>'
        )
        out.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{box}" height="{box}" '
            f'rx="2.5" fill="{color}"><title>{day["date"]}: '
            f'{count} contribution{"s" if count != 1 else ""}</title>{anim}</rect>'
        )
    footer_y = height - 19
    out += [text(26, footer_y, "GitHub public calendar", 11.5, MUTED)]
    label_x = width - 182
    out.append(text(label_x, footer_y, "Less", 10.5, MUTED))
    for i, color in enumerate(LEVELS):
        out.append(rect(label_x + 33 + i * 16, footer_y - 9, 11, 11, color, 2))
    out.append(text(label_x + 118, footer_y, "More", 10.5, MUTED))
    return svg(width, height, "Public contributions from " + shown[0]["date"] +
               " to " + shown[-1]["date"], out)


class ContributionParser(HTMLParser):
    """Join public calendar cells with their human-readable tooltip counts."""

    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.tooltip = None
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("td", "rect") and attrs.get("data-date"):
            self.cells[attrs["id"]] = {
                "date": attrs["data-date"],
                "level": int(attrs.get("data-level", 0)),
            }
        if tag == "tool-tip" and attrs.get("for"):
            self.tooltip = attrs["for"]
            self.buffer = []

    def handle_data(self, data):
        if self.tooltip is not None:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip is not None:
            self.tooltips[self.tooltip] = " ".join(self.buffer)
            self.tooltip = None

    def records(self):
        days = []
        for key, cell in self.cells.items():
            tip = self.tooltips.get(key, "").strip()
            match = re.match(r"([\d,]+)\s+contributions?\b", tip, re.I)
            if match:
                count = int(match.group(1).replace(",", ""))
            elif re.match(r"No contributions\b", tip, re.I) or cell["level"] == 0:
                count = 0
            else:
                raise ValueError("A contribution count could not be read for " + cell["date"])
            if not 0 <= cell["level"] <= 4:
                raise ValueError("Unexpected contribution intensity")
            days.append({**cell, "count": count})
        days.sort(key=lambda day: day["date"])
        return days


def get(url, json_result=True):
    headers = {"User-Agent": "Abdul-Basit-GitHub-Profile/1.0"}
    if urllib.parse.urlparse(url).hostname == "api.github.com":
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=40) as response:
        content = response.read(5_000_001)
    if len(content) > 5_000_000:
        raise ValueError("GitHub response exceeds the expected size")
    return json.loads(content) if json_result else content.decode("utf-8")


def validate(profile):
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", profile["username"]):
        raise ValueError("Invalid GitHub username")
    for project in profile["projects"]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", project["repo"]):
            raise ValueError("Invalid repository name")
    if len(profile["projects"]) != 2:
        raise ValueError("This layout displays two featured projects")


def fetch_snapshot(profile):
    username = profile["username"]
    user = get(f"https://api.github.com/users/{username}")
    parser = ContributionParser()
    parser.feed(get(f"https://github.com/users/{username}/contributions", False))
    records = parser.records()
    if len(records) < 300:
        raise ValueError("GitHub did not return a complete contribution calendar")
    today = dt.datetime.now(dt.timezone.utc).date()
    records = [d for d in records if today - dt.timedelta(days=364)
               <= dt.date.fromisoformat(d["date"]) <= today]
    if not records or len(records) < 350:
        raise ValueError("The public calendar does not cover the expected year")
    return {
        "username": username,
        "refreshed_date": today.isoformat(),
        "public_repos": user["public_repos"],
        "contributions": records,
    }


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     delete=False) as stream:
        stream.write(content)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def build(profile, snapshot):
    if snapshot.get("username", "").lower() != profile["username"].lower():
        raise ValueError("Saved data belongs to a different GitHub profile")
    return {
        "hero.svg": hero(profile),
        "hero-mobile.svg": hero(profile, True),
        "stack.svg": stack(profile),
        "stack-mobile.svg": stack(profile, True),
        "project-vps.svg": project_card(profile, profile["projects"][0], 0),
        "project-android.svg": project_card(profile, profile["projects"][1], 1),
        "activity.svg": activity(snapshot),
        "activity-mobile.svg": activity(snapshot, True),
        "calendar.svg": calendar(snapshot),
        "calendar-mobile.svg": calendar(snapshot, True),
    }


def render_readme(profile):
    username = profile['username']
    url = f'https://github.com/{username}'
    projects = profile['projects']
    intro = esc(f"{profile['name']}, @{username}. {profile['tagline']}")
    return textwrap.dedent(f'''\
        <p align="center">
          <picture>
            <source media="(max-width: 600px)" srcset="./assets/hero-mobile.svg">
            <img src="./assets/hero.svg" alt="{intro}" width="920">
          </picture>
        </p>

        <p align="center">
          <a href="{url}?tab=repositories">Browse my repositories</a> &nbsp; · &nbsp;
          <a href="{url}/{projects[0]['repo']}/issues">VPS project support</a>
        </p>

        ## Projects

        <a href="{url}/{projects[0]['repo']}"><img src="./assets/project-vps.svg" width="410" alt="{esc(projects[0]['name'] + '. ' + projects[0]['description'])}"></a>
        <a href="{url}/{projects[1]['repo']}"><img src="./assets/project-android.svg" width="410" alt="{esc(projects[1]['name'] + '. ' + projects[1]['description'])}"></a>

        ## Tools I work with

        <picture>
          <source media="(max-width: 600px)" srcset="./assets/stack-mobile.svg">
          <img src="./assets/stack.svg" width="920" alt="{esc(', '.join(profile['skills']))}">
        </picture>

        ## Contributions

        <picture>
          <source media="(max-width: 600px)" srcset="./assets/activity-mobile.svg">
          <img src="./assets/activity.svg" width="920" alt="GitHub contribution totals, active days, longest streak and public repository count. Refreshed daily.">
        </picture>

        <picture>
          <source media="(max-width: 600px)" srcset="./assets/calendar-mobile.svg">
          <img src="./assets/calendar.svg" width="920" alt="My GitHub contribution calendar for the last 12 months, updated daily.">
        </picture>

        <details>
        <summary>About this profile</summary>

        The cards use self-contained SVG animations. GitHub Actions refreshes the public contribution data each day.

        Edit profile.json to change the introduction, skills and featured projects. The source is in scripts/.

        Design references — [navi3582](https://github.com/navi3582) and [DenverCoder1](https://github.com/DenverCoder1). Original artwork and implementation for {profile['name']}.

        </details>
        ''')


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--offline", action="store_true", help="Use the last successful snapshot")
    options = args.parse_args()
    profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    validate(profile)
    snapshot_file = ROOT / "data/public-github.json"
    snapshot = (json.loads(snapshot_file.read_text(encoding="utf-8"))
                if options.offline else fetch_snapshot(profile))
    cards = build(profile, snapshot)
    for name, content in cards.items():
        atomic_write(ROOT / "assets" / name, content)
    atomic_write(ROOT / 'README.md', render_readme(profile))
    if not options.offline:
        atomic_write(snapshot_file, json.dumps(snapshot, indent=2) + "\n")
    print(f"Built {len(cards)} cards for @{profile['username']}. "
          f"Data refreshed {snapshot['refreshed_date']}.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print(f"Profile refresh failed: {error}", file=sys.stderr)
        raise SystemExit(1)
