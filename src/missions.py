"""Mars Barn Opus — Mission Presets (Oregon Trail Style)

Choose your mission. Choose your crew. Choose your strategy.
Different starting conditions emphasize different survival approaches.

Like Oregon Trail: do you bring more food or more spare parts?
Do you push hard or take it slow? Every choice has consequences.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MissionPreset:
    """A selectable mission configuration."""
    name: str
    slug: str
    description: str
    difficulty: str  # "easy", "medium", "hard", "extreme"
    crew_type: str   # "human", "robot", "mixed"
    crew_size: int
    starting_resources: Dict[str, float]
    governor_archetype: str
    special_rules: List[str]
    flavor_text: str

    def serialize(self) -> Dict:
        return {
            "name": self.name, "slug": self.slug,
            "description": self.description,
            "difficulty": self.difficulty,
            "crew_type": self.crew_type,
            "crew_size": self.crew_size,
            "governor": self.governor_archetype,
            "special_rules": self.special_rules,
        }


MISSIONS: Dict[str, MissionPreset] = {
    # ── Robot Missions (Phase 1 — no humans) ──
    "optimus_pathfinder": MissionPreset(
        name="Optimus Pathfinder",
        slug="optimus_pathfinder",
        description="4 Tesla Optimus bots establish the first base. No humans. Pure autonomy.",
        difficulty="medium",
        crew_type="robot",
        crew_size=4,
        starting_resources={
            "o2_kg": 0, "h2o_liters": 200, "food_kcal": 0,
            "power_kwh": 800,
        },
        governor_archetype="engineer",
        special_rules=[
            "No O2 or food consumption (robots)",
            "High power consumption (charging)",
            "Dust damages robot joints",
            "No supply drops (full autonomy)",
        ],
        flavor_text="The first boots on Mars aren't boots at all. "
                    "They're actuators. 4 Optimus units, 800 kWh of "
                    "battery, and the entire future of the colony riding "
                    "on whether they can build a habitat before the dust "
                    "eats their joints.",
    ),
    "lunar_testbed": MissionPreset(
        name="Lunar Testbed",
        slug="lunar_testbed",
        description="2 bots on the Moon. Shorter mission, harsher conditions. Proof of concept.",
        difficulty="hard",
        crew_type="robot",
        crew_size=2,
        starting_resources={
            "o2_kg": 0, "h2o_liters": 50, "food_kcal": 0,
            "power_kwh": 400,
        },
        governor_archetype="survivalist",
        special_rules=[
            "14-day lunar night (no solar for 14 sols)",
            "Extreme temperature swings (-173°C to 127°C)",
            "No atmosphere (no ISRU from air)",
            "Water from permanently shadowed craters only",
        ],
        flavor_text="Before Mars, prove it on the Moon. Two Optimus "
                    "units, minimal supplies, and a 14-day night that "
                    "will freeze the battery solid if you don't plan ahead.",
    ),

    # ── Human Missions (Phase 2+) ──
    "ares_first_landing": MissionPreset(
        name="Ares I: First Landing",
        slug="ares_first_landing",
        description="4 humans, 30 sols of reserves. The classic Mars mission. Survive 500 sols.",
        difficulty="medium",
        crew_type="human",
        crew_size=4,
        starting_resources={
            "o2_kg": 100.8, "h2o_liters": 300, "food_kcal": 300000,
            "power_kwh": 500,
        },
        governor_archetype="engineer",
        special_rules=["Standard Mars conditions", "Supply drops every 760 sols"],
        flavor_text="This is the one everyone's been training for. "
                    "4 crew, 30 sols of reserves, and 225 million km "
                    "between you and the nearest hospital. The governor AI "
                    "makes every decision. You just watch.",
    ),
    "skeleton_crew": MissionPreset(
        name="Skeleton Crew",
        slug="skeleton_crew",
        description="2 humans, minimal supplies. Every gram counts.",
        difficulty="hard",
        crew_type="human",
        crew_size=2,
        starting_resources={
            "o2_kg": 25, "h2o_liters": 75, "food_kcal": 75000,
            "power_kwh": 300,
        },
        governor_archetype="survivalist",
        special_rules=[
            "Half crew = half consumption but half production",
            "No redundancy — one injury is a crisis",
            "No supply drops",
        ],
        flavor_text="Budget cuts. Two astronauts instead of four. "
                    "Half the supplies. Same planet. The governor needs "
                    "to be twice as smart.",
    ),
    "abundant_start": MissionPreset(
        name="Garden of Mars",
        slug="abundant_start",
        description="6 crew with double reserves. Easy mode — but can you sustain it?",
        difficulty="easy",
        crew_type="human",
        crew_size=6,
        starting_resources={
            "o2_kg": 300, "h2o_liters": 900, "food_kcal": 900000,
            "power_kwh": 1000,
        },
        governor_archetype="diplomat",
        special_rules=[
            "Double starting reserves",
            "6 crew (more production, more consumption)",
            "Supply drops every 400 sols",
        ],
        flavor_text="NASA went all in. Six crew, double supplies, "
                    "and a governor who believes in cooperation. "
                    "The question isn't whether you'll survive. "
                    "It's whether you'll thrive.",
    ),

    # ── Challenge Missions ──
    "dust_bowl": MissionPreset(
        name="Dust Bowl",
        slug="dust_bowl",
        description="Land during peak dust season. Solar panels are a luxury.",
        difficulty="extreme",
        crew_type="human",
        crew_size=4,
        starting_resources={
            "o2_kg": 80, "h2o_liters": 200, "food_kcal": 200000,
            "power_kwh": 300,
        },
        governor_archetype="commander",
        special_rules=[
            "Permanent dust haze (solar at 40% efficiency)",
            "Major dust storm every 50 sols",
            "Equipment failure rate doubled",
        ],
        flavor_text="They said don't land during dust season. "
                    "We landed during dust season. The sky is orange, "
                    "the panels are coated, and the commander is already "
                    "making hard choices.",
    ),
    "no_isru": MissionPreset(
        name="ISRU Down",
        slug="no_isru",
        description="ISRU failed on landing. No local O2/H2O production. Live on reserves.",
        difficulty="extreme",
        crew_type="human",
        crew_size=4,
        starting_resources={
            "o2_kg": 200, "h2o_liters": 500, "food_kcal": 400000,
            "power_kwh": 500,
        },
        governor_archetype="scientist",
        special_rules=[
            "ISRU efficiency permanently at 0%",
            "Must survive on reserves + greenhouse only",
            "Can research ISRU repair (60 sols)",
        ],
        flavor_text="The ISRU unit cracked during landing. No O2 "
                    "production. No water extraction. You have what "
                    "you brought and what the greenhouse can grow. "
                    "The scientist says she can fix it. In 60 sols.",
    ),

    # ── Mixed Crew ──
    "hybrid_colony": MissionPreset(
        name="Hybrid Colony",
        slug="hybrid_colony",
        description="2 humans + 4 robots. The future of Mars colonization.",
        difficulty="medium",
        crew_type="mixed",
        crew_size=6,
        starting_resources={
            "o2_kg": 50, "h2o_liters": 200, "food_kcal": 150000,
            "power_kwh": 800,
        },
        governor_archetype="scientist",
        special_rules=[
            "Robots handle construction and EVA",
            "Humans handle research and greenhouse",
            "Robots need power, humans need O2/food/water",
            "If humans die, robots continue autonomously",
        ],
        flavor_text="The real future isn't all-human or all-robot. "
                    "It's both. Two scientists direct four Optimus units. "
                    "The humans think. The robots build. Together, "
                    "they might just make it.",
    ),
}


def list_missions() -> None:
    """Print available missions."""
    print(f"\n{'='*65}")
    print(f"  MARS BARN OPUS — Mission Selection")
    print(f"{'='*65}\n")

    for slug, m in MISSIONS.items():
        diff_color = {"easy": "🟢", "medium": "🟡", "hard": "🔴", "extreme": "⚫"}
        diff = diff_color.get(m.difficulty, "⚪")
        print(f"  {diff} {m.name}")
        print(f"     {m.description}")
        print(f"     Crew: {m.crew_size} ({m.crew_type}) | "
              f"Governor: {m.governor_archetype} | "
              f"Difficulty: {m.difficulty}")
        print(f"     \"{m.flavor_text[:80]}...\"")
        print()

    print(f"  Usage: python src/sim.py --mission optimus_pathfinder")
    print(f"{'='*65}\n")
