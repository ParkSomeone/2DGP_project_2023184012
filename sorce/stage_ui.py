from pico2d import draw_rectangle

from stage_config import SCREEN_HEIGHT, SCREEN_WIDTH


_GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    "%": ("11001", "11010", "00100", "01000", "10110", "00110", "00000"),
}


def draw_text(text, x, y, scale=2, color=(255, 242, 219)):
    r, g, b = color
    cursor_x = int(x)
    for character in text.upper():
        glyph = _GLYPHS.get(character)
        if glyph is None:
            cursor_x += scale * 4
            continue
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    left = cursor_x + column * scale
                    bottom = y + (6 - row) * scale
                    draw_rectangle(
                        left,
                        bottom,
                        left + scale,
                        bottom + scale,
                        r,
                        g,
                        b,
                        255,
                        True,
                    )
        cursor_x += scale * 6
    return cursor_x


def draw_bar(x, y, width, height, ratio, color):
    draw_rectangle(x, y, x + width, y + height, 23, 22, 38, 230, True)
    fill_width = max(0, min(width, int(width * ratio)))
    if fill_width:
        draw_rectangle(
            x,
            y,
            x + fill_width,
            y + height,
            color[0],
            color[1],
            color[2],
            255,
            True,
        )
    draw_rectangle(x, y, x + width, y + height, 218, 198, 160, 255)


def draw_hud(player, boss, remaining_time, events, outcome):
    draw_rectangle(20, SCREEN_HEIGHT - 104, 418, SCREEN_HEIGHT - 22,
                   28, 27, 45, 205, True)
    draw_text("HP", 34, SCREEN_HEIGHT - 55, 2, (255, 232, 210))
    draw_bar(
        72,
        SCREEN_HEIGHT - 58,
        270,
        18,
        player.hp / player.max_hp,
        (203, 67, 83),
    )
    draw_text(
        f"LV {player.level}  XP {player.experience:03d}",
        34,
        SCREEN_HEIGHT - 88,
        2,
        (238, 215, 164),
    )
    draw_text(
        f"Q {player.potions}  UPG {player.upgrade_tokens}",
        230,
        SCREEN_HEIGHT - 88,
        2,
        (238, 215, 164),
    )

    timer = max(0, int(remaining_time))
    minutes, seconds = divmod(timer, 60)
    draw_rectangle(SCREEN_WIDTH - 236, SCREEN_HEIGHT - 75,
                   SCREEN_WIDTH - 20, SCREEN_HEIGHT - 22,
                   28, 27, 45, 205, True)
    draw_text(
        f"STAGE {minutes:02d}:{seconds:02d}",
        SCREEN_WIDTH - 218,
        SCREEN_HEIGHT - 58,
        2,
        (255, 232, 210),
    )

    draw_text("W E R AIM", 36, 34, 2, (230, 215, 190))
    for index, key in enumerate(("w", "e", "r")):
        x = 186 + index * 110
        cooldown = player.cooldowns[key]
        label = "READY" if cooldown <= 0 else f"{cooldown:.1f}"
        draw_text(f"{key.upper()} {label}", x, 34, 2,
                  (255, 221, 150) if cooldown <= 0 else (176, 171, 181))

    if boss.alive:
        draw_text("BOSS", SCREEN_WIDTH - 260, SCREEN_HEIGHT - 112,
                  2, (255, 211, 157))
        draw_bar(
            SCREEN_WIDTH - 188,
            SCREEN_HEIGHT - 112,
            162,
            14,
            boss.hp / boss.max_hp,
            (180, 51, 91),
        )

    if player.state == "AIM":
        draw_text("AIM - CLICK FIRE / RIGHT CLICK CANCEL",
                  SCREEN_WIDTH // 2 - 256, SCREEN_HEIGHT - 62, 2,
                  (255, 229, 164))
    elif events:
        draw_text("EVENT READY - INTEGRATE NEXT MODE",
                  SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT - 62, 2,
                  (235, 219, 180))

    if outcome:
        message = {
            "survived": "STAGE COMPLETE",
            "player_died": "GAME OVER",
            "boss_defeated": "BOSS DEFEATED",
        }[outcome]
        draw_rectangle(
            SCREEN_WIDTH // 2 - 280,
            SCREEN_HEIGHT // 2 - 48,
            SCREEN_WIDTH // 2 + 280,
            SCREEN_HEIGHT // 2 + 54,
            28,
            27,
            45,
            225,
            True,
        )
        draw_text(
            message,
            SCREEN_WIDTH // 2 - len(message) * 9,
            SCREEN_HEIGHT // 2,
            3,
            (255, 229, 164),
        )
        draw_text(
            "RESULT EVENT QUEUED - ESC TO EXIT",
            SCREEN_WIDTH // 2 - 198,
            SCREEN_HEIGHT // 2 - 30,
            2,
            (232, 215, 187),
        )
