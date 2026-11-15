import os

import game_framework
import game_world
from pico2d import load_image

from stage_config import (
    MONSTER_HEIGHT,
    MONSTER_HP,
    MONSTER_WIDTH,
    SCREEN_WIDTH,
    WORLD_SCROLL_SPEED,
)


_image_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "image", "monster.png")
)


class Monster:
    def __init__(self, x, ground_y):
        self.image = load_image(_image_path)
        self.x = float(x)
        self.ground_y = float(ground_y)
        self.hp = MONSTER_HP
        self.width = MONSTER_WIDTH
        self.height = MONSTER_HEIGHT
        self.alive = True

    def update(self):
        dt = game_framework.frame_time * game_framework.simulation_scale
        self.x += WORLD_SCROLL_SPEED * dt
        if self.x - self.width / 2 > SCREEN_WIDTH:
            self.alive = False
            game_world.remove_object(self)

    def draw(self):
        self.image.draw(self.x, self.ground_y + self.height / 2)

    def take_damage(self, damage):
        if not self.alive:
            return False
        self.hp -= max(0, int(damage))
        if self.hp <= 0:
            self.alive = False
            game_world.remove_object(self)
            return True
        return False
