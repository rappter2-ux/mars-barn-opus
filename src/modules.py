"""Mars Barn Opus — Colony Modules (Base Expansion)

Start with a bare landing habitat. Build new modules over time.
Each module has construction cost, build time, and production bonuses.
The governor decides when to build. The operator can override.

Module types:
  - habitat: starting module, crew quarters (always present)
  - greenhouse_dome: food production bonus
  - isru_plant: O2/H2O production bonus
  - repair_bay: system repair speed bonus
  - radiation_shelter: crew radiation protection
  - solar_farm: additional solar panel capacity
  - water_extractor: ice mining for water bonus
  - comms_array: reduces communication delay
  - storage_depot: increases resource storage capacity
  - research_lab: enables tech upgrades (future)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ModuleType:
    """Blueprint for a colony module."""
    name: str
    slug: str
    description: str
    build_sols: int              # How many sols to construct
    cost_power_kwh: float        # Power consumed during construction
    cost_materials: Dict[str, float]  # Resources consumed to build
    effects: Dict[str, float]    # Bonuses when operational
    max_count: int = 1           # How many can be built


# Module catalog
MODULES: Dict[str, ModuleType] = {
    "greenhouse_dome": ModuleType(
        name="Greenhouse Dome",
        slug="greenhouse_dome",
        description="Pressurized growing area. Boosts food production by 50%.",
        build_sols=15,
        cost_power_kwh=200,
        cost_materials={"h2o_liters": 50, "food_kcal": 20000},
        effects={"greenhouse_bonus": 0.50},
    ),
    "isru_plant": ModuleType(
        name="ISRU Plant",
        slug="isru_plant",
        description="In-situ resource utilization. Boosts O2/H2O production by 40%.",
        build_sols=20,
        cost_power_kwh=300,
        cost_materials={"h2o_liters": 30},
        effects={"isru_bonus": 0.40},
    ),
    "repair_bay": ModuleType(
        name="Repair Bay",
        slug="repair_bay",
        description="System maintenance facility. Doubles repair speed.",
        build_sols=10,
        cost_power_kwh=150,
        cost_materials={"food_kcal": 15000},
        effects={"repair_bonus": 1.0},
    ),
    "radiation_shelter": ModuleType(
        name="Radiation Shelter",
        slug="radiation_shelter",
        description="Shielded bunker. Reduces crew radiation dose by 60%.",
        build_sols=12,
        cost_power_kwh=250,
        cost_materials={"h2o_liters": 80},
        effects={"radiation_shielding": 0.60},
    ),
    "solar_farm": ModuleType(
        name="Solar Farm",
        slug="solar_farm",
        description="Additional solar panels. Increases power generation by 40%.",
        build_sols=8,
        cost_power_kwh=100,
        cost_materials={},
        effects={"solar_bonus": 0.40},
        max_count=3,
    ),
    "water_extractor": ModuleType(
        name="Water Extractor",
        slug="water_extractor",
        description="Regolith ice mining. Passive H2O production each sol.",
        build_sols=14,
        cost_power_kwh=200,
        cost_materials={"food_kcal": 10000},
        effects={"passive_h2o": 3.0},  # 3 liters/sol passive
    ),
    "comms_array": ModuleType(
        name="Comms Array",
        slug="comms_array",
        description="High-gain antenna. Reduces comms delay by 30%.",
        build_sols=6,
        cost_power_kwh=80,
        cost_materials={},
        effects={"comms_delay_reduction": 0.30},
    ),
    "storage_depot": ModuleType(
        name="Storage Depot",
        slug="storage_depot",
        description="Expanded storage. Increases reserve capacity by 50%.",
        build_sols=10,
        cost_power_kwh=120,
        cost_materials={"h2o_liters": 20},
        effects={"storage_bonus": 0.50},
    ),
}


@dataclass
class BuiltModule:
    """A constructed module in the colony."""
    module_type: str          # Key in MODULES
    operational: bool = True
    built_sol: int = 0
    health: float = 1.0       # 0-1, degrades from events

    @property
    def blueprint(self) -> ModuleType:
        """Get the module blueprint."""
        return MODULES[self.module_type]

    def serialize(self) -> Dict:
        """Serialize for twin state."""
        bp = self.blueprint
        return {
            "type": self.module_type,
            "name": bp.name,
            "operational": self.operational,
            "built_sol": self.built_sol,
            "health": round(self.health, 2),
            "effects": bp.effects,
        }


@dataclass
class ConstructionProject:
    """A module currently under construction."""
    module_type: str
    sols_remaining: int
    total_sols: int
    power_committed: float = 0

    @property
    def progress(self) -> float:
        """Construction progress 0-1."""
        if self.total_sols <= 0:
            return 1.0
        return 1.0 - (self.sols_remaining / self.total_sols)

    def serialize(self) -> Dict:
        """Serialize for twin state."""
        bp = MODULES[self.module_type]
        return {
            "type": self.module_type,
            "name": bp.name,
            "progress": round(self.progress, 2),
            "sols_remaining": self.sols_remaining,
        }


@dataclass
class ColonyBase:
    """The physical colony base with modules."""
    modules: List[BuiltModule] = field(default_factory=list)
    construction: Optional[ConstructionProject] = None
    build_log: List[Dict] = field(default_factory=list)

    def has_module(self, slug: str) -> bool:
        """Check if a module type is built and operational."""
        return any(m.module_type == slug and m.operational for m in self.modules)

    def count_module(self, slug: str) -> int:
        """Count operational modules of a type."""
        return sum(1 for m in self.modules
                   if m.module_type == slug and m.operational)

    def get_bonus(self, effect_key: str) -> float:
        """Get total bonus for an effect across all operational modules."""
        total = 0.0
        for m in self.modules:
            if m.operational and m.health > 0.3:
                bp = m.blueprint
                total += bp.effects.get(effect_key, 0.0) * m.health
        return total

    def can_build(self, slug: str, resources: 'Resources') -> tuple:
        """Check if a module can be built. Returns (can_build, reason)."""
        if slug not in MODULES:
            return False, f"Unknown module: {slug}"
        bp = MODULES[slug]
        if self.construction is not None:
            return False, "Already building something"
        if self.count_module(slug) >= bp.max_count:
            return False, f"Max {bp.max_count} {bp.name} allowed"
        # Check resources
        if resources.power_kwh < bp.cost_power_kwh:
            return False, f"Need {bp.cost_power_kwh} kWh (have {resources.power_kwh:.0f})"
        for res_key, amount in bp.cost_materials.items():
            current = getattr(resources, res_key, 0)
            if current < amount:
                return False, f"Need {amount} {res_key} (have {current:.0f})"
        return True, "Ready to build"

    def start_construction(self, slug: str, resources: 'Resources',
                          current_sol: int) -> Optional[str]:
        """Start building a module. Deducts resources. Returns error or None."""
        can, reason = self.can_build(slug, resources)
        if not can:
            return reason
        bp = MODULES[slug]
        # Deduct costs
        resources.power_kwh -= bp.cost_power_kwh
        for res_key, amount in bp.cost_materials.items():
            current = getattr(resources, res_key, 0)
            setattr(resources, res_key, current - amount)
        self.construction = ConstructionProject(
            module_type=slug,
            sols_remaining=bp.build_sols,
            total_sols=bp.build_sols,
        )
        return None

    def tick(self, current_sol: int) -> List[str]:
        """Advance construction by one sol. Returns event strings."""
        events = []
        if self.construction:
            self.construction.sols_remaining -= 1
            if self.construction.sols_remaining <= 0:
                # Construction complete
                module = BuiltModule(
                    module_type=self.construction.module_type,
                    built_sol=current_sol,
                )
                self.modules.append(module)
                bp = module.blueprint
                events.append(f"CONSTRUCTION COMPLETE: {bp.name}")
                self.build_log.append({
                    "sol": current_sol,
                    "module": self.construction.module_type,
                    "name": bp.name,
                })
                self.construction = None
        return events

    def serialize(self) -> Dict:
        """Serialize for twin state."""
        return {
            "modules": [m.serialize() for m in self.modules],
            "construction": self.construction.serialize() if self.construction else None,
            "bonuses": {
                "greenhouse_bonus": round(self.get_bonus("greenhouse_bonus"), 2),
                "isru_bonus": round(self.get_bonus("isru_bonus"), 2),
                "solar_bonus": round(self.get_bonus("solar_bonus"), 2),
                "repair_bonus": round(self.get_bonus("repair_bonus"), 2),
                "radiation_shielding": round(self.get_bonus("radiation_shielding"), 2),
                "passive_h2o": round(self.get_bonus("passive_h2o"), 2),
                "comms_delay_reduction": round(self.get_bonus("comms_delay_reduction"), 2),
                "storage_bonus": round(self.get_bonus("storage_bonus"), 2),
            },
        }


def governor_build_decision(base: ColonyBase, resources: 'Resources',
                            sol: int, crisis_level: float) -> Optional[str]:
    """AI governor decides what to build next.

    Priority order based on colony needs:
    1. If food is critical → greenhouse_dome
    2. If O2/H2O critical → isru_plant
    3. If power is low → solar_farm
    4. If radiation is high → radiation_shelter
    5. If systems damaged → repair_bay
    6. Otherwise → water_extractor (passive income)

    Won't build during crisis (crisis_level > 0.6).
    """
    if crisis_level > 0.6:
        return None  # Don't build during crisis
    if base.construction is not None:
        return None  # Already building

    # Check what we need most
    o2_days = resources.days_of("o2") if hasattr(resources, 'days_of') else 30
    h2o_days = resources.days_of("h2o") if hasattr(resources, 'days_of') else 30
    food_days = resources.days_of("food") if hasattr(resources, 'days_of') else 30
    power_days = resources.days_of("power") if hasattr(resources, 'days_of') else 30

    priorities = []
    if food_days < 25 and not base.has_module("greenhouse_dome"):
        priorities.append(("greenhouse_dome", 100 - food_days))
    if (o2_days < 25 or h2o_days < 25) and not base.has_module("isru_plant"):
        priorities.append(("isru_plant", 100 - min(o2_days, h2o_days)))
    if power_days < 20 and base.count_module("solar_farm") < 3:
        priorities.append(("solar_farm", 80 - power_days))
    if not base.has_module("radiation_shelter") and sol > 30:
        priorities.append(("radiation_shelter", 40))
    if not base.has_module("repair_bay") and sol > 50:
        priorities.append(("repair_bay", 30))
    if not base.has_module("water_extractor") and sol > 20:
        priorities.append(("water_extractor", 35))
    if not base.has_module("comms_array") and sol > 40:
        priorities.append(("comms_array", 20))
    if not base.has_module("storage_depot") and sol > 60:
        priorities.append(("storage_depot", 15))

    # Sort by priority score
    priorities.sort(key=lambda x: -x[1])

    for slug, _ in priorities:
        can, _ = base.can_build(slug, resources)
        if can:
            return slug
    return None
