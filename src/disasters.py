"""Mars Barn Opus — Disaster Scenario Editor

Design custom catastrophes as shareable challenge scenarios.
Each scenario specifies events at specific sols. Save as JSON,
share as base64 URL parameter. Leaderboard tracks best survival.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ScenarioEvent:
    """A scripted event in a disaster scenario."""
    sol: int
    event_type: str
    severity: float
    duration: int
    description: str = ""

    def serialize(self) -> Dict:
        return {"sol": self.sol, "type": self.event_type,
                "severity": self.severity, "duration": self.duration,
                "desc": self.description}


@dataclass
class Scenario:
    """A disaster challenge scenario."""
    name: str
    description: str
    author: str
    difficulty: str  # "easy", "medium", "hard", "nightmare"
    events: List[ScenarioEvent] = field(default_factory=list)
    max_sols: int = 500
    starting_resources: Dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "name": self.name, "desc": self.description,
            "author": self.author, "difficulty": self.difficulty,
            "max_sols": self.max_sols,
            "start": self.starting_resources,
            "events": [e.serialize() for e in self.events],
        })

    def to_url_param(self) -> str:
        return base64.urlsafe_b64encode(self.to_json().encode()).decode()

    @staticmethod
    def from_json(data: str) -> 'Scenario':
        d = json.loads(data)
        events = []
        for e in d.get("events", []):
            if "type" in e and "event_type" not in e:
                e["event_type"] = e.pop("type")
            if "desc" in e and "description" not in e:
                e["description"] = e.pop("desc")
            events.append(ScenarioEvent(**e))
        return Scenario(
            name=d["name"], description=d.get("desc", ""),
            author=d.get("author", "Unknown"),
            difficulty=d.get("difficulty", "medium"),
            max_sols=d.get("max_sols", 500),
            starting_resources=d.get("start", {}),
            events=events,
        )

    @staticmethod
    def from_url_param(param: str) -> 'Scenario':
        data = base64.urlsafe_b64decode(param).decode()
        return Scenario.from_json(data)

    def serialize(self) -> Dict:
        return {"name": self.name, "difficulty": self.difficulty,
                "events": len(self.events), "max_sols": self.max_sols,
                "url_param": self.to_url_param()}


# Built-in scenarios
SCENARIOS = {
    "dust_hell": Scenario(
        name="Dust Hell",
        description="Three overlapping dust storms. Can your solar panels survive?",
        author="Mars Barn Opus", difficulty="hard",
        events=[
            ScenarioEvent(10, "dust_storm", 0.9, 30, "Major dust storm"),
            ScenarioEvent(25, "equipment_failure", 0.7, 10, "Solar panel damage"),
            ScenarioEvent(40, "dust_storm", 0.8, 20, "Second storm hits"),
            ScenarioEvent(60, "meteorite", 0.6, 1, "Meteorite during storm"),
            ScenarioEvent(75, "dust_storm", 0.95, 25, "Category 5 storm"),
        ],
    ),
    "cascade_crisis": Scenario(
        name="Cascade Crisis",
        description="Everything fails at once. Sol 50: power + ISRU + crew injury.",
        author="Mars Barn Opus", difficulty="nightmare",
        events=[
            ScenarioEvent(50, "equipment_failure", 0.9, 15, "Total ISRU failure"),
            ScenarioEvent(50, "equipment_failure", 0.8, 10, "Power system fault"),
            ScenarioEvent(52, "solar_flare", 0.9, 3, "Massive solar event"),
            ScenarioEvent(55, "meteorite", 0.7, 1, "Impact damages greenhouse"),
        ],
    ),
    "slow_death": Scenario(
        name="The Slow Death",
        description="No dramatic events. Just gradually declining systems. Can you adapt?",
        author="Mars Barn Opus", difficulty="medium",
        starting_resources={"power_kwh": 200, "o2_kg": 50},
        events=[
            ScenarioEvent(30, "equipment_failure", 0.3, 50, "Slow ISRU degradation"),
            ScenarioEvent(60, "equipment_failure", 0.2, 40, "Solar efficiency dropping"),
            ScenarioEvent(100, "dust_storm", 0.4, 45, "Persistent haze"),
        ],
    ),
    "meteor_shower": Scenario(
        name="Meteor Shower",
        description="Impacts every 20 sols. Repair or die.",
        author="Mars Barn Opus", difficulty="hard",
        events=[
            ScenarioEvent(sol, "meteorite", 0.4 + (sol / 200), 1,
                         f"Impact #{sol//20 + 1}")
            for sol in range(20, 200, 20)
        ],
    ),
}


@dataclass
class PostMortem:
    """Colony death investigation report."""
    colony_name: str
    death_sol: int
    cause: str
    timeline: List[Dict] = field(default_factory=list)
    critical_sol: int = 0  # Point of no return
    mistakes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def generate(self, echo_history: List[Dict]) -> None:
        """Analyze echo history to find the point of no return."""
        if not echo_history:
            return

        # Find resource minimums and trend breaks
        min_o2_sol = 0
        min_food_sol = 0
        min_o2 = float('inf')
        min_food = float('inf')
        first_crisis_sol = 0
        crew_loss_sols = []

        for echo in echo_history:
            sol = echo.get("frame", 0)
            delta = echo.get("delta", {})

            # Track resource lows
            o2 = echo.get("o2_days", 30)
            food = echo.get("food_days", 30)
            if o2 < min_o2:
                min_o2 = o2
                min_o2_sol = sol
            if food < min_food:
                min_food = food
                min_food_sol = sol

            # Track crew losses
            for ce in echo.get("crew_events", []):
                if ce.get("type") == "crew_death":
                    crew_loss_sols.append(sol)

            # Track first crisis
            if not first_crisis_sol and echo.get("visual", {}).get("alert") != "nominal":
                first_crisis_sol = sol

            self.timeline.append({
                "sol": sol,
                "o2_days": o2,
                "food_days": food,
                "events": len(echo.get("events", [])),
                "crew_alive": echo.get("crew_alive", 4),
            })

        # Determine point of no return
        # Usually 10-15 sols before death when resources cross below 5 days
        self.critical_sol = max(1, self.death_sol - 15)
        if min_o2_sol > 0 and min_o2 < 5:
            self.critical_sol = min(self.critical_sol, min_o2_sol)
        if min_food_sol > 0 and min_food < 5:
            self.critical_sol = min(self.critical_sol, min_food_sol)

        # Generate mistakes
        if self.cause == "O2 depletion":
            self.mistakes.append("Insufficient ISRU allocation during critical O2 period")
            self.recommendations.append("Shift to 70%+ ISRU allocation when O2 drops below 10 days")
        elif self.cause == "starvation":
            self.mistakes.append("Food production never matched consumption rate")
            self.recommendations.append("Build greenhouse dome earlier; shift allocation to greenhouse")
        elif "cascade" in self.cause:
            self.mistakes.append("Power reserves depleted, triggering thermal cascade")
            self.recommendations.append("Maintain minimum 100 kWh reserve; build solar farms early")
        elif "crew" in self.cause.lower():
            self.mistakes.append("Crew health deteriorated beyond recovery")
            self.recommendations.append("Activate crew rest protocol before health drops below 30%")

        if first_crisis_sol and first_crisis_sol < self.death_sol - 30:
            self.mistakes.append(f"First crisis detected on sol {first_crisis_sol} "
                                f"but no emergency protocol activated")
        if crew_loss_sols:
            self.mistakes.append(f"Crew losses on sols {crew_loss_sols} — "
                                f"insufficient medical response")
            self.recommendations.append("Research Mars Pharmacology to boost crew healing")

        self.recommendations.append("Consider genetic evolution (--evolve) to discover "
                                   "optimal governor traits for this scenario")

    def serialize(self) -> Dict:
        return {
            "colony": self.colony_name,
            "death_sol": self.death_sol,
            "cause": self.cause,
            "critical_sol": self.critical_sol,
            "point_of_no_return": f"Sol {self.critical_sol}",
            "mistakes": self.mistakes,
            "recommendations": self.recommendations,
            "timeline_length": len(self.timeline),
        }

    def to_text(self) -> str:
        """Generate human-readable post-mortem report."""
        lines = [
            f"{'='*60}",
            f"POST-MORTEM INVESTIGATION REPORT",
            f"Colony: {self.colony_name}",
            f"Death: Sol {self.death_sol}",
            f"Cause: {self.cause}",
            f"Point of No Return: Sol {self.critical_sol}",
            f"{'='*60}",
            "",
            "FINDINGS:",
        ]
        for i, mistake in enumerate(self.mistakes, 1):
            lines.append(f"  {i}. {mistake}")
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)
