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


def pulse(animation, low, high):
    animation.attrib.update(values=f"{low};{high};{high};{low};{low}", dur="6s",
                            keyTimes="0;0.35;0.5;0.85;1", repeatCount="indefinite",
                            calcMode="spline", keySplines=";".join(["0.45 0 0.55 1"] * 4))


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
    footprints = []
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
            pulse(motion, f"{x:g} {ground_y - rise * 0.4:.3f}", end)
            for side in tile.findall(f"{{{SVG}}}rect")[1:]:
                animation = side.find(f"{{{SVG}}}animate")
                initial = float(animation.attrib["values"].split(";")[0])
                height = f"{initial + rise / 1.15:.2f}"
                side.set("height", height)
                pulse(animation, f"{initial + rise * 0.4 / 1.15:.3f}", height)
        u, v = (x + ground_y / slope) / 2, (x - ground_y / slope) / 2
        footprints.append((u, v))
    if not footprints:
        raise ValueError("No calendar tiles found")

    # One full tile around the dates contains the projected tops as well as
    # the feet of the columns. 22 vertical units project to 19.1 grid units.
    us, vs = zip(*footprints)
    pitch, face = 20, 18
    u0, v0 = min(us), min(vs)
    week_count = round((max(us) - u0) / pitch) + 1
    day_count = round((max(vs) - v0) / pitch) + 1

    def diamond(u, v, width, depth):
        corners = ((u, v), (u+width, v), (u+width, v+depth), (u, v+depth))
        return " ".join(f"{a+b:.2f},{(a-b)*slope:.2f}" for a, b in corners)

    for child in list(tiles):
        if child.get("id") in {"calendar-base", "calendar-surround"}:
            tiles.remove(child)
    surround = ET.Element(f"{{{SVG}}}g", id="calendar-surround",
                          attrib={"aria-hidden": "true", "pointer-events": "none"})
    tiles.insert(0, surround)
    ET.SubElement(surround, f"{{{SVG}}}polygon", id="calendar-base", fill="#65736c",
                  points=diamond(u0-pitch-2, v0-pitch-2,
                                 (week_count+3)*pitch+2, (day_count+3)*pitch+2))
    # Draw the full grid underneath the columns, including the partial week
    # and a two-tile apron past the latest week and the raised back edge.
    for col in range(-1, week_count + 2):
        for row in range(-1, day_count + 2):
            ET.SubElement(surround, f"{{{SVG}}}polygon", fill=PALETTE[0][0],
                          points=diamond(u0+col*pitch, v0+row*pitch, face, face))
    tiles.set("transform", "translate(50 18) scale(0.89)")
    tree.write(Path("assets/contribution-calendar-animated.svg"), encoding="utf-8")


if __name__ == "__main__":
    style_calendar(PATH)
