"""Tests for scoring and leaderboard system."""
from __future__ import annotations

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src"))

from scoring import score_run, Score, build_leaderboard, LeaderboardEntry


class TestScoring:
    def test_perfect_survival(self):
        result = {"survived_sols": 500, "alive": True, "morale": 1.0,
                  "reputation": 1.0, "trades_completed": 10,
                  "sols_on_rations": 0, "final_resources": {}}
        s = score_run(result, max_sols=500)
        assert s.survival > 90
        assert s.composite > 50

    def test_early_death(self):
        result = {"survived_sols": 10, "alive": False, "morale": 0.5,
                  "reputation": 0.3, "trades_completed": 0,
                  "sols_on_rations": 5, "final_resources": {}}
        s = score_run(result, max_sols=500)
        assert s.survival < 20
        assert s.composite < 30

    def test_grade_s(self):
        s = Score(survival=95, efficiency=90, morale=95,
                  resilience=90, diplomacy=85, composite=92)
        assert s.grade == "S"

    def test_grade_f(self):
        s = Score(survival=10, efficiency=5, morale=20,
                  resilience=0, diplomacy=0, composite=8)
        assert s.grade == "F"

    def test_survival_nonlinear(self):
        """Surviving 50% of sols should score higher than 50."""
        half = score_run({"survived_sols": 250, "final_resources": {},
                          "morale": 1.0, "sols_on_rations": 0}, max_sols=500)
        quarter = score_run({"survived_sols": 125, "final_resources": {},
                             "morale": 1.0, "sols_on_rations": 0}, max_sols=500)
        assert half.survival > 50  # Nonlinear: 50% survival > 50 score
        assert quarter.survival > 25

    def test_morale_penalty(self):
        high_morale = score_run({"survived_sols": 100, "morale": 1.0,
                                  "sols_on_rations": 0, "final_resources": {}},
                                 max_sols=500)
        low_morale = score_run({"survived_sols": 100, "morale": 0.5,
                                 "sols_on_rations": 50, "final_resources": {}},
                                max_sols=500)
        assert high_morale.morale > low_morale.morale

    def test_diplomacy_rewards_trades(self):
        trader = score_run({"survived_sols": 100, "morale": 1.0,
                            "trades_completed": 20, "reputation": 0.9,
                            "sols_on_rations": 0, "final_resources": {}},
                           max_sols=500)
        hermit = score_run({"survived_sols": 100, "morale": 1.0,
                            "trades_completed": 0, "reputation": 0.2,
                            "sols_on_rations": 0, "final_resources": {}},
                           max_sols=500)
        assert trader.diplomacy > hermit.diplomacy

    def test_sabotage_penalty(self):
        clean = score_run({"survived_sols": 100, "morale": 1.0,
                           "sabotages_attempted": 0, "reputation": 0.5,
                           "trades_completed": 5, "sols_on_rations": 0,
                           "final_resources": {}}, max_sols=500)
        dirty = score_run({"survived_sols": 100, "morale": 1.0,
                           "sabotages_attempted": 5, "reputation": 0.5,
                           "trades_completed": 5, "sols_on_rations": 0,
                           "final_resources": {}}, max_sols=500)
        assert clean.diplomacy > dirty.diplomacy


class TestLeaderboard:
    def test_build_from_benchmark(self):
        benchmark = {"archetypes": {
            "engineer": {"runs": [
                {"survived": 100, "alive": False},
                {"survived": 150, "alive": False},
            ]},
            "wildcard": {"runs": [
                {"survived": 200, "alive": False},
                {"survived": 80, "alive": False},
            ]},
        }}
        entries = build_leaderboard(benchmark, max_sols=500)
        assert len(entries) == 2
        assert all(isinstance(e, LeaderboardEntry) for e in entries)

    def test_leaderboard_sorted_by_score(self):
        benchmark = {"archetypes": {
            "low": {"runs": [{"survived": 50, "alive": False}]},
            "high": {"runs": [{"survived": 400, "alive": False}]},
        }}
        entries = build_leaderboard(benchmark, max_sols=500)
        assert entries[0].archetype == "high"
        assert entries[1].archetype == "low"

    def test_confidence_interval(self):
        benchmark = {"archetypes": {
            "test": {"runs": [
                {"survived": 100, "alive": False},
                {"survived": 120, "alive": False},
                {"survived": 110, "alive": False},
                {"survived": 105, "alive": False},
                {"survived": 115, "alive": False},
            ]},
        }}
        entries = build_leaderboard(benchmark, max_sols=500)
        assert len(entries) == 1
        ci = entries[0].confidence_interval
        assert ci[0] < entries[0].avg_score
        assert ci[1] > entries[0].avg_score
