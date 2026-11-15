from stage_config import AIM_TIME_SCALE


def simulation_scale(is_aiming: bool) -> float:
    return AIM_TIME_SCALE if is_aiming else 1.0


def aim_direction(mouse_x: float, character_x: float) -> int:
    return 1 if mouse_x > character_x else -1


def award_experience(current_xp: int, amount: int, threshold: int) -> tuple[int, int]:
    if amount < 0:
        raise ValueError("Experience amount cannot be negative")
    if threshold <= 0:
        raise ValueError("Experience threshold must be positive")

    total = current_xp + amount
    levels_gained, remaining_xp = divmod(total, threshold)
    return remaining_xp, levels_gained


def intersects(
    left_a: float,
    bottom_a: float,
    right_a: float,
    top_a: float,
    left_b: float,
    bottom_b: float,
    right_b: float,
    top_b: float,
) -> bool:
    return (
        left_a < right_b
        and right_a > left_b
        and bottom_a < top_b
        and top_a > bottom_b
    )
