import unittest

from stage_rules import aim_direction, award_experience, intersects, simulation_scale


class StageRulesTests(unittest.TestCase):
    def test_aiming_halves_simulation_time(self):
        self.assertEqual(simulation_scale(True), 0.5)
        self.assertEqual(simulation_scale(False), 1.0)

    def test_aim_direction_points_right_only_when_cursor_is_right(self):
        self.assertEqual(aim_direction(401, 400), 1)
        self.assertEqual(aim_direction(400, 400), -1)
        self.assertEqual(aim_direction(399, 400), -1)

    def test_experience_preserves_remainder_and_multiple_levelups(self):
        self.assertEqual(award_experience(80, 45, 100), (25, 1))
        self.assertEqual(award_experience(90, 225, 100), (15, 3))

    def test_intersection_requires_positive_area_overlap(self):
        self.assertTrue(intersects(0, 0, 10, 10, 9, 9, 20, 20))
        self.assertFalse(intersects(0, 0, 10, 10, 10, 0, 20, 10))
        self.assertFalse(intersects(0, 0, 10, 10, 0, 10, 10, 20))


if __name__ == "__main__":
    unittest.main()
