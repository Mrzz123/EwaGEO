import datetime
import unittest

from liewa.liewa_cli.full_disks import get_sun_times, resolve_color_mode


UTC = datetime.timezone.utc


class AdaptiveColorTests(unittest.TestCase):
    def test_liaoning_summer_sun_times_are_reasonable(self):
        sunrise, sunset, status = get_sun_times(
            datetime.date(2026, 6, 21), 41.237411, 122.995547
        )
        self.assertEqual("normal", status)
        # UTC+8 gives approximately 04:15 sunrise and 19:24 sunset.
        self.assertEqual(datetime.date(2026, 6, 20), sunrise.date())
        self.assertTrue(datetime.time(19, 30) < sunrise.time() < datetime.time(21, 0))
        self.assertTrue(datetime.time(10, 30) < sunset.time() < datetime.time(12, 30))

    def test_adaptive_mode_changes_around_the_selected_location(self):
        daylight = datetime.datetime(2026, 6, 21, 4, 0, tzinfo=UTC)
        night = datetime.datetime(2026, 6, 21, 16, 0, tzinfo=UTC)
        self.assertEqual(
            "natural_color",
            resolve_color_mode(
                "adaptive", daylight, 41.237411, 122.995547, "Liaoning"
            ),
        )
        self.assertEqual(
            "geocolor",
            resolve_color_mode(
                "adaptive", night, 41.237411, 122.995547, "Liaoning"
            ),
        )

    def test_same_utc_time_can_differ_by_location(self):
        instant = datetime.datetime(2026, 6, 21, 4, 0, tzinfo=UTC)
        self.assertEqual(
            "natural_color",
            resolve_color_mode(
                "adaptive", instant, 41.237411, 122.995547, "Liaoning"
            ),
        )
        self.assertEqual(
            "geocolor",
            resolve_color_mode(
                "adaptive", instant, 40.7128, -74.0060, "New York"
            ),
        )

    def test_polar_day_and_night_are_handled(self):
        self.assertEqual(
            "natural_color",
            resolve_color_mode(
                "adaptive",
                datetime.datetime(2026, 6, 21, 12, tzinfo=UTC),
                78.2232,
                15.6469,
                "Svalbard",
            ),
        )
        self.assertEqual(
            "geocolor",
            resolve_color_mode(
                "adaptive",
                datetime.datetime(2026, 12, 21, 12, tzinfo=UTC),
                78.2232,
                15.6469,
                "Svalbard",
            ),
        )


if __name__ == "__main__":
    unittest.main()
