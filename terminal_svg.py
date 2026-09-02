#!/usr/bin/env python3
"""
terminal_svg.py — Generates a retro terminal SVG from GitHub stats JSON.
"""

import argparse
import json
import sys
import re
from typing import Dict, Any

# === THEMES ===
THEMES = {
    "tokyonight": {
        "bg": "#1a1b26",
        "fg": "#c0caf5",
        "green": "#9ece6a",
        "cyan": "#7dcfff",
        "purple": "#bb9af7",
        "orange": "#ff9e64",
        "red": "#f7768e",
        "yellow": "#e0af68",
        "titlebar": "#24283b",
        "border": "#414868",
        "cursor": "#9ece6a",
    },
    "dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "green": "#50fa7b",
        "cyan": "#8be9fd",
        "purple": "#bd93f9",
        "orange": "#ffb86c",
        "red": "#ff5555",
        "yellow": "#f1fa8c",
        "titlebar": "#44475a",
        "border": "#6272a4",
        "cursor": "#50fa7b",
    },
    "catppuccin": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "green": "#a6e3a1",
        "cyan": "#89dceb",
        "purple": "#cba6f7",
        "orange": "#fab387",
        "red": "#f38ba8",
        "yellow": "#f9e2af",
        "titlebar": "#313244",
        "border": "#45475a",
        "cursor": "#a6e3a1",
    },
    "nord": {
        "bg": "#2e3440",
        "fg": "#e5e9f0",
        "green": "#a3be8c",
        "cyan": "#8fbcbb",
        "purple": "#b48ead",
        "orange": "#d08770",
        "red": "#bf616a",
        "yellow": "#ebcb8b",
        "titlebar": "#3b4252",
        "border": "#4c566a",
        "cursor": "#a3be8c",
    },
    "green_phosphor": {
        "bg": "#0a0a0a",
        "fg": "#33ff33",
        "green": "#33ff33",
        "cyan": "#33ff33",
        "purple": "#33ff33",
        "orange": "#33ff33",
        "red": "#33ff33",
        "yellow": "#33ff33",
        "titlebar": "#1a1a1a",
        "border": "#33ff33",
        "cursor": "#33ff33",
    },
}


def sanitize_text(text) -> str:
    """Remove all invalid/non-printable characters and escape XML special characters."""
    if text is None:
        return ""
    text = str(text)
    # Strip control/non-printable ASCII (keep this conservative — see note in README
    # about box-drawing/block characters used elsewhere in this file, which are
    # inserted as static literals, not through this function).
    text = re.sub(r"[^\x20-\x7E]", "", text)
    # Escape XML entities — order matters, & must go first
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text


