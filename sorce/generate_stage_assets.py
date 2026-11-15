import os
import struct
import zlib


class Canvas:
    def __init__(self, width, height, color=(0, 0, 0, 0)):
        self.width = width
        self.height = height
        self.pixels = bytearray(color * (width * height))

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 4
            self.pixels[offset:offset + 4] = bytes(color)

    def rect(self, x1, y1, x2, y2, color):
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(self.width, int(x2))
        y2 = min(self.height, int(y2))
        if x1 >= x2 or y1 >= y2:
            return
        row = bytes(color) * (x2 - x1)
        for y in range(y1, y2):
            offset = (y * self.width + x1) * 4
            self.pixels[offset:offset + len(row)] = row

    def ellipse(self, cx, cy, rx, ry, color):
        rx = max(1, int(rx))
        ry = max(1, int(ry))
        for y in range(max(0, cy - ry), min(self.height, cy + ry + 1)):
            relative_y = (y - cy) / ry
            span = int(rx * (1 - relative_y * relative_y) ** 0.5)
            self.rect(cx - span, y, cx + span + 1, y + 1, color)

    def polygon(self, points, color):
        min_y = max(0, min(point[1] for point in points))
        max_y = min(self.height - 1, max(point[1] for point in points))
        for y in range(min_y, max_y + 1):
            crossings = []
            for index, (x1, y1) in enumerate(points):
                x2, y2 = points[(index + 1) % len(points)]
                if y1 == y2:
                    continue
                if min(y1, y2) <= y < max(y1, y2):
                    crossings.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            crossings.sort()
            for index in range(0, len(crossings) - 1, 2):
                self.rect(crossings[index], y, crossings[index + 1] + 1, y + 1, color)

    def line(self, x1, y1, x2, y2, color, thickness=1):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        error = dx - dy
        while True:
            self.rect(x1 - thickness // 2, y1 - thickness // 2,
                      x1 + thickness // 2 + 1, y1 + thickness // 2 + 1, color)
            if x1 == x2 and y1 == y2:
                break
            twice_error = error * 2
            if twice_error > -dy:
                error -= dy
                x1 += sx
            if twice_error < dx:
                error += dx
                y1 += sy


def png_chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def save_png(path, canvas):
    raw = bytearray()
    stride = canvas.width * 4
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw.extend(canvas.pixels[start:start + stride])
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", canvas.width, canvas.height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as file:
        file.write(data)


def make_background():
    canvas = Canvas(1600, 900, (30, 26, 57, 255))
    for y in range(520):
        t = y / 520
        color = (int(39 + 36 * t), int(35 + 20 * t), int(82 + 20 * t), 255)
        canvas.rect(0, y, 1600, y + 1, color)

    canvas.ellipse(1230, 170, 72, 72, (238, 178, 125, 255))
    canvas.ellipse(1230, 170, 61, 61, (250, 210, 154, 255))
    for x, y in ((170, 92), (360, 135), (580, 76), (790, 164), (1030, 85), (1460, 105)):
        canvas.ellipse(x, y, 3, 3, (255, 232, 198, 255))

    canvas.polygon([(0, 390), (155, 230), (285, 365), (480, 190), (720, 395),
                    (900, 245), (1110, 400), (1325, 210), (1600, 390),
                    (1600, 640), (0, 640)], (54, 46, 83, 255))
    canvas.polygon([(0, 470), (240, 320), (415, 486), (650, 290), (890, 488),
                    (1110, 345), (1330, 485), (1500, 330), (1600, 420),
                    (1600, 670), (0, 670)], (42, 40, 73, 255))

    for x in range(-20, 1650, 180):
        canvas.rect(x, 430, x + 24, 680, (34, 34, 62, 255))
        canvas.polygon([(x - 30, 440), (x + 12, 340), (x + 55, 440)], (34, 34, 62, 255))
        canvas.rect(x - 8, 520, x + 35, 538, (84, 55, 89, 255))
    canvas.rect(0, 640, 1600, 900, (30, 31, 51, 255))
    canvas.polygon([(0, 710), (250, 660), (430, 730), (700, 670), (950, 725),
                    (1220, 660), (1600, 710), (1600, 900), (0, 900)], (23, 28, 46, 255))
    for x in range(40, 1600, 130):
        canvas.ellipse(x, 790 + (x % 5) * 12, 42, 8, (48, 42, 64, 255))
        canvas.ellipse(x + 24, 852, 24, 6, (41, 39, 61, 255))

    # A distant red gate hints at the pursuing dungeon boss.
    canvas.rect(1350, 392, 1435, 650, (31, 24, 47, 255))
    canvas.rect(1364, 408, 1421, 650, (112, 40, 73, 255))
    canvas.rect(1374, 428, 1411, 650, (219, 87, 100, 255))
    return canvas


def make_ground():
    canvas = Canvas(160, 128, (0, 0, 0, 0))
    canvas.rect(0, 0, 160, 128, (39, 30, 44, 255))
    canvas.rect(0, 0, 160, 18, (91, 143, 111, 255))
    canvas.rect(0, 18, 160, 28, (56, 95, 78, 255))
    canvas.rect(0, 28, 160, 36, (54, 42, 55, 255))
    for x in range(0, 160, 40):
        canvas.rect(x + 4, 45, x + 25, 52, (69, 49, 55, 255))
        canvas.rect(x + 22, 76, x + 38, 84, (55, 42, 52, 255))
    canvas.rect(0, 112, 160, 128, (28, 25, 39, 255))
    return canvas


def make_platform(kind):
    canvas = Canvas(96, 48, (0, 0, 0, 0))
    canvas.rect(0, 14, 96, 48, (58, 43, 61, 255))
    canvas.rect(0, 14, 96, 24, (82, 61, 67, 255))
    canvas.rect(0, 8, 96, 17, (115, 156, 107, 255))
    canvas.rect(0, 8, 96, 11, (166, 192, 125, 255))
    for x in range(8, 96, 24):
        canvas.rect(x, 27, x + 13, 30, (91, 67, 68, 255))
        canvas.rect(x + 10, 38, x + 20, 41, (43, 37, 52, 255))
    if kind == "start":
        canvas.ellipse(8, 19, 13, 13, (115, 156, 107, 255))
        canvas.rect(0, 18, 10, 48, (60, 46, 61, 255))
    elif kind == "end":
        canvas.ellipse(88, 19, 13, 13, (115, 156, 107, 255))
        canvas.rect(86, 18, 96, 48, (60, 46, 61, 255))
    return canvas


def make_player_sheet():
    canvas = Canvas(64 * 4, 96, (0, 0, 0, 0))
    outline = (31, 29, 48, 255)
    hood = (58, 108, 157, 255)
    hood_light = (88, 148, 183, 255)
    coat = (72, 65, 99, 255)
    scarf = (235, 181, 91, 255)
    skin = (232, 183, 145, 255)
    boot = (69, 48, 56, 255)
    for frame in range(4):
        offset = frame * 64
        stride = (frame % 2) * 5
        canvas.ellipse(offset + 31, 17, 18, 18, outline)
        canvas.ellipse(offset + 30, 16, 15, 15, hood)
        canvas.ellipse(offset + 27, 16, 10, 11, hood_light)
        canvas.rect(offset + 14, 24, offset + 31, 30, skin)
        canvas.rect(offset + 12, 20, offset + 29, 25, outline)
        canvas.rect(offset + 10, 29, offset + 39, 64, outline)
        canvas.polygon([(offset + 13, 31), (offset + 37, 31), (offset + 42, 61),
                        (offset + 8, 61)], coat)
        canvas.polygon([(offset + 11, 33), (offset + 24, 38), (offset + 30, 55),
                        (offset + 8, 53)], scarf)
        canvas.rect(offset + 6, 38, offset + 19, 44, scarf)
        canvas.rect(offset + 20, 42, offset + 37, 47, (246, 202, 119, 255))
        canvas.rect(offset + 24, 47, offset + 29, 52, (48, 39, 51, 255))
        canvas.rect(offset + 8, 52, offset + 39, 62, (55, 50, 77, 255))

        leg_y = 63
        if frame in (0, 2):
            canvas.polygon([(offset + 14, leg_y), (offset + 27, leg_y),
                            (offset + 25 + stride, 82), (offset + 11 + stride, 83)], outline)
            canvas.polygon([(offset + 26, leg_y), (offset + 37, leg_y),
                            (offset + 44 - stride, 80), (offset + 33 - stride, 81)], outline)
            canvas.rect(offset + 4 + stride, 80, offset + 19 + stride, 87, boot)
            canvas.rect(offset + 36 - stride, 78, offset + 52 - stride, 85, boot)
        else:
            canvas.polygon([(offset + 14, leg_y), (offset + 27, leg_y),
                            (offset + 17 - stride, 80), (offset + 5 - stride, 79)], outline)
            canvas.polygon([(offset + 26, leg_y), (offset + 37, leg_y),
                            (offset + 39 + stride, 83), (offset + 29 + stride, 84)], outline)
            canvas.rect(offset + 1 - stride, 76, offset + 17 - stride, 83, boot)
            canvas.rect(offset + 34 + stride, 81, offset + 51 + stride, 88, boot)
        canvas.ellipse(offset + 12, 60, 4, 5, scarf)
    return canvas


def make_monster():
    canvas = Canvas(72, 80, (0, 0, 0, 0))
    outline = (35, 28, 46, 255)
    canvas.ellipse(36, 44, 30, 31, outline)
    canvas.ellipse(36, 42, 25, 27, (147, 84, 113, 255))
    canvas.polygon([(11, 35), (17, 7), (31, 29)], outline)
    canvas.polygon([(41, 29), (56, 6), (60, 39)], outline)
    canvas.polygon([(15, 31), (19, 16), (28, 31)], (201, 127, 133, 255))
    canvas.polygon([(45, 30), (55, 15), (56, 34)], (201, 127, 133, 255))
    canvas.ellipse(25, 42, 5, 7, (255, 215, 136, 255))
    canvas.ellipse(47, 42, 5, 7, (255, 215, 136, 255))
    canvas.ellipse(25, 43, 2, 4, (35, 28, 46, 255))
    canvas.ellipse(47, 43, 2, 4, (35, 28, 46, 255))
    canvas.rect(27, 57, 45, 61, (45, 29, 49, 255))
    canvas.rect(30, 57, 34, 62, (242, 222, 186, 255))
    canvas.rect(39, 57, 43, 62, (242, 222, 186, 255))
    canvas.rect(18, 68, 31, 76, (87, 55, 77, 255))
    canvas.rect(42, 68, 55, 76, (87, 55, 77, 255))
    return canvas


def make_boss():
    canvas = Canvas(256, 320, (0, 0, 0, 0))
    outline = (25, 22, 40, 255)
    canvas.ellipse(128, 180, 95, 128, outline)
    canvas.ellipse(128, 171, 81, 115, (74, 39, 75, 255))
    canvas.polygon([(65, 104), (49, 7), (114, 81)], outline)
    canvas.polygon([(145, 81), (212, 7), (191, 111)], outline)
    canvas.polygon([(69, 93), (61, 27), (106, 84)], (183, 76, 91, 255))
    canvas.polygon([(154, 83), (199, 27), (185, 98)], (183, 76, 91, 255))
    canvas.ellipse(97, 150, 15, 18, (245, 112, 87, 255))
    canvas.ellipse(159, 150, 15, 18, (245, 112, 87, 255))
    canvas.ellipse(98, 152, 6, 9, (255, 229, 160, 255))
    canvas.ellipse(160, 152, 6, 9, (255, 229, 160, 255))
    canvas.polygon([(108, 203), (148, 203), (128, 224)], (31, 22, 39, 255))
    canvas.rect(112, 204, 120, 214, (245, 226, 190, 255))
    canvas.rect(136, 204, 144, 214, (245, 226, 190, 255))
    canvas.polygon([(60, 213), (15, 279), (72, 266), (84, 314),
                    (128, 286), (171, 314), (183, 266), (241, 279),
                    (196, 213), (173, 243), (83, 243)], (57, 35, 68, 255))
    canvas.ellipse(128, 252, 22, 18, (203, 54, 78, 255))
    canvas.ellipse(128, 252, 10, 9, (255, 156, 99, 255))
    canvas.rect(46, 263, 76, 296, (74, 41, 72, 255))
    canvas.rect(180, 263, 210, 296, (74, 41, 72, 255))
    canvas.rect(47, 287, 73, 301, (124, 66, 75, 255))
    canvas.rect(183, 287, 209, 301, (124, 66, 75, 255))
    return canvas


def make_chest():
    canvas = Canvas(64, 64, (0, 0, 0, 0))
    canvas.rect(7, 24, 57, 57, (57, 35, 43, 255))
    canvas.rect(10, 28, 54, 53, (168, 96, 52, 255))
    canvas.rect(6, 19, 58, 32, (104, 60, 47, 255))
    canvas.rect(8, 17, 56, 24, (211, 159, 76, 255))
    canvas.rect(27, 27, 37, 50, (242, 211, 122, 255))
    canvas.rect(30, 32, 34, 39, (98, 57, 47, 255))
    canvas.rect(14, 34, 20, 39, (239, 191, 100, 255))
    canvas.rect(44, 34, 50, 39, (239, 191, 100, 255))
    return canvas


def make_projectile():
    canvas = Canvas(32, 32, (0, 0, 0, 0))
    canvas.ellipse(16, 16, 14, 14, (239, 177, 82, 150))
    canvas.ellipse(16, 16, 9, 9, (255, 225, 133, 255))
    canvas.ellipse(16, 16, 4, 4, (255, 250, 214, 255))
    return canvas


def main():
    output = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "image"))
    os.makedirs(output, exist_ok=True)
    assets = {
        "stage_background.png": make_background(),
        "ground_tile.png": make_ground(),
        "platform_start.png": make_platform("start"),
        "platform_mid.png": make_platform("mid"),
        "platform_end.png": make_platform("end"),
        "player_run.png": make_player_sheet(),
        "monster.png": make_monster(),
        "boss.png": make_boss(),
        "chest.png": make_chest(),
        "projectile.png": make_projectile(),
    }
    for name, canvas in assets.items():
        save_png(os.path.join(output, name), canvas)
        print(f"Generated {name} ({canvas.width}x{canvas.height})")


if __name__ == "__main__":
    main()
