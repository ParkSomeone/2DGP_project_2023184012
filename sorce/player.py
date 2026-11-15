import os

import game_framework
from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_SPACE,
    SDLK_a,
    SDLK_d,
    SDLK_s,
    draw_circle,
    draw_line,
    load_image,
)
from transitions import Machine

from stage_config import (
    GRAVITY,
    GROUND_TOP,
    PLAYER_HEIGHT,
    PLAYER_INVULNERABLE_DURATION,
    PLAYER_JUMP_VELOCITY,
    PLAYER_MAX_HP,
    PLAYER_SPEED,
    PLAYER_START_POTIONS,
    PLAYER_START_X,
    PLAYER_WIDTH,
    SCREEN_WIDTH,
    WORLD_SCROLL_SPEED,
    XP_REQUIRED_PER_LEVEL,
    LEVEL_UPGRADE_TOKENS,
    MONSTER_DAMAGE_RATIO,
    PLAYER_HITSTUN_DURATION,
)
from stage_rules import aim_direction, award_experience


_image_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "image", "player_run.png")
)


class Player:
    def __init__(self):
        self.image = load_image(_image_path)
        self.x = float(PLAYER_START_X)
        self.y = float(GROUND_TOP)
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.speed = PLAYER_SPEED
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.level = 1
        self.experience = 0
        self.potions = PLAYER_START_POTIONS
        self.upgrade_tokens = 0
        self.cooldowns = {"w": 0.0, "e": 0.0, "r": 0.0}
        self.passive_slots = [0.0, 0.0, 0.0]
        self.auto_attack_timer = 0.5
        self.invulnerable_timer = 0.0
        self.hitstun_timer = 0.0
        self.knockback_speed = WORLD_SCROLL_SPEED
        self.velocity_y = 0.0
        self.grounded = True
        self.previous_y = self.y
        self.jump_requested = False
        self.drop_requested = False
        self.drop_through_platform = None
        self.move_direction = 0
        self.pressed_keys = set()
        self.animation_time = 0.0
        self.selected_skill = None
        self.aim_direction = -1
        self.aim_mouse_x = self.x - 100
        self.aim_mouse_y = self.y + self.height * 0.7
        self.death_reported = False

        self.machine = Machine(
            model=self,
            states=("RUN", "AIM", "HITSTUN", "DEAD"),
            initial="RUN",
            auto_transitions=False,
            transitions=(
                {"trigger": "begin_aim", "source": "RUN", "dest": "AIM"},
                {"trigger": "cancel_aim", "source": "AIM", "dest": "RUN"},
                {
                    "trigger": "start_hitstun",
                    "source": ("RUN", "AIM"),
                    "dest": "HITSTUN",
                },
                {"trigger": "recover", "source": "HITSTUN", "dest": "RUN"},
                {
                    "trigger": "transition_to_dead",
                    "source": ("RUN", "AIM", "HITSTUN"),
                    "dest": "DEAD",
                },
            ),
        )

    @property
    def left(self):
        return self.x - self.width / 2

    @property
    def right(self):
        return self.x + self.width / 2

    @property
    def bottom(self):
        return self.y

    @property
    def top(self):
        return self.y + self.height

    @property
    def alive(self):
        return self.state != "DEAD"

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            self.pressed_keys.add(event.key)
            if event.key == SDLK_SPACE:
                if SDLK_s in self.pressed_keys:
                    self.drop_requested = True
                else:
                    self.jump_requested = True
        elif event.type == SDL_KEYUP:
            self.pressed_keys.discard(event.key)
        if SDLK_d in self.pressed_keys:
            self.move_direction = 1
        elif SDLK_a in self.pressed_keys:
            self.move_direction = -1
        else:
            self.move_direction = 0

    def set_aim_target(self, mouse_x, mouse_y):
        self.aim_mouse_x = float(mouse_x)
        self.aim_mouse_y = float(mouse_y)
        self.aim_direction = aim_direction(self.aim_mouse_x, self.x)

    def can_use_skill(self, key):
        return (
            self.alive
            and self.state == "RUN"
            and key in self.cooldowns
            and self.cooldowns[key] <= 0
        )

    def start_aiming(self, key, mouse_x, mouse_y):
        if not self.can_use_skill(key):
            return False
        self.selected_skill = key
        self.set_aim_target(mouse_x, mouse_y)
        self.begin_aim()
        return True

    def cancel_aiming(self):
        if self.state != "AIM":
            return False
        self.selected_skill = None
        self.cancel_aim()
        return True

    def take_monster_damage(self):
        if not self.alive or self.invulnerable_timer > 0:
            return False
        self.hp = max(0.0, self.hp - self.max_hp * MONSTER_DAMAGE_RATIO)
        self.invulnerable_timer = PLAYER_INVULNERABLE_DURATION
        self.hitstun_timer = PLAYER_HITSTUN_DURATION
        self.selected_skill = None
        if self.hp <= 0:
            self.transition_to_dead()
        else:
            self.start_hitstun()
        return True

    def touch_boss(self):
        if not self.alive:
            return False
        self.hp = 0.0
        self.selected_skill = None
        self.transition_to_dead()
        return True

    def add_experience(self, amount):
        self.experience, levels_gained = award_experience(
            self.experience, amount, XP_REQUIRED_PER_LEVEL
        )
        if levels_gained:
            self.level += levels_gained
            self.upgrade_tokens += LEVEL_UPGRADE_TOKENS * levels_gained
        return levels_gained

    def collect_chest(self):
        self.upgrade_tokens += 2

    def use_potion(self):
        if not self.alive or self.potions <= 0 or self.hp >= self.max_hp:
            return False
        self.potions -= 1
        self.hp = min(self.max_hp, self.hp + self.max_hp * 0.5)
        return True

    def update(self):
        dt = game_framework.frame_time
        movement_dt = dt * game_framework.simulation_scale
        if dt <= 0 or not self.alive:
            return

        self.previous_y = self.y
        self.animation_time += dt
        self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        for key in self.cooldowns:
            self.cooldowns[key] = max(0.0, self.cooldowns[key] - dt)
        self.auto_attack_timer -= dt
        self.passive_slots = [max(0.0, value - dt) for value in self.passive_slots]

        if self.state == "HITSTUN":
            self.x += self.knockback_speed * movement_dt
            self.hitstun_timer -= dt
            if self.hitstun_timer <= 0:
                self.recover()
        elif self.move_direction:
            self.x += self.move_direction * self.speed * movement_dt

        self.x = min(SCREEN_WIDTH - self.width / 2, max(self.width / 2, self.x))

        if self.jump_requested:
            if self.grounded and self.state in ("RUN", "AIM"):
                self.velocity_y = PLAYER_JUMP_VELOCITY
                self.grounded = False
            self.jump_requested = False

        if not self.grounded:
            self.y += self.velocity_y * movement_dt
            self.velocity_y -= GRAVITY * movement_dt
            if self.y <= GROUND_TOP:
                self.y = GROUND_TOP
                self.velocity_y = 0.0
                self.grounded = True

    def land_on(self, platform_top):
        self.y = float(platform_top)
        self.velocity_y = 0.0
        self.grounded = True

    def draw(self):
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 12) % 2:
            return
        frame = int(self.animation_time * 10) % 4
        self.image.clip_composite_draw(
            frame * 64,
            0,
            64,
            96,
            0,
            "h" if self.state == "AIM" and self.aim_direction > 0 else "",
            self.x,
            self.y + self.height / 2,
            self.width,
            self.height,
        )
        if self.state == "AIM":
            draw_line(
                self.x,
                self.y + self.height * 0.65,
                self.aim_mouse_x,
                self.aim_mouse_y,
                255,
                222,
                145,
                180,
            )
            draw_circle(
                self.aim_mouse_x,
                self.aim_mouse_y,
                12,
                255,
                220,
                136,
                230,
            )

    def add_upgrade_token(self, count):
        self.upgrade_tokens += max(0, int(count))

    def next_auto_attack_ready(self):
        if self.auto_attack_timer > 0:
            return False
        self.auto_attack_timer = 1.1
        return True
