"""Mars Barn Opus — Autonomous Robot Crew (Tesla Optimus)

Phase 1 uses autonomous robots instead of humans. Tesla Optimus bots
handle all colony operations: construction, maintenance, ISRU, farming,
repairs, and exploration.

The digital twin models virtual Optimus bots. The physical twin IS
real Optimus bots. Same state model. Same LisPy control programs.
Same autonomy scoreboard. 1:1 mirror.

Robot specs based on Tesla Optimus Gen 2:
- Height: 1.73m, Weight: 56kg
- Actuators: 28 structural degrees of freedom
- Hands: 11 DoF each, tactile fingertip sensors
- Power: 2.3kWh battery, ~5h active operation per charge
- Sensors: cameras, IMU, force/torque sensors
- Compute: Tesla FSD computer (onboard AI)
- Communication: WiFi/mesh to colony controller

Advantages over human crew:
- No O2 consumption (still need power to charge)
- No food consumption
- No psychological needs (no morale to manage)
- Can work in vacuum (EVA without suits)
- Can be repaired (not healed — repaired)
- Can be powered down and stored indefinitely
- Radiation-tolerant (electronics, not biology)

Tradeoffs:
- Need charging infrastructure (power-hungry)
- Less adaptable than humans (narrower skill set per unit)
- Repair requires spare parts (can't self-heal)
- No creativity/innovation (follows programs)
- Dust ingress damages joints
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class RobotRole(Enum):
    BUILDER = "builder"          # Construction, module assembly
    MECHANIC = "mechanic"        # System repair, maintenance
    FARMER = "farmer"            # Greenhouse, ISRU operation
    EXPLORER = "explorer"        # Geological survey, sample collection
    MEDIC = "medic_bot"          # Maintenance of other robots
    GENERAL = "general"          # Multi-purpose, lower efficiency


# Role → system bonuses (same pattern as human crew)
ROBOT_ROLE_BONUSES = {
    RobotRole.BUILDER: {"construction_speed": 0.25, "repair": 0.10},
    RobotRole.MECHANIC: {"repair": 0.30, "solar": 0.10, "isru": 0.10},
    RobotRole.FARMER: {"greenhouse": 0.25, "isru": 0.15},
    RobotRole.EXPLORER: {"terrain_bonus": 0.20, "water_finding": 0.25},
    RobotRole.MEDIC: {"robot_repair": 0.30},
    RobotRole.GENERAL: {"repair": 0.05, "greenhouse": 0.05, "isru": 0.05},
}

# Optimus bot names (unit designators)
OPTIMUS_NAMES = [
    "OPT-01 Atlas", "OPT-02 Nova", "OPT-03 Titan", "OPT-04 Vega",
    "OPT-05 Orion", "OPT-06 Luna", "OPT-07 Mars", "OPT-08 Sol",
    "OPT-09 Astra", "OPT-10 Nexus", "OPT-11 Apex", "OPT-12 Zero",
]


@dataclass
class RobotUnit:
    """A single Tesla Optimus robot unit."""
    name: str
    role: RobotRole
    # Status
    operational: bool = True
    health: float = 100.0          # 0 = non-functional, 100 = factory fresh
    battery_pct: float = 100.0     # 0 = dead, 100 = full charge
    charge_rate_per_sol: float = 80.0  # % per sol when charging
    # Performance
    efficiency: float = 1.0        # 0-1, degrades with damage/dust
    dust_accumulation: float = 0.0 # 0-100, requires cleaning
    sols_active: int = 0
    tasks_completed: int = 0
    # Failure tracking
    cause_of_failure: Optional[str] = None
    last_maintained_sol: int = 0

    @property
    def effective_output(self) -> float:
        """How much useful work this robot produces (0-1).

        Combines health, battery, efficiency, and dust.
        """
        if not self.operational:
            return 0.0
        health_factor = self.health / 100.0
        battery_factor = min(1.0, self.battery_pct / 30.0)  # Below 30% = reduced
        dust_factor = max(0.3, 1.0 - self.dust_accumulation / 150.0)
        return health_factor * battery_factor * self.efficiency * dust_factor

    @property
    def needs_charging(self) -> bool:
        """Whether this robot needs to charge."""
        return self.battery_pct < 20.0

    @property
    def needs_maintenance(self) -> bool:
        """Whether this robot needs cleaning/repair."""
        return self.dust_accumulation > 60 or self.health < 70

    @property
    def status_line(self) -> str:
        """One-line status."""
        if not self.operational:
            return f"OFFLINE ({self.cause_of_failure})"
        if self.needs_charging:
            return "CHARGING"
        if self.needs_maintenance:
            return "NEEDS MAINTENANCE"
        if self.effective_output > 0.8:
            return "NOMINAL"
        return "DEGRADED"

    def serialize(self) -> Dict:
        """Serialize for twin state — 1:1 with physical bot."""
        return {
            "name": self.name,
            "role": self.role.value,
            "operational": self.operational,
            "health": round(self.health, 1),
            "battery_pct": round(self.battery_pct, 1),
            "efficiency": round(self.efficiency, 2),
            "dust_accumulation": round(self.dust_accumulation, 1),
            "effective_output": round(self.effective_output, 2),
            "status": self.status_line,
            "sols_active": self.sols_active,
            "tasks_completed": self.tasks_completed,
            "needs_charging": self.needs_charging,
            "needs_maintenance": self.needs_maintenance,
        }


@dataclass
class RobotCrew:
    """Fleet of Tesla Optimus robots."""
    units: List[RobotUnit] = field(default_factory=list)
    total_power_consumed_kwh: float = 0.0

    @property
    def operational_count(self) -> int:
        return sum(1 for u in self.units if u.operational)

    @property
    def avg_health(self) -> float:
        ops = [u for u in self.units if u.operational]
        return sum(u.health for u in ops) / max(1, len(ops))

    @property
    def avg_efficiency(self) -> float:
        ops = [u for u in self.units if u.operational]
        return sum(u.effective_output for u in ops) / max(1, len(ops))

    def get_role_bonus(self, system: str) -> float:
        """Total bonus for a colony system from operational robots."""
        bonus = 0.0
        for unit in self.units:
            if unit.operational:
                role_data = ROBOT_ROLE_BONUSES.get(unit.role, {})
                bonus += role_data.get(system, 0.0) * unit.effective_output
        return bonus

    def tick(self, sol: int, available_power_kwh: float,
             dust_storm: bool = False) -> tuple:
        """Advance all robots by one sol.

        Returns (power_consumed, events list).
        """
        events = []
        power_consumed = 0.0

        for unit in self.units:
            if not unit.operational:
                continue

            unit.sols_active += 1

            # Battery drain: ~20% per sol of active work
            unit.battery_pct -= 20.0

            # Charging: uses colony power
            if unit.battery_pct < 50:
                charge_kwh = 2.3 * (100 - unit.battery_pct) / 100  # 2.3kWh battery
                if available_power_kwh - power_consumed > charge_kwh:
                    unit.battery_pct = min(100, unit.battery_pct + unit.charge_rate_per_sol)
                    power_consumed += charge_kwh
                else:
                    events.append(f"{unit.name}: insufficient power to charge")

            # Dust accumulation (faster in dust storms)
            dust_rate = 3.0 if dust_storm else 0.5
            unit.dust_accumulation += dust_rate

            # Dust damages joints over time
            if unit.dust_accumulation > 80:
                unit.health -= 0.5
                unit.efficiency = max(0.5, unit.efficiency - 0.005)

            # Battery death
            if unit.battery_pct <= 0:
                unit.battery_pct = 0
                events.append(f"{unit.name}: battery depleted — entering standby")

            # Health degradation → failure
            if unit.health <= 0:
                unit.operational = False
                unit.cause_of_failure = "mechanical failure (dust/wear)"
                events.append(f"ROBOT LOST: {unit.name} — {unit.cause_of_failure}")

            # Maintenance by medic bot
            medics = [u for u in self.units
                      if u.operational and u.role == RobotRole.MEDIC and u is not unit]
            if medics and unit.needs_maintenance:
                best_medic = max(medics, key=lambda m: m.effective_output)
                repair = 2.0 * best_medic.effective_output
                unit.health = min(100, unit.health + repair)
                unit.dust_accumulation = max(0, unit.dust_accumulation - 5)
                unit.tasks_completed += 1

        self.total_power_consumed_kwh += power_consumed
        return power_consumed, events

    def serialize(self) -> List[Dict]:
        """Serialize all units for twin state."""
        return [u.serialize() for u in self.units]


def generate_robot_crew(size: int = 4, seed: int = 42) -> RobotCrew:
    """Generate a robot crew with balanced roles."""
    import random
    rng = random.Random(seed)

    role_assignments = {
        2: [RobotRole.MECHANIC, RobotRole.FARMER],
        3: [RobotRole.MECHANIC, RobotRole.FARMER, RobotRole.BUILDER],
        4: [RobotRole.MECHANIC, RobotRole.FARMER, RobotRole.BUILDER, RobotRole.EXPLORER],
        6: [RobotRole.MECHANIC, RobotRole.FARMER, RobotRole.BUILDER,
            RobotRole.EXPLORER, RobotRole.MEDIC, RobotRole.GENERAL],
    }
    roles = role_assignments.get(size,
        [RobotRole.GENERAL] * size)

    names = list(OPTIMUS_NAMES)
    rng.shuffle(names)

    units = []
    for i in range(size):
        units.append(RobotUnit(
            name=names[i % len(names)],
            role=roles[i % len(roles)],
            health=95 + rng.uniform(0, 5),
            battery_pct=100.0,
            efficiency=0.95 + rng.uniform(0, 0.05),
        ))

    return RobotCrew(units=units)
