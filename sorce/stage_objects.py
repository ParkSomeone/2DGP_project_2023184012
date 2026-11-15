import os
import random

import game_framework
import game_world
from pico2d import draw_circle, draw_line, load_image

from monster import Monster
from stage_config import (
    CHEST_SPAWN_INTERVAL,
    FLOOR_MONSTER_SPAWN_CHANCE,
    FLOOR_MONSTER_SPAWN_INTERVAL,
    GROUND_TOP,
    MONSTER_WIDTH,
    PLATFORM_HEIGHTS,
    PLATFORM_LENGTH_SCALE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WORLD_SCROLL_SPEED,
)


_image_cache = {}
_image_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "image")
)


def _image(filename):
    if filename not in _image_cache:
        _image_cache[filename] = load_image(
            os.path.join(_image_directory, filename)
        )
    return _image_cache[filename]


def _delta_time():
    return game_framework.frame_time * game_framework.simulation_scale


def _real_delta_time():
    return game_framework.frame_time


def _remove(obj):
    game_world.remove_object(obj)


def _spawn_platform_monsters(platform, rng):
    count = rng.randint(1, 3)
    segment_width = platform.width / count
    for index in range(count):
        left = platform.x + segment_width * index + MONSTER_WIDTH / 2
        right = platform.x + segment_width * (index + 1) - MONSTER_WIDTH / 2
        x = rng.uniform(left, right)
        game_world.add_object(Monster(x, platform.top), 1)


class ScrollingBackground:
    def __init__(self):
        self.image = _image("stage_background.png")
        self.width = SCREEN_WIDTH
        self.offset = 0.0

    def update(self):
        self.offset = (
            self.offset - WORLD_SCROLL_SPEED * _delta_time()
        ) % self.width

    def draw(self):
        for x in (self.offset - self.width, self.offset):
            self.image.draw(x + self.width / 2, SCREEN_HEIGHT / 2)


class Ground:
    def __init__(self):
        self.image = _image("ground_tile.png")
        self.width = 160
        self.offset = 0.0

    def update(self):
        self.offset = (
            self.offset - WORLD_SCROLL_SPEED * _delta_time()
        ) % self.width

    def draw(self):
        x = self.offset - self.width
        while x < SCREEN_WIDTH:
            self.image.draw(x + self.width / 2, GROUND_TOP / 2)
            x += self.width


class MovingPlatform:
    def __init__(self, x, top, middle_tiles):
        self.x = float(x)
        self.top = float(top)
        self.middle_tiles = max(2, int(middle_tiles))
        self.start_image = _image("platform_start.png")
        self.middle_image = _image("platform_mid.png")
        self.end_image = _image("platform_end.png")
        self.tile_width = int(96 * PLATFORM_LENGTH_SCALE)
        self.tile_height = 48
        self.width = self.tile_width * (self.middle_tiles + 2)

    def update(self):
        self.x += WORLD_SCROLL_SPEED * _delta_time()
        if self.x > SCREEN_WIDTH:
            _remove(self)

    def draw(self):
        center_y = self.top - self.tile_height / 2
        self.start_image.draw(self.x + self.tile_width / 2, center_y)
        for index in range(self.middle_tiles):
            x = self.x + self.tile_width * (index + 1)
            self.middle_image.draw(x + self.tile_width / 2, center_y)
        self.end_image.draw(
            self.x + self.width - self.tile_width / 2, center_y
        )


class TreasureChest:
    def __init__(self, x, ground_y):
        self.image = _image("chest.png")
        self.x = float(x)
        self.ground_y = float(ground_y)
        self.width = 56
        self.height = 56
        self.collected = False

    def update(self):
        self.x += WORLD_SCROLL_SPEED * _delta_time()
        if self.x - self.width / 2 > SCREEN_WIDTH:
            self.collected = True
            _remove(self)

    def draw(self):
        self.image.draw(self.x, self.ground_y + self.height / 2)


