"""Tests for autonomy enforcement and scoreboard."""
from __future__ import annotations

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src"))

from autonomy import AutonomyEnforcer, AutonomyScoreboard, Phase


class TestAutonomyEnforcer:
    def test_phase1_blocks_override(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        allowed = ae.can_override(10)
        assert not allowed
        assert ae.failed
        assert "intervention" in ae.failure_reason.lower()

    def test_phase1_blocks_supply(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        allowed = ae.can_receive_supply(10)
        assert not allowed
        assert ae.failed

    def test_phase1_blocks_command(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        allowed = ae.can_send_command(10)
        assert not allowed
        assert ae.failed

    def test_phase2_allows_override(self):
        ae = AutonomyEnforcer(phase=Phase.SUPERVISED)
        allowed = ae.can_override(10)
        assert allowed
        assert not ae.failed

    def test_phase2_allows_supply(self):
        ae = AutonomyEnforcer(phase=Phase.SUPERVISED)
        allowed = ae.can_receive_supply(10)
        assert allowed

    def test_tracks_interventions(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        ae.can_override(10)
        ae.can_send_command(20)
        assert len(ae.interventions) == 2
        assert ae.overrides_blocked == 1
        assert ae.commands_blocked == 1

    def test_serialize(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        data = ae.serialize()
        assert data["phase"] == "full_autonomy"
        assert not data["failed"]

    def test_status(self):
        ae = AutonomyEnforcer(phase=Phase.FULL_AUTONOMY)
        status = ae.get_status()
        assert status["phase"] == "full_autonomy"


class TestScoreboard:
    def test_record_run(self):
        sb = AutonomyScoreboard()
        sb.record_run("test", "engineer", 150, True, seed=42)
        assert len(sb.entries) == 1
        assert sb.entries[0]["autonomy_sols"] == 150

    def test_grading(self):
        sb = AutonomyScoreboard()
        sb.record_run("a", "engineer", 500, True)
        sb.record_run("b", "wildcard", 200, False, "O2 depletion")
        sb.record_run("c", "hermit", 30, False, "starvation")
        assert sb.entries[0]["grade"] == "MARS-READY"
        assert sb.entries[1]["grade"] == "A"
        assert sb.entries[2]["grade"] == "D"

    def test_mars_ready(self):
        sb = AutonomyScoreboard()
        sb.record_run("a", "evolved", 500, True)
        data = sb.serialize()
        assert data["mars_ready_count"] == 1
        assert data["best_sols"] == 500

    def test_serialize(self):
        sb = AutonomyScoreboard()
        sb.record_run("a", "engineer", 100, False, "O2")
        sb.record_run("b", "wildcard", 200, False, "food")
        data = sb.serialize()
        assert data["total_runs"] == 2
        assert data["best_sols"] == 200
        assert len(data["leaderboard"]) == 2

    def test_sort_order(self):
        sb = AutonomyScoreboard()
        sb.record_run("low", "hermit", 50, False)
        sb.record_run("high", "contrarian", 300, True)
        sb.record_run("mid", "engineer", 150, False)
        data = sb.serialize()
        assert data["leaderboard"][0]["autonomy_sols"] == 300
        assert data["leaderboard"][-1]["autonomy_sols"] == 50
