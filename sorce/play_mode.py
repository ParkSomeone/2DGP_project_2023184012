import game_framework
import game_world
from pico2d import (
    SDL_BUTTON_LEFT,
    SDL_BUTTON_RIGHT,
    SDL_KEYDOWN,
    SDL_MOUSEBUTTONDOWN,
    SDL_MOUSEMOTION,
    SDL_QUIT,
    SDLK_ESCAPE,
    SDLK_e,
    SDLK_q,
    SDLK_r,
    SDLK_w,
    get_events,
    update_canvas,
    clear_canvas,
)

from player import Player
from boss import Boss
from monster import Monster
from stage_config import (
    ACTIVE_SKILLS,
    AIM_MAX_DURATION,
    AUTO_ATTACK_DAMAGE,
    AUTO_ATTACK_RANGE,
    AUTO_ATTACK_SPEED,
    GROUND_TOP,
    MAX_FRAME_DELTA,
    PLAYER_XP_PER_MONSTER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STAGE_DURATION,
    CHEST_UPGRADE_TOKENS,
)
from stage_objects import (
    DeathEffect,
    Ground,
    Projectile,
    ScrollingBackground,
    StageSpawner,
    TreasureChest,
    create_initial_platforms,
)
from stage_rules import intersects, simulation_scale
from stage_ui import draw_hud, draw_text


_PLAYER_SKILL_KEYS = {
    SDLK_w: "w",
    SDLK_e: "e",
    SDLK_r: "r",
}

_player = None
_boss = None
_spawner = None
_platforms = []
_stage_events = []
_mouse_x = SCREEN_WIDTH / 2
_mouse_y = SCREEN_HEIGHT / 2
_remaining_time = STAGE_DURATION
_outcome = None
_aim_elapsed = 0.0


def consume_events():
    pending = list(_stage_events)
    _stage_events.clear()
    return pending


def _emit_event(event_type, **payload):
    _stage_events.append({"type": event_type, **payload})


def _objects_of_type(object_type):
    for layer in game_world.world:
        for obj in tuple(layer):
            if isinstance(obj, object_type):
                yield obj


def _set_mouse_position(x, y):
    global _mouse_x, _mouse_y
    _mouse_x = max(0, min(SCREEN_WIDTH, float(x)))
    _mouse_y = max(0, min(SCREEN_HEIGHT, float(y)))
    if _player is not None and _player.state == "AIM":
        _player.set_aim_target(_mouse_x, _mouse_y)


def _start_aim(skill_key):
    global _aim_elapsed
    if _player.start_aiming(skill_key, _mouse_x, _mouse_y):
        _aim_elapsed = 0.0
        return True
    return False


def _fire_active_skill():
    global _aim_elapsed
    skill_key = _player.selected_skill
    if _player.state != "AIM" or skill_key not in ACTIVE_SKILLS:
        return

    _aim_elapsed = 0.0
    skill = ACTIVE_SKILLS[skill_key]
    origin_x = _player.x + _player.aim_direction * 26
    origin_y = _player.y + _player.height * 0.68
    horizontal_distance = max(abs(_mouse_x - _player.x), 1.0)
    slope = (_mouse_y - origin_y) / horizontal_distance
    spread = (-0.12, 0.0, 0.12) if skill["count"] == 3 else (0.0,)
    for angle_offset in spread:
        game_world.add_object(
            Projectile(
                origin_x,
                origin_y,
                _player.aim_direction,
                skill["damage"],
                skill["speed"],
                active_skill=True,
                angle=slope + angle_offset,
            ),
            1,
        )
    _player.cooldowns[skill_key] = skill["cooldown"]
    _player.selected_skill = None
    _player.cancel_aim()


def init():
    global _player, _boss, _spawner, _platforms
    global _remaining_time, _outcome, _stage_events, _aim_elapsed

    game_world.clear()
    _stage_events = []
    _remaining_time = STAGE_DURATION
    _outcome = None
    _aim_elapsed = 0.0
    game_framework.simulation_scale = 1.0

    game_world.add_object(ScrollingBackground(), 0)
    game_world.add_object(Ground(), 0)
    _boss = Boss()
    game_world.add_object(_boss, 1)
    _platforms = create_initial_platforms()
    _player = Player()
    game_world.add_object(_player, 1)
    _spawner = StageSpawner()


