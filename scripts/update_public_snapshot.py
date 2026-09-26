#!/usr/bin/env python3
import hashlib
import html
import json
import math
import os
import re
import urllib.request
from pathlib import Path

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "NiloufarRabiee")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = Path("assets/public-code-snapshot-v1.svg")

# Keep the card compact forever: at most 7 rows.
# When there are more repositories, the six largest stay visible and the rest
# are combined into one "Other public repos" row.
MAX_ROWS = 7

PALETTE = [
    "#5EEAD4", "#7DD3FC", "#C084FC", "#F0ABFC",
    "#A7F3D0", "#CBD5E1", "#93C5FD",
]


def fetch_public_repos():
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?per_page=100&type=owner&page={page}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{OWNER}-profile-snapshot",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"

        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)

        if not batch:
            break

        repos.extend(
            {"name": repo["name"], "size": int(repo.get("size", 0))}
            for repo in batch
            if not repo.get("private", False)
        )

        if len(batch) < 100:
            break
        page += 1

    return sorted(repos, key=lambda repo: (-repo["size"], repo["name"].lower()))


def source_fingerprint(repos):
    # Ignore this profile repository's own reported size. The generated SVG
    # lives here, so counting that size would make the automation update itself.
    normalized = [
        {
            "name": repo["name"],
            "size": None if repo["name"] == OWNER else repo["size"],
        }
        for repo in sorted(repos, key=lambda repo: repo["name"].lower())
    ]
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def compact_rows(repos):
    if len(repos) <= MAX_ROWS:
        return repos

    visible = repos[: MAX_ROWS - 1]
    remainder = repos[MAX_ROWS - 1 :]
    visible.append(
        {
            "name": f"Other public repos ({len(remainder)})",
            "size": sum(max(0, repo["size"]) for repo in remainder),
        }
    )
    return visible


def render_svg(repos, fingerprint):
    rows = compact_rows(repos)
    total = sum(max(0, repo["size"]) for repo in repos)
    count = len(repos)

    width = 1200
    height = 410
    row_height = 39
    row_start = 135
    center_y = 220
    radius = 82
    circumference = 2 * math.pi * radius

    lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">',
        f'  <!-- data-fingerprint: {fingerprint} -->',
        "  <defs>",
        f'    <linearGradient id="bg" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">',
        '      <stop stop-color="#050A14"/>',
        '      <stop offset="1" stop-color="#0D0817"/>',
        "    </linearGradient>",
        '    <pattern id="grid" width="42" height="42" patternUnits="userSpaceOnUse">',
        '      <path d="M42 0H0V42" stroke="#94A3B8" stroke-opacity=".03"/>',
        "    </pattern>",
        "  </defs>",
        "",
        f'  <rect width="{width}" height="{height}" rx="28" fill="url(#bg)"/>',
        f'  <rect width="{width}" height="{height}" rx="28" fill="url(#grid)"/>',
        "",
        '  <text x="58" y="48" fill="#708198" font-family="ui-monospace,SFMono-Regular,Menlo,monospace" font-size="11" font-weight="700" letter-spacing="2.2">PUBLIC CODE SNAPSHOT</text>',
        '  <text x="1140" y="48" text-anchor="end" fill="#5B506C" font-family="Georgia,serif" font-size="12.5" font-style="italic">auto-updated from public repositories</text>',
        "",
        f'  <g transform="translate(245 {center_y})">',
        '    <circle r="108" fill="#09111D" stroke="#E2E8F0" stroke-opacity=".06"/>',
        '    <circle r="82" fill="none" stroke="#182333" stroke-width="26"/>',
    ]

    offset = 0.0
    for index, repo in enumerate(rows):
        size = max(0, repo["size"])
        fraction = (size / total) if total else ((1 / len(rows)) if rows else 0)
        dash = fraction * circumference
        if dash > 0:
            color = PALETTE[index % len(PALETTE)]
            lines.append(
                f'    <circle r="82" fill="none" stroke="{color}" stroke-width="26" '
                f'stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90)"/>'
            )
        offset += dash

    lines.extend(
        [
            "",
            f'    <text x="0" y="-4" text-anchor="middle" fill="#F8FAFC" font-family="Inter,Arial,sans-serif" font-size="38" font-weight="800">{count}</text>',
            '    <text x="0" y="22" text-anchor="middle" fill="#8FA0B7" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" letter-spacing="1.2">PUBLIC REPOS</text>',
            "  </g>",
            "",
            f'  <text x="58" y="{height - 18}" fill="#5E7088" font-family="Inter,Arial,sans-serif" font-size="11">Repository footprint by GitHub-reported repository size</text>',
            "",
            '  <g font-family="Inter,Arial,sans-serif">',
            '    <text x="455" y="88" fill="#F8FAFC" font-size="18" font-weight="750">Public repository footprint</text>',
            '    <text x="455" y="112" fill="#8798AE" font-size="12.5">Largest repositories + combined remainder</text>',
        ]
    )

    for index, repo in enumerate(rows):
        name = html.escape(repo["name"])
        size = max(0, repo["size"])
        percent = (size / total * 100) if total else ((100 / len(rows)) if rows else 0)
        y = row_start + index * row_height
        bar_width = 290 * percent / 100
        color = PALETTE[index % len(PALETTE)]

        lines.extend(
            [
                f'    <g transform="translate(455 {y})">',
                f'      <circle cx="5" cy="5" r="5" fill="{color}"/>',
                f'      <text x="22" y="9" fill="#DCEAF0" font-size="12.5" font-weight="650">{name}</text>',
                f'      <text x="280" y="9" fill="#8798AE" font-size="12" text-anchor="end">{percent:.1f}%</text>',
                '      <rect x="310" y="-1" width="290" height="12" rx="6" fill="#101B29"/>',
            ]
        )
        if bar_width > 0:
            lines.append(
                f'      <rect x="310" y="-1" width="{bar_width:.1f}" height="12" rx="6" '
                f'fill="{color}" fill-opacity=".82"/>'
            )
        lines.append("    </g>")

    lines.extend(
        [
            "  </g>",
            "",
            f'  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="27" stroke="#E2E8F0" stroke-opacity=".06"/>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def main():
    repos = fetch_public_repos()
    fingerprint = source_fingerprint(repos)

    if OUTPUT.exists():
        current = OUTPUT.read_text(encoding="utf-8")
        match = re.search(r"data-fingerprint:\s*([0-9a-f]+)", current)
        if match and match.group(1) == fingerprint:
            print("Public repository snapshot is already current.")
            return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_svg(repos, fingerprint), encoding="utf-8")
    print(f"Updated {OUTPUT} for {len(repos)} public repositories.")


if __name__ == "__main__":
    main()
