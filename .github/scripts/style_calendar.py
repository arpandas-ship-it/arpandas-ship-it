"""Style the generated night calendar and give every column a visible foundation."""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
PATH = Path("profile-3d-contrib/profile-night-green.svg")
PALETTE = [
    ("#a9b4ae", "#89958e", "#74847b"),
    ("#9bd5a9", "#69a67c", "#45845c"),
    ("#76c58e", "#4b9c69", "#327e51"),
    ("#58b578", "#348c58", "#216e41"),
    ("#3da662", "#287e47", "#185e32"),
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
    # A raised column shares the footprint of its ground tile.
    slope = math.tan(math.radians(30))
    projected = []
    for tile in tiles.findall(f"{{{SVG}}}g"):
        top = tile.find(f"{{{SVG}}}rect")
        if top is None or not top.get("class", "").startswith("cont-top-"):
            continue
        x, y = map(float, tile.attrib["transform"][10:-1].split())
        motion = tile.find(f"{{{SVG}}}animateTransform")
        ground_y = float(motion.attrib["values"].split(";")[0].split()[1]) if motion is not None else y
        if motion is not None:
            level = int(top.attrib["class"].split("-")[-1])
            rise = (0, 5, 10, 16, 22)[level]
            start = motion.attrib["values"].split(";")[0]
            end = f"{x:g} {ground_y - rise:.2f}"
            tile.set("transform", f"translate({end})")
            motion.set("values", f"{start};{end}")
            for side in tile.findall(f"{{{SVG}}}rect")[1:]:
                animation = side.find(f"{{{SVG}}}animate")
                initial = float(animation.attrib["values"].split(";")[0])
                height = f"{initial + rise / 1.15:.2f}"
                side.set("height", height)
                animation.set("values", f"{initial:g};{height}")
        u, v = (x + ground_y / slope) / 2, (x - ground_y / slope) / 2
        projected.extend(((u, v), (u + 18, v + 18)))
    if not projected:
        raise ValueError("No calendar tiles found")
    u, v = zip(*projected)
    left, right = min(u) - 3, max(u) + 3
    back, front = min(v) - 3, max(v) + 3
    corners = [(left, back), (right, back), (right, front), (left, front)]
    points = " ".join(f"{a+b:.2f},{(a-b)*slope+3:.2f}" for a, b in corners)
    base = tiles.find(f"{{{SVG}}}polygon[@id='calendar-base']")
    if base is None:
        base = ET.Element(f"{{{SVG}}}polygon", id="calendar-base")
        tiles.insert(0, base)
    base.set("points", points)
    base.set("fill", "#62726a")
    tree.write(path, encoding="utf-8")


if __name__ == "__main__":
    style_calendar(PATH)