def handle_events():
    global _outcome, _aim_elapsed

    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return

        if event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            if _player is not None and _player.state == "AIM":
                _player.cancel_aiming()
                _aim_elapsed = 0.0
            else:
                game_framework.quit()
                return

        if event.type == SDL_KEYDOWN and event.key in _PLAYER_SKILL_KEYS:
            if _player is not None and _outcome is None:
                _start_aim(_PLAYER_SKILL_KEYS[event.key])

        elif event.type == SDL_KEYDOWN and event.key == SDLK_q:
            if _player is not None and _outcome is None:
                _player.use_potion()

        elif event.type == SDL_MOUSEMOTION:
            _set_mouse_position(
                event.x, SCREEN_HEIGHT - float(event.y)
            )

        elif event.type == SDL_MOUSEBUTTONDOWN:
            _set_mouse_position(
                event.x, SCREEN_HEIGHT - float(event.y)
            )
            if event.button == SDL_BUTTON_LEFT:
                if _player is not None and _outcome is None:
                    _fire_active_skill()
            elif event.button == SDL_BUTTON_RIGHT:
                if _player is not None:
                    _player.cancel_aiming()
                    _aim_elapsed = 0.0

        if _player is not None and _outcome is None:
            _player.handle_event(event)


def _player_box():
    return (
        _player.left,
        _player.bottom,
        _player.right,
        _player.top,
    )


def _object_box(obj):
    return (
        obj.x - obj.width / 2,
        obj.ground_y,
        obj.x + obj.width / 2,
        obj.ground_y + obj.height,
    )


def _resolve_platform_landing():
    active_platforms = [
        platform for platform in _platforms
        if platform in game_world.world[1]
    ]
    _platforms[:] = active_platforms

    if _player.drop_requested:
        _player.drop_requested = False
        if _player.grounded and _player.y > GROUND_TOP:
            platform = next(
                (
                    candidate for candidate in active_platforms
                    if _player.right > candidate.x
                    and _player.left < candidate.x + candidate.width
                    and abs(_player.y - candidate.top) < 1
                ),
                None,
            )
            if platform is not None:
                _player.drop_through_platform = platform
                _player.grounded = False

    ignored_platform = _player.drop_through_platform
    if ignored_platform is not None and (
        ignored_platform not in active_platforms
        or _player.top < ignored_platform.top
    ):
        _player.drop_through_platform = None

    if _player.grounded and _player.y > GROUND_TOP:
        standing = any(
            _player.right > platform.x
            and _player.left < platform.x + platform.width
            and abs(_player.y - platform.top) < 1
            for platform in active_platforms
        )
        if not standing:
            _player.grounded = False

    if _player.grounded or _player.velocity_y > 0:
        return

    for platform in active_platforms:
        if platform is _player.drop_through_platform:
            continue
        horizontal_overlap = (
            _player.right > platform.x
            and _player.left < platform.x + platform.width
        )
        crossed_top = (
            _player.previous_y >= platform.top
            and _player.y <= platform.top
        )
        if horizontal_overlap and crossed_top:
            _player.land_on(platform.top)
            return


def _emit_upgrade_event(source, tokens):
    if tokens <= 0:
        return
    _emit_event(
        "upgrade_requested",
        source=source,
        tokens=tokens,
        total_tokens=_player.upgrade_tokens,
    )


def _resolve_projectile_hits():
    monsters = tuple(_objects_of_type(Monster))
    for projectile in tuple(_objects_of_type(Projectile)):
        if not projectile.alive:
            continue
        projectile_box = (
            projectile.x - projectile.width / 2,
            projectile.y - projectile.height / 2,
            projectile.x + projectile.width / 2,
            projectile.y + projectile.height / 2,
        )
        hit_target = False
        for monster in monsters:
            if not monster.alive:
                continue
            if intersects(*projectile_box, *_object_box(monster)):
                killed = monster.take_damage(projectile.damage)
                projectile.hit()
                hit_target = True
                if killed:
                    game_world.add_object(
                        DeathEffect(
                            monster.x,
                            monster.ground_y + monster.height / 2,
                        ),
                        1,
                    )
                break

        if (
            not hit_target
            and projectile.alive
            and projectile.active_skill
            and _boss.alive
            and intersects(
                *projectile_box,
                _boss.x - _boss.width / 2,
                _boss.ground_y,
                _boss.x + _boss.width / 2,
                _boss.ground_y + _boss.height,
            )
        ):
            defeated = _boss.take_damage(
                projectile.damage,
                active_skill=True,
            )
            projectile.hit()
            if defeated:
                _finish_stage("boss_defeated")


