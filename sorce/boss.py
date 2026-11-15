import os

import game_framework
from pico2d import load_image

from stage_config import BOSS_HEIGHT, BOSS_HP, BOSS_WIDTH, BOSS_X, GROUND_TOP


_image_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "image", "boss.png")
)


class Boss:
    def __init__(self):
        self.image = load_image(_image_path)
        self.x = float(BOSS_X)
        self.ground_y = float(GROUND_TOP)
        self.width = BOSS_WIDTH
        self.height = BOSS_HEIGHT
        self.hp = BOSS_HP
        self.max_hp = BOSS_HP
        self.alive = True
        self.animation_time = 0.0

    def update(self):
        self.animation_time += game_framework.frame_time

    def draw(self):
        if not self.alive:
            return
        bob = 5 * (1 if int(self.animation_time * 2) % 2 == 0 else -1)
        self.image.draw(
            self.x,
            self.ground_y + self.height / 2 + bob,
        )

    def take_damage(self, damage, active_skill=False):
        if not self.alive or not active_skill:
            return False
        self.hp -= max(0, int(damage))
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False
