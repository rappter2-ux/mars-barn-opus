"""Tests for colony module expansion system."""
from __future__ import annotations

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src"))

from modules import (
    ColonyBase, BuiltModule, ConstructionProject, MODULES,
    governor_build_decision, ModuleType,
)
from colony import Resources, create_colony, Allocation, step


class TestModuleCatalog:
    def test_all_modules_have_required_fields(self):
        for slug, bp in MODULES.items():
            assert bp.name, f"{slug} missing name"
            assert bp.build_sols > 0, f"{slug} invalid build_sols"
            assert isinstance(bp.effects, dict), f"{slug} missing effects"
            assert bp.max_count >= 1, f"{slug} invalid max_count"

    def test_module_count(self):
        assert len(MODULES) >= 8


class TestColonyBase:
    def test_empty_base(self):
        base = ColonyBase()
        assert len(base.modules) == 0
        assert base.construction is None
        assert not base.has_module("greenhouse_dome")

    def test_build_module(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=300000, power_kwh=500)
        err = base.start_construction("greenhouse_dome", r, 10)
        assert err is None
        assert base.construction is not None
        assert base.construction.module_type == "greenhouse_dome"
        assert r.power_kwh < 500  # Power deducted

    def test_cant_build_during_construction(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=300000, power_kwh=1000)
        base.start_construction("greenhouse_dome", r, 10)
        can, reason = base.can_build("solar_farm", r)
        assert not can
        assert "Already building" in reason

    def test_construction_completes(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=300000, power_kwh=500)
        base.start_construction("solar_farm", r, 10)
        # Tick through build time (solar_farm = 8 sols)
        events = []
        for sol in range(10, 20):
            events.extend(base.tick(sol))
        assert base.has_module("solar_farm")
        assert any("COMPLETE" in e for e in events)
        assert base.construction is None

    def test_max_count_enforced(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=500, food_kcal=500000, power_kwh=2000)
        # Greenhouse has max_count=1
        base.modules.append(BuiltModule(module_type="greenhouse_dome"))
        can, reason = base.can_build("greenhouse_dome", r)
        assert not can
        assert "Max" in reason

    def test_solar_farm_stacks(self):
        base = ColonyBase()
        # Solar farm has max_count=3
        base.modules.append(BuiltModule(module_type="solar_farm"))
        base.modules.append(BuiltModule(module_type="solar_farm"))
        r = Resources(power_kwh=500)
        can, _ = base.can_build("solar_farm", r)
        assert can  # Can build 3rd

    def test_get_bonus(self):
        base = ColonyBase()
        base.modules.append(BuiltModule(module_type="greenhouse_dome"))
        bonus = base.get_bonus("greenhouse_bonus")
        assert bonus == 0.50

    def test_stacked_bonus(self):
        base = ColonyBase()
        base.modules.append(BuiltModule(module_type="solar_farm"))
        base.modules.append(BuiltModule(module_type="solar_farm"))
        bonus = base.get_bonus("solar_bonus")
        assert abs(bonus - 0.80) < 0.01  # 2 x 0.40

    def test_damaged_module_reduced_bonus(self):
        base = ColonyBase()
        m = BuiltModule(module_type="greenhouse_dome", health=0.5)
        base.modules.append(m)
        bonus = base.get_bonus("greenhouse_bonus")
        assert abs(bonus - 0.25) < 0.01  # 0.50 * 0.5 health

    def test_serialize(self):
        base = ColonyBase()
        base.modules.append(BuiltModule(module_type="solar_farm", built_sol=15))
        data = base.serialize()
        assert "modules" in data
        assert "bonuses" in data
        assert len(data["modules"]) == 1


class TestGovernorBuildDecision:
    def test_builds_greenhouse_when_food_low(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=30000, power_kwh=500)
        choice = governor_build_decision(base, r, 30, 0.0)
        assert choice == "greenhouse_dome"

    def test_builds_isru_when_o2_low(self):
        base = ColonyBase()
        base.modules.append(BuiltModule(module_type="greenhouse_dome"))
        r = Resources(o2_kg=10, h2o_liters=300, food_kcal=300000, power_kwh=500)
        choice = governor_build_decision(base, r, 30, 0.0)
        assert choice == "isru_plant"

    def test_no_build_during_crisis(self):
        base = ColonyBase()
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=300000, power_kwh=500)
        choice = governor_build_decision(base, r, 30, 0.8)
        assert choice is None

    def test_no_build_when_already_building(self):
        base = ColonyBase()
        base.construction = ConstructionProject("solar_farm", 5, 8)
        r = Resources(o2_kg=100, h2o_liters=300, food_kcal=300000, power_kwh=500)
        choice = governor_build_decision(base, r, 30, 0.0)
        assert choice is None


class TestColonyIntegration:
    def test_colony_with_base(self):
        colony = create_colony("Test")
        colony.base = ColonyBase()
        alloc = Allocation(heating_fraction=0.25, isru_fraction=0.40,
                           greenhouse_fraction=0.35)
        for _ in range(30):
            if not colony.alive:
                break
            step(colony, 300.0, 200.0, alloc)
        # Should have attempted to build something by sol 30
        assert colony.sol >= 20

    def test_modules_boost_production(self):
        # Colony with greenhouse dome should produce more food
        c1 = create_colony("NoModules")
        c2 = create_colony("WithModules")
        c2.base = ColonyBase()
        c2.base.modules.append(BuiltModule(module_type="greenhouse_dome"))
        alloc = Allocation(heating_fraction=0.20, isru_fraction=0.40,
                           greenhouse_fraction=0.40)
        step(c1, 300.0, 200.0, alloc)
        step(c2, 300.0, 200.0, alloc)
        assert c2.resources.food_kcal > c1.resources.food_kcal

    def test_serialize_with_base(self):
        from colony import serialize
        colony = create_colony("Test")
        colony.base = ColonyBase()
        colony.base.modules.append(BuiltModule(module_type="solar_farm"))
        data = serialize(colony)
        assert data["base"] is not None
        assert len(data["base"]["modules"]) == 1