def _award_monster_experience():
    levels_gained = _player.add_experience(PLAYER_XP_PER_MONSTER)
    _emit_event(
        "monster_defeated",
        experience=PLAYER_XP_PER_MONSTER,
        levels_gained=levels_gained,
    )
    if levels_gained:
        _emit_upgrade_event("level_up", levels_gained)


def _resolve_death_effects():
    for effect in tuple(_objects_of_type(DeathEffect)):
        if effect.complete and not effect.rewarded:
            effect.rewarded = True
            game_world.remove_object(effect)
            _award_monster_experience()


def _try_auto_attack():
    if not _player.alive or not _player.next_auto_attack_ready():
        return

    target = None
    closest_distance = AUTO_ATTACK_RANGE
    for monster in _objects_of_type(Monster):
        distance = _player.x - monster.x
        if 0 < distance < closest_distance:
            closest_distance = distance
            target = monster
    if target is None:
        _player.auto_attack_timer = 0.2
        return

    origin_y = _player.y + _player.height * 0.68
    target_y = target.ground_y + target.height * 0.55
    slope = (target_y - origin_y) / max(1.0, _player.x - target.x)
    game_world.add_object(
        Projectile(
            _player.x - 26,
            origin_y,
            -1,
            AUTO_ATTACK_DAMAGE,
            AUTO_ATTACK_SPEED,
            angle=slope,
        ),
        1,
    )


def _resolve_actor_collisions():
    player_box = _player_box()
    if _boss.alive and intersects(
        *player_box,
        _boss.x - _boss.width / 2,
        _boss.ground_y,
        _boss.x + _boss.width / 2,
        _boss.ground_y + _boss.height,
    ):
        _player.touch_boss()

    if not _player.alive:
        _finish_stage("player_died")
        return

    for monster in tuple(_objects_of_type(Monster)):
        if intersects(*player_box, *_object_box(monster)):
            _player.take_monster_damage()
            if not _player.alive:
                _finish_stage("player_died")
                return

    for chest in tuple(_objects_of_type(TreasureChest)):
        if chest.collected:
            continue
        if intersects(*player_box, *_object_box(chest)):
            chest.collected = True
            game_world.remove_object(chest)
            _player.add_upgrade_token(CHEST_UPGRADE_TOKENS)
            _emit_event(
                "chest_collected",
                upgrade_tokens=CHEST_UPGRADE_TOKENS,
            )
            _emit_upgrade_event("chest", CHEST_UPGRADE_TOKENS)


def _finish_stage(outcome):
    global _outcome
    if _outcome is not None:
        return
    _outcome = outcome
    game_framework.simulation_scale = 1.0
    _emit_event(outcome)


def update():
    global _remaining_time, _aim_elapsed

    dt = min(MAX_FRAME_DELTA, max(0.0, game_framework.frame_time))
    game_framework.frame_time = dt
    if _outcome is not None:
        return

    if _player.state == "AIM":
        _aim_elapsed += dt
        if _aim_elapsed >= AIM_MAX_DURATION - 1e-9:
            _fire_active_skill()
    else:
        _aim_elapsed = 0.0

    game_framework.simulation_scale = simulation_scale(
        _player.state == "AIM"
    )
    game_world.update()
    scaled_dt = dt * game_framework.simulation_scale
    _remaining_time = max(0.0, _remaining_time - scaled_dt)

    _resolve_platform_landing()
    _resolve_actor_collisions()
    if _outcome is not None:
        return

    _resolve_death_effects()
    _spawner.update(_platforms)
    _try_auto_attack()
    _resolve_projectile_hits()
    if _outcome is not None:
        return

    if _remaining_time <= 0:
        _finish_stage("survived")


def render():
    clear_canvas()
    game_world.render()
    if _player is not None and _boss is not None:
        draw_hud(
            _player,
            _boss,
            _remaining_time,
            _stage_events,
            _outcome,
        )
        if _outcome is None:
            draw_text(
                "A/D MOVE  SPACE JUMP  S+SPACE DROP  W/E/R AIM  Q HEAL",
                SCREEN_WIDTH // 2 - 270,
                SCREEN_HEIGHT - 32,
                2,
                (237, 223, 199),
            )
    update_canvas()


def pause():
    pass


def resume():
    pass


def finish():
    global _player, _boss, _spawner, _platforms
    game_framework.simulation_scale = 1.0
    game_world.clear()
    _player = None
    _boss = None
    _spawner = None
    _platforms = []
