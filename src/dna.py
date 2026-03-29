"""Mars Barn Opus — Colony DNA Fingerprint

Hash each echo frame into a unique visual pattern. Each colony run
produces a unique fingerprint — the colony's story as art.

The fingerprint is a grid where each cell represents one sol:
- Color = dominant resource state (green=healthy, yellow=stressed, red=critical)
- Brightness = morale
- Pattern = events (dust storm = grain, meteorite = spike)

Two colonies that survived 500 sols look different because they
made different decisions. The fingerprint IS the story.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List


def sol_to_color(state: Dict) -> tuple:
    """Convert one sol's state to an RGB color.

    Green channel = O2 health
    Red channel = crisis intensity
    Blue channel = power level
    Alpha/brightness = morale
    """
    o2_days = state.get("o2_days", 30)
    food_days = state.get("food_days", 30)
    power = state.get("power", 500)
    morale = state.get("morale", 0.85)
    has_event = state.get("has_event", False)
    crew_alive = state.get("crew_alive", 4)

    # Green: resource health (0-255)
    resource_health = min(1.0, min(o2_days, food_days) / 30.0)
    g = int(resource_health * 200 + 30)

    # Red: crisis/danger (0-255)
    crisis = max(0, 1.0 - resource_health)
    r = int(crisis * 200 + (55 if has_event else 20))

    # Blue: power/tech level (0-255)
    power_frac = min(1.0, power / 800.0)
    b = int(power_frac * 150 + 40)

    # Modulate by morale
    brightness = 0.4 + morale * 0.6
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)

    # Crew death: flash red
    if crew_alive < 4:
        r = min(255, r + (4 - crew_alive) * 40)

    return (min(255, r), min(255, g), min(255, b))


def generate_fingerprint_data(echo_history: List[Dict],
                              width: int = 50) -> List[List[tuple]]:
    """Generate a 2D grid of RGB colors from echo frame history.

    Each row wraps at `width` sols, creating a visual timeline
    that reads left-to-right, top-to-bottom like a book.
    """
    if not echo_history:
        return []

    grid = []
    row = []
    for echo in echo_history:
        state = {
            "o2_days": echo.get("o2_days", 30),
            "food_days": echo.get("food_days", 30),
            "power": echo.get("power", 500),
            "morale": echo.get("morale", 0.85),
            "has_event": len(echo.get("events", [])) > 0,
            "crew_alive": echo.get("crew_alive", 4),
        }
        color = sol_to_color(state)
        row.append(color)
        if len(row) >= width:
            grid.append(row)
            row = []
    if row:
        # Pad last row
        while len(row) < width:
            row.append((10, 10, 15))
        grid.append(row)

    return grid


def fingerprint_hash(echo_history: List[Dict]) -> str:
    """Generate a unique hash for this colony's entire history."""
    data = ""
    for echo in echo_history:
        data += f"{echo.get('frame', 0)}:{echo.get('delta', {}).get('o2', 0):.2f}:"
        data += f"{echo.get('delta', {}).get('food', 0):.2f}:"
        data += f"{len(echo.get('events', []))}:"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def fingerprint_to_svg(grid: List[List[tuple]], cell_size: int = 6,
                       colony_name: str = "Colony",
                       hash_str: str = "") -> str:
    """Render fingerprint grid as an inline SVG string."""
    if not grid:
        return '<svg width="100" height="20"><text x="5" y="15" fill="#666" font-size="11">No data</text></svg>'

    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    w = cols * cell_size + 20
    h = rows * cell_size + 40

    cells = []
    for y, row in enumerate(grid):
        for x, (r, g, b) in enumerate(row):
            cells.append(
                f'<rect x="{x * cell_size + 10}" y="{y * cell_size + 25}" '
                f'width="{cell_size - 1}" height="{cell_size - 1}" '
                f'fill="rgb({r},{g},{b})" rx="1"/>'
            )

    header = (f'<text x="10" y="15" fill="#c9d1d9" font-size="11" '
              f'font-family="monospace">{colony_name}</text>')
    footer = (f'<text x="10" y="{h - 5}" fill="#484f58" font-size="9" '
              f'font-family="monospace">DNA: {hash_str} | {sum(len(r) for r in grid)} sols</text>')

    return (f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="background:#0d1117;border-radius:6px">'
            f'{header}{"".join(cells)}{footer}</svg>')