class Projectile:
    def __init__(self, x, y, direction, damage, speed, active_skill=False, angle=0):
        self.image = _image("projectile.png")
        self.x = float(x)
        self.y = float(y)
        self.direction = 1 if direction > 0 else -1
        self.damage = int(damage)
        self.speed = float(speed)
        self.active_skill = active_skill
        self.angle = float(angle)
        self.width = 24
        self.height = 24
        self.alive = True

    def update(self):
        dt = _delta_time()
        self.x += self.direction * self.speed * dt
        self.y += self.angle * self.speed * dt
        if (
            self.x < -self.width
            or self.x > SCREEN_WIDTH + self.width
            or self.y < 0
            or self.y > SCREEN_HEIGHT
        ):
            self.alive = False
            _remove(self)

    def draw(self):
        self.image.draw(self.x, self.y)

    def hit(self):
        if self.alive:
            self.alive = False
            _remove(self)


class StageSpawner:
    def __init__(self):
        self.chest_timer = 4.0
        self.floor_monster_timer = FLOOR_MONSTER_SPAWN_INTERVAL
        self.random = random.Random()
        self.platform_timers = {
            top: self.random.uniform(1.0, 2.0) for top in PLATFORM_HEIGHTS
        }

    def update(self, platforms):
        dt = _delta_time()
        self.chest_timer -= dt
        self.floor_monster_timer -= dt
        if self.floor_monster_timer <= 0:
            if self.random.random() < FLOOR_MONSTER_SPAWN_CHANCE:
                game_world.add_object(
                    Monster(-MONSTER_WIDTH * 2, GROUND_TOP),
                    1,
                )
            self.floor_monster_timer = FLOOR_MONSTER_SPAWN_INTERVAL
        if self.chest_timer <= 0:
            self.spawn_chest(platforms)
            self.chest_timer = CHEST_SPAWN_INTERVAL * self.random.uniform(
                0.8, 1.2
            )
        for top, timer in tuple(self.platform_timers.items()):
            timer -= dt
            if timer <= 0:
                platform = MovingPlatform(0, top, self.random.randint(3, 7))
                platform.x = (
                    -platform.width - self.random.randint(30, 180)
                )
                platforms.append(platform)
                game_world.add_object(platform, 1)
                _spawn_platform_monsters(platform, self.random)
                timer = self.random.uniform(3.0, 5.0)
            self.platform_timers[top] = timer

    def spawn_chest(self, platforms):
        available_platforms = [
            platform
            for platform in platforms
            if platform.x + platform.width > 56
            and platform.x < SCREEN_WIDTH - 28
        ]
        available_layers = [GROUND_TOP]
        available_layers.extend(
            top
            for top in PLATFORM_HEIGHTS
            if any(platform.top == top for platform in available_platforms)
        )
        selected_layer = self.random.choice(available_layers)

        if selected_layer == GROUND_TOP:
            x = -56
        else:
            layer_platforms = [
                platform
                for platform in available_platforms
                if platform.top == selected_layer
            ]
            platform = self.random.choice(layer_platforms)
            left = max(platform.x + 28, 28)
            right = min(platform.x + platform.width - 28, SCREEN_WIDTH - 28)
            x = self.random.uniform(left, right)

        chest = TreasureChest(x, selected_layer)
        game_world.add_object(chest, 1)


def create_initial_platforms():
    platforms = []
    for top in PLATFORM_HEIGHTS:
        for _ in range(2):
            middle_tiles = random.randint(3, 7)
            platform = MovingPlatform(0, top, middle_tiles)
            platform.x = -platform.width - random.randint(30, 300)
            platforms.append(platform)
            game_world.add_object(platform, 1)
            _spawn_platform_monsters(platform, random)
    return platforms


class DeathEffect:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.duration = 0.32
        self.complete = False
        self.rewarded = False

    def update(self):
        self.age += _real_delta_time()
        if self.age >= self.duration:
            self.complete = True

    def draw(self):
        if self.complete:
            return
        progress = self.age / self.duration
        radius = 9 + int(progress * 25)
        alpha = int(255 * (1 - progress))
        draw_circle(self.x, self.y, radius, 255, 195, 106, alpha)
        draw_circle(self.x, self.y, max(2, radius // 2), 255, 111, 95, alpha)
        for direction in (-1, 1):
            draw_line(
                self.x + direction * radius,
                self.y + radius * 0.6,
                self.x + direction * (radius + 12),
                self.y + radius + 14,
                255,
                221,
                146,
                alpha,
            )
