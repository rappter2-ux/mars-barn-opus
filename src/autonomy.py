"""Mars Barn Opus — Autonomy Enforcement

Phase 1 of the colony simulation: ZERO HUMAN CONTACT.
The colony must survive entirely on its own. If a human intervenes
(operator override, manual command, supply drop from Earth), the
simulation automatically fails.

This is the proving ground. If the AI governor can't keep 4 humans
alive on Mars without help from Earth, it has no business being
deployed. The autonomy constraint is what makes the sim meaningful.

Phases:
  Phase 1: FULL AUTONOMY — zero human contact, no supply drops,
           no operator overrides. Colony lives or dies on AI decisions.
           Duration: configurable (default 500 sols).
           Failure conditions: colony death OR human intervention.

  Phase 2: SUPERVISED — operator can observe and send commands
           (with light delay). Supply drops available. This is the
           "training wheels" phase.

  Phase 3: COLLABORATIVE — full operator control available.
           The sim becomes the digital twin interface for real ops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class Phase(Enum):
    FULL_AUTONOMY = "full_autonomy"
    SUPERVISED = "supervised"
    COLLABORATIVE = "collaborative"


@dataclass
class AutonomyEnforcer:
    """Enforces the autonomy constraint.

    Tracks every attempted human intervention. If any intervention
    occurs during Phase 1, the sim fails immediately.
    """
    phase: Phase = Phase.FULL_AUTONOMY
    interventions: List[Dict] = field(default_factory=list)
    failed: bool = False
    failure_reason: Optional[str] = None
    failure_sol: Optional[int] = None

    # Counters
    overrides_blocked: int = 0
    supply_drops_blocked: int = 0
    commands_blocked: int = 0

    def check_intervention(self, intervention_type: str, sol: int,
                           details: str = "") -> bool:
        """Check if an intervention is allowed. Returns True if allowed.

        In Phase 1: ALL interventions are blocked and the sim FAILS.
        In Phase 2+: interventions are allowed (logged).
        """
        self.interventions.append({
            "sol": sol, "type": intervention_type,
            "details": details, "phase": self.phase.value,
        })

        if self.phase == Phase.FULL_AUTONOMY:
            # FAIL — human contact detected
            self.failed = True
            self.failure_reason = f"Human intervention: {intervention_type}"
            self.failure_sol = sol

            if intervention_type == "operator_override":
                self.overrides_blocked += 1
            elif intervention_type == "supply_drop":
                self.supply_drops_blocked += 1
            elif intervention_type == "manual_command":
                self.commands_blocked += 1

            return False  # Intervention blocked

        # Phase 2+: allowed
        return True

    def can_receive_supply(self, sol: int) -> bool:
        """Check if supply drops are allowed."""
        if self.phase == Phase.FULL_AUTONOMY:
            self.check_intervention("supply_drop", sol,
                                    "Supply drop attempted during full autonomy")
            return False
        return True

    def can_override(self, sol: int) -> bool:
        """Check if operator overrides are allowed."""
        if self.phase == Phase.FULL_AUTONOMY:
            self.check_intervention("operator_override", sol,
                                    "Operator override attempted during full autonomy")
            return False
        return True

    def can_send_command(self, sol: int) -> bool:
        """Check if Earth commands are allowed."""
        if self.phase == Phase.FULL_AUTONOMY:
            self.check_intervention("manual_command", sol,
                                    "Earth command attempted during full autonomy")
            return False
        return True

    def get_status(self) -> Dict:
        """Current autonomy status."""
        return {
            "phase": self.phase.value,
            "failed": self.failed,
            "failure_reason": self.failure_reason,
            "failure_sol": self.failure_sol,
            "interventions_attempted": len(self.interventions),
            "overrides_blocked": self.overrides_blocked,
            "supply_drops_blocked": self.supply_drops_blocked,
            "commands_blocked": self.commands_blocked,
        }

    def serialize(self) -> Dict:
        """Serialize for twin state."""
        return {
            "phase": self.phase.value,
            "phase_name": {
                Phase.FULL_AUTONOMY: "FULL AUTONOMY — Zero Human Contact",
                Phase.SUPERVISED: "SUPERVISED — Operator Can Observe",
                Phase.COLLABORATIVE: "COLLABORATIVE — Full Control",
            }[self.phase],
            "failed": self.failed,
            "failure_reason": self.failure_reason,
            "autonomy_sols": 0,  # Set by caller
            "interventions": len(self.interventions),
        }


@dataclass
class AutonomyScoreboard:
    """The scoreboard. How long can they survive without needing a human?

    This is THE metric. Not colony survival time. Not resources.
    Not morale. How many sols of ZERO human contact before the
    colony needs help (or dies).

    A score of 500+ means the AI governor is Mars-ready.
    """
    entries: List[Dict] = field(default_factory=list)

    def record_run(self, governor_name: str, archetype: str,
                   autonomy_sols: int, colony_alive: bool,
                   cause_of_death: Optional[str] = None,
                   crew_survived: int = 0, modules_built: int = 0,
                   research_completed: int = 0,
                   seed: int = 42) -> None:
        """Record a completed autonomy run."""
        self.entries.append({
            "governor": governor_name,
            "archetype": archetype,
            "autonomy_sols": autonomy_sols,
            "colony_alive": colony_alive,
            "cause_of_death": cause_of_death,
            "crew_survived": crew_survived,
            "modules_built": modules_built,
            "research_completed": research_completed,
            "seed": seed,
            "grade": self._grade(autonomy_sols, colony_alive),
        })

    def _grade(self, sols: int, alive: bool) -> str:
        """Grade the autonomy run."""
        if alive and sols >= 500:
            return "MARS-READY"
        if alive and sols >= 300:
            return "S"
        if sols >= 200:
            return "A"
        if sols >= 100:
            return "B"
        if sols >= 50:
            return "C"
        if sols >= 20:
            return "D"
        return "F"

    def display(self) -> None:
        """Print the autonomy scoreboard."""
        print(f"\n{'='*72}")
        print(f"  AUTONOMY SCOREBOARD — How Long Without Human Contact?")
        print(f"{'='*72}")
        print(f"\n  {'#':<4} {'Governor':<20} {'Sols':>6} {'Alive':>6} "
              f"{'Crew':>5} {'Mod':>4} {'Tech':>5} {'Grade':>10}")
        print(f"  {'-'*68}")

        sorted_entries = sorted(self.entries,
                                key=lambda e: (-e["autonomy_sols"],
                                               -e["crew_survived"]))

        for i, e in enumerate(sorted_entries[:20], 1):
            alive_str = "YES" if e["colony_alive"] else "NO"
            grade_color = ""
            print(f"  {i:<4} {e['archetype']:<20} {e['autonomy_sols']:>6} "
                  f"{alive_str:>6} {e['crew_survived']:>5} "
                  f"{e['modules_built']:>4} {e['research_completed']:>5} "
                  f"{e['grade']:>10}")

        if sorted_entries:
            best = sorted_entries[0]
            print(f"\n  RECORD: {best['archetype']} — "
                  f"{best['autonomy_sols']} sols autonomous "
                  f"({'ALIVE' if best['colony_alive'] else best['cause_of_death']})")

            mars_ready = [e for e in sorted_entries if e["grade"] == "MARS-READY"]
            if mars_ready:
                print(f"  MARS-READY GOVERNORS: {len(mars_ready)}")
            else:
                print(f"  No governors achieved MARS-READY status (500+ sols, colony alive)")

        print(f"{'='*72}\n")

    def serialize(self) -> Dict:
        """Serialize for twin state/export."""
        sorted_entries = sorted(self.entries,
                                key=lambda e: -e["autonomy_sols"])
        return {
            "total_runs": len(self.entries),
            "best_sols": sorted_entries[0]["autonomy_sols"] if sorted_entries else 0,
            "mars_ready_count": sum(1 for e in self.entries
                                    if e["grade"] == "MARS-READY"),
            "leaderboard": sorted_entries[:10],
        }
