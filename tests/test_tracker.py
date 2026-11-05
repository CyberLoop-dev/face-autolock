import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from autolock import PresenceTracker  # noqa: E402


class TrackerTests(unittest.TestCase):
    def test_never_locks_an_empty_room(self):
        t = PresenceTracker(away_seconds=10)
        events = [t.update(s, face=False, body=False) for s in range(0, 120)]
        self.assertNotIn("lock", events)

    def test_locks_once_after_human_leaves(self):
        t = PresenceTracker(away_seconds=10)
        self.assertEqual(t.update(0, True, False), "armed")
        events = [t.update(s, False, False) for s in range(1, 60)]
        self.assertEqual(events.count("lock"), 1)
        self.assertEqual(events.index("lock"), 11 - 1)  # first second > 10s of absence

    def test_looking_away_does_not_lock(self):
        t = PresenceTracker(away_seconds=10, body_grace=60)
        t.update(0, True, False)
        # face lost, but the upper body is still visible
        events = [t.update(s, False, True) for s in range(1, 50)]
        self.assertNotIn("lock", events)

    def test_body_only_stops_counting_after_grace(self):
        t = PresenceTracker(away_seconds=10, body_grace=60)
        t.update(0, True, False)
        events = [t.update(s, False, True) for s in range(1, 120)]
        self.assertIn("lock", events)

    def test_darkness_never_counts_as_leaving(self):
        t = PresenceTracker(away_seconds=10)
        t.update(0, True, False)
        events = [t.update(s, False, False, can_see=False) for s in range(1, 200)]
        self.assertNotIn("lock", events)

    def test_rearms_when_human_returns(self):
        t = PresenceTracker(away_seconds=10)
        t.update(0, True, False)
        [t.update(s, False, False) for s in range(1, 30)]
        self.assertFalse(t.armed)
        self.assertEqual(t.update(40, True, False), "armed")
        events = [t.update(s, False, False) for s in range(41, 80)]
        self.assertEqual(events.count("lock"), 1)


if __name__ == "__main__":
    unittest.main()
