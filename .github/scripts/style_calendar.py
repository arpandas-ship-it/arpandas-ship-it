"""Style the generated night calendar and give every column a visible foundation."""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
PATH = Path("profile-3d-contrib/profile-night-green.svg")
PALETTE = [
    ("#c8d1cb", "#aab6ae", "#96a59b"),
    ("#abcbb0", "#86ab8c", "#719979"),
    ("#79ad86", "#568e64", "#467b53"),
    ("#49885c", "#337146", "#295c39"),
    ("#2f6c47", "#235738", "#19462c"),
]


def style_calendar(path):
    tree = ET.parse(path)
    root = tree.getroot()
    style = root.find(f"{{{SVG}}}style")
    for level, colors in enumerate(PALETTE):
        for face, color in zip(("top", "left", "right"), colors):
            selector = rf"(\.cont-{face}-{level}\s*\{{\s*fill:\s*)[^;]+"
            style.text, matches = re.subn(selector, rf"\g<1>{color}", style.text)
            if matches != 1:
                raise ValueError(f"Missing calendar color for {face} {level}")

    tiles = root.find(f"{{{SVG}}}g")
    # Work in the calendar's two diagonal axes. Include the whole top face,
    # its ground position, and the sides, even during the rise animation.
    slope = math.tan(math.radians(30))
    projected = []
    for tile in tiles.findall(f"{{{SVG}}}g"):
        top = tile.find(f"{{{SVG}}}rect")
        if top is None or not top.get("class", "").startswith("cont-top-"):
            continue
        x, y = map(float, tile.attrib["transform"][10:-1].split())
        motion = tile.find(f"{{{SVG}}}animateTransform")
        ground_y = float(motion.attrib["values"].split(";")[0].split()[1]) if motion is not None else y
        for height in (y, ground_y, ground_y + 3):
            u, v = (x + height / slope) / 2, (x - height / slope) / 2
            projected.extend(((u, v), (u + 18, v + 18)))
    if not projected:
        raise ValueError("No calendar tiles found")
    u, v = zip(*projected)
    left, right = min(u) - 7, max(u) + 7
    back, front = min(v) - 7, max(v) + 7
    corners = [(left, back), (right, back), (right, front), (left, front)]
    points = " ".join(f"{a+b:.2f},{(a-b)*slope:.2f}" for a, b in corners)
    base = tiles.find(f"{{{SVG}}}polygon[@id='calendar-base']")
    if base is None:
        base = ET.Element(f"{{{SVG}}}polygon", id="calendar-base")
        tiles.insert(0, base)
    base.set("points", points)
    base.set("fill", "#a9b6ae")
    tree.write(path, encoding="utf-8")


if __name__ == "__main__":
    style_calendar(PATH)
