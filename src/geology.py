"""Mars Barn Opus — Geological Survey System

Rovers autonomously explore terrain, discover mineral deposits,
ice veins, cave entrances, and ancient riverbeds. Each discovery
unlocks new building options or resource bonuses.

The terrain isn't decoration — it's gameplay.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Discovery:
    """A geological discovery made by a rover."""
    discovery_type: str
    name: str
    description: str
    sol_discovered: int
    location: tuple  # (x, y) grid coords
    bonus: Dict[str, float]  # Resource/system bonuses
    explored: bool = False  # Fully surveyed?

    def serialize(self) -> Dict:
        return {"type": self.discovery_type, "name": self.name,
                "sol": self.sol_discovered, "location": list(self.location),
                "bonus": self.bonus, "explored": self.explored}


DISCOVERY_TYPES = {
    "ice_deposit": {
        "names": ["Frost Vein Alpha", "Subsurface Ice Field", "Permafrost Lens",
                  "Polar Ice Outcrop", "Glacial Remnant"],
        "desc": "Subsurface water ice. Passive H2O production bonus.",
        "bonus": {"passive_h2o": 2.0},
        "probability": 0.03,
    },
    "mineral_deposit": {
        "names": ["Iron Oxide Seam", "Hematite Ridge", "Olivine Outcrop",
                  "Magnetite Cluster", "Basalt Formation"],
        "desc": "Mineral-rich regolith. Reduces construction costs.",
        "bonus": {"construction_cost_reduction": 0.15},
        "probability": 0.025,
    },
    "cave_entrance": {
        "names": ["Lava Tube Alpha", "Subsurface Cavern", "Collapsed Skylight",
                  "Shelter Cave", "Tharsis Tube"],
        "desc": "Natural shelter. Massive radiation protection bonus.",
        "bonus": {"radiation_shielding": 0.50},
        "probability": 0.008,
    },
    "ancient_riverbed": {
        "names": ["Dry Channel Delta", "Paleolake Sediment", "Fluvial Deposit",
                  "Ancient Streambed", "Noachian Clay"],
        "desc": "Clay-rich soil. Excellent for greenhouse cultivation.",
        "bonus": {"food_production_bonus": 0.20},
        "probability": 0.02,
    },
    "geothermal_vent": {
        "names": ["Thermal Anomaly", "Fumarole Site", "Hot Spring Remnant",
                  "Volcanic Vent", "Magmatic Intrusion"],
        "desc": "Geothermal energy source. Passive power generation.",
        "bonus": {"passive_power": 5.0},
        "probability": 0.005,
    },
}


@dataclass
class GeologySurvey:
    """Manages geological exploration."""
    discoveries: List[Discovery] = field(default_factory=list)
    survey_progress: float = 0.0  # 0-1, how much terrain surveyed
    rovers_deployed: int = 0

    def tick(self, sol: int, rover_count: int = 1,
             rng: Optional[random.Random] = None) -> List[str]:
        """Advance survey by one sol. Returns event strings."""
        if rng is None:
            rng = random.Random(sol)
        events = []
        self.rovers_deployed = rover_count
        self.survey_progress = min(1.0, self.survey_progress + 0.002 * rover_count)

        for dtype, config in DISCOVERY_TYPES.items():
            if rng.random() < config["probability"] * rover_count:
                already = sum(1 for d in self.discoveries if d.discovery_type == dtype)
                if already >= 3:
                    continue
                name = rng.choice(config["names"])
                loc = (rng.randint(0, 31), rng.randint(0, 31))
                discovery = Discovery(
                    discovery_type=dtype, name=name,
                    description=config["desc"],
                    sol_discovered=sol, location=loc,
                    bonus=dict(config["bonus"]),
                )
                self.discoveries.append(discovery)
                events.append(f"DISCOVERY: {name} — {config['desc']}")

        return events

    def get_bonus(self, bonus_key: str) -> float:
        """Total bonus from all discoveries."""
        return sum(d.bonus.get(bonus_key, 0) for d in self.discoveries)

    def serialize(self) -> Dict:
        return {
            "discoveries": [d.serialize() for d in self.discoveries],
            "survey_progress": round(self.survey_progress, 3),
            "rovers_deployed": self.rovers_deployed,
            "total_discoveries": len(self.discoveries),
        }