def generate_svg(stats: Dict[str, Any], theme_name: str = "tokyonight") -> str:
    """Generate a clean, valid, self-contained SVG."""
    theme = THEMES.get(theme_name, THEMES["tokyonight"])

    raw_username = stats.get("username") or "user"
    username = sanitize_text(raw_username)
    # Fall back to the RAW username (not the already-escaped `username` var) to
    # avoid double-escaping entities like &lt; into &amp;lt;.
    name = sanitize_text(stats.get("name") or raw_username)
    stars = stats.get("stars") or 0
    followers = stats.get("followers") or 0
    repos = stats.get("repos") or 0
    contributions = stats.get("contributions")
    contributions_display = str(contributions) if contributions is not None else "n/a"
    top_langs = stats.get("top_languages") or []
    fetched_at = sanitize_text(stats.get("fetched_at", ""))[:10]

    lines = []
    lines.append(f'<tspan fill="{theme["fg"]}" font-weight="bold">GitHub Stats — {username}</tspan>')
    lines.append(f'<tspan fill="{theme["green"]}">&gt; </tspan><tspan fill="{theme["fg"]}">whoami</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">{name} (@{username})</tspan>')
    lines.append(f'<tspan fill="{theme["green"]}">&gt; </tspan><tspan fill="{theme["fg"]}">neofetch</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  ├─ <tspan fill="{theme["cyan"]}">Followers:</tspan> {followers}</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  ├─ <tspan fill="{theme["cyan"]}">Repos:</tspan> {repos}</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  ├─ <tspan fill="{theme["cyan"]}">Stars:</tspan> {stars}</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  └─ <tspan fill="{theme["cyan"]}">Contributions:</tspan> {contributions_display}</tspan>')

    if top_langs:
        lines.append(f'<tspan fill="{theme["green"]}">&gt; </tspan><tspan fill="{theme["fg"]}">languages</tspan>')
        for entry in top_langs[:5]:
            lang, pct = entry[0], entry[1]
            safe_lang = sanitize_text(lang)
            bar_width = max(1, int(float(pct) * 0.3))
            bar_width = min(bar_width, 30)
            bars = "█" * bar_width + "░" * (30 - bar_width)
            lines.append(
                f'<tspan fill="{theme["fg"]}">  {safe_lang:<12} </tspan>'
                f'<tspan fill="{theme["purple"]}">{bars}</tspan>'
                f'<tspan fill="{theme["fg"]}"> {pct}%</tspan>'
            )

    lines.append(f'<tspan fill="{theme["green"]}">&gt; </tspan><tspan fill="{theme["fg"]}">status</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  ├─ <tspan fill="{theme["cyan"]}">Profile:</tspan> <tspan fill="{theme["green"]}">✓ active</tspan></tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  ├─ <tspan fill="{theme["cyan"]}">Updated:</tspan> {fetched_at}</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  └─ <tspan fill="{theme["cyan"]}">System:</tspan> <tspan fill="{theme["green"]}">operational</tspan></tspan>')
    lines.append(f'<tspan fill="{theme["green"]}">&gt; </tspan><tspan fill="{theme["fg"]}">ready</tspan>')
    lines.append(f'<tspan fill="{theme["fg"]}">  </tspan><tspan fill="{theme["cursor"]}" text-decoration="blink">█</tspan>')

    line_height = 20
    y_offset = 45
    text_blocks = []
    for i, line in enumerate(lines):
        y = y_offset + i * line_height
        text_blocks.append(f'      <text x="15" y="{y}" font-family="monospace" font-size="14">{line}</text>')

    width = 620
    height = 60 + len(lines) * line_height + 20

    # NOTE: no @import of external fonts here — GitHub's camo/SVG sanitizer strips
    # or blocks externally-loaded resources in embedded README SVGs, which would
    # otherwise cause fonts (and potentially the whole <style> block) to silently
    # fail. We rely on the system monospace font stack instead, which is fully
    # self-contained and renders identically everywhere.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      text {{ font-family: 'JetBrains Mono', 'Fira Code', 'Cousine', 'Consolas', monospace; }}
      @keyframes blink {{ 0% {{ opacity: 0; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
      text[text-decoration='blink'] {{ animation: blink 1s step-end infinite; }}
    </style>
  </defs>

  <rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="{theme['bg']}" stroke="{theme['border']}" stroke-width="2"/>

  <rect x="0" y="0" width="{width}" height="30" rx="10" fill="{theme['titlebar']}"/>
  <rect x="0" y="20" width="{width}" height="10" fill="{theme['titlebar']}"/>

  <circle cx="15" cy="15" r="6" fill="#ff5f56"/>
  <circle cx="35" cy="15" r="6" fill="#ffbd2e"/>
  <circle cx="55" cy="15" r="6" fill="#27c93f"/>

  <text x="70" y="20" fill="{theme['fg']}" font-size="12" font-family="monospace" font-weight="bold">GitHub Stats</text>

{chr(10).join(text_blocks)}
</svg>'''

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate terminal SVG from GitHub stats")
    parser.add_argument("--input", "-i", help="JSON file from fetch_stats.py")
    parser.add_argument("--theme", "-t", default="tokyonight", choices=list(THEMES.keys()))
    parser.add_argument("--output", "-o", default="stats.svg", help="Output SVG file")
    args = parser.parse_args()

    if not args.input:
        print("Error: --input is required", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r") as f:
        stats = json.load(f)

    svg = generate_svg(stats, args.theme)

    with open(args.output, "w") as f:
        f.write(svg)

    print(f"Generated {args.output} with {args.theme} theme", file=sys.stderr)


if __name__ == "__main__":
    main()