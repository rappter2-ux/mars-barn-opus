"""Tests for geology, economy, disasters, conversations."""
from __future__ import annotations

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src"))


class TestGeology:
    def test_survey_tick(self):
        from geology import GeologySurvey
        gs = GeologySurvey()
        events = []
        for sol in range(200):
            events.extend(gs.tick(sol, rover_count=2))
        assert gs.survey_progress > 0
        assert len(gs.discoveries) > 0

    def test_discovery_bonus(self):
        from geology import GeologySurvey, Discovery
        gs = GeologySurvey()
        gs.discoveries.append(Discovery("ice_deposit", "Ice", "", 10, (5, 5),
                                         {"passive_h2o": 2.0}))
        assert gs.get_bonus("passive_h2o") == 2.0

    def test_serialize(self):
        from geology import GeologySurvey
        gs = GeologySurvey()
        gs.tick(1)
        data = gs.serialize()
        assert "discoveries" in data
        assert "survey_progress" in data


class TestEconomy:
    def test_tick(self):
        from economy import Economy
        econ = Economy()
        events = econ.tick(1, crew_count=4, module_count=2, research_count=1)
        assert econ.balance != 10000  # Changed
        assert isinstance(events, list)

    def test_deficit_warning(self):
        from economy import Economy
        econ = Economy(balance=-100)
        events = econ.tick(1, 4, 5, 0)
        assert any("DEFICIT" in e for e in events)

    def test_serialize(self):
        from economy import Economy
        econ = Economy()
        econ.tick(1, 4, 2, 1)
        data = econ.serialize()
        assert "balance" in data
        assert "exchange_rates" in data


class TestDisasters:
    def test_scenario_serialize(self):
        from disasters import SCENARIOS
        s = SCENARIOS["dust_hell"]
        data = s.serialize()
        assert data["name"] == "Dust Hell"
        assert data["events"] == 5

    def test_scenario_url_roundtrip(self):
        from disasters import SCENARIOS, Scenario
        orig = SCENARIOS["cascade_crisis"]
        url = orig.to_url_param()
        restored = Scenario.from_url_param(url)
        assert restored.name == orig.name
        assert len(restored.events) == len(orig.events)

    def test_post_mortem(self):
        from disasters import PostMortem
        pm = PostMortem("Test Colony", 100, "O2 depletion")
        history = [{"frame": i, "delta": {"o2": -0.5, "food": -100},
                    "events": [], "crew_events": [], "o2_days": 30 - i * 0.3,
                    "food_days": 30, "visual": {"alert": "nominal"},
                    "crew_alive": 4} for i in range(100)]
        pm.generate(history)
        assert pm.critical_sol > 0
        assert len(pm.mistakes) > 0
        assert len(pm.recommendations) > 0
        text = pm.to_text()
        assert "POST-MORTEM" in text

    def test_all_scenarios_valid(self):
        from disasters import SCENARIOS
        for name, s in SCENARIOS.items():
            assert s.name
            assert len(s.events) > 0
            assert s.difficulty in ("easy", "medium", "hard", "nightmare")


class TestConversations:
    def test_generate_conversation(self):
        from conversations import generate_conversation
        crew = [
            {"name": "Chen W.", "role": "CMDR", "hp": 90, "mor": 80, "alive": True},
            {"name": "Rodriguez M.", "role": "ENGR", "hp": 85, "mor": 75, "alive": True},
        ]
        state = {"morale": 0.8}
        # Run enough sols to get at least one conversation
        convos = []
        for sol in range(50):
            c = generate_conversation(crew, state, [], sol)
            if c:
                convos.append(c)
        assert len(convos) > 0
        assert "dialogue" in convos[0]
        assert len(convos[0]["dialogue"]) >= 2

    def test_no_conversation_with_one_crew(self):
        from conversations import generate_conversation
        crew = [{"name": "Solo", "role": "CMDR", "hp": 90, "mor": 80, "alive": True}]
        result = generate_conversation(crew, {"morale": 0.8}, [], 42)
        assert result is None

    def test_crisis_context(self):
        from conversations import generate_conversation
        crew = [
            {"name": "A", "role": "CMDR", "hp": 50, "mor": 20, "alive": True},
            {"name": "B", "role": "ENGR", "hp": 40, "mor": 15, "alive": True},
        ]
        convos = []
        for sol in range(100):
            c = generate_conversation(crew, {"morale": 0.15}, [], sol)
            if c:
                convos.append(c)
        crisis_convos = [c for c in convos if c["context"] == "crisis"]
        assert len(crisis_convos) > 0
