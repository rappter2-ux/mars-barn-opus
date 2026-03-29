"""Mars Barn Opus — Event System

Stochastic events: dust storms, meteorite impacts, solar flares,
equipment failures, seasonal shifts, radiation spikes.

Events have lifecycle (generation -> active -> expiry), severity,
duration, and typed effects on colony systems/resources.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from config import (
    EVENT_PROBABILITIES, EVENT_DURATION_RANGE,
    MARS_SOLAR_FLARE_DOSE_MSV,
)


@dataclass
class Event:
    """A single active event."""
    event_type: str
    severity: float          # 0.0 to 1.0
    duration_sols: int       # Total duration
    remaining_sols: int      # Sols left
    effects: Dict[str, float] = field(default_factory=dict)
    description: str = ""
    sol_started: int = 0

    @property
    def expired(self) -> bool:
        """Whether this event has run its course."""
        return self.remaining_sols <= 0


# Event effect generators — each returns an effects dict based on severity

def _dust_storm_effects(severity: float) -> Dict[str, float]:
    """Dust storms reduce solar output, increase atmospheric opacity."""
    return {
        "solar_multiplier": 1.0 - 0.8 * severity,    # Up to 80% solar reduction
        "dust_factor": 1.0 + 3.0 * severity,          # Up to 4x optical depth
        "solar_damage": 0.02 * severity,               # Minor panel degradation
    }


def _dust_devil_effects(severity: float) -> Dict[str, float]:
    """Dust devils: minor, sometimes helpful (clean panels)."""
    return {
        "solar_multiplier": 1.0 - 0.1 * severity,
        "dust_factor": 1.0 + 0.3 * severity,
        # Dust devils can actually clean solar panels (Spirit rover!)
        "solar_repair": 0.01 * severity if severity < 0.3 else 0.0,
    }


def _solar_flare_effects(severity: float) -> Dict[str, float]:
    """Solar flares: radiation spike, possible electronics damage."""
    return {
        "radiation_msv": MARS_SOLAR_FLARE_DOSE_MSV * severity,
        "comms_damage": 0.1 * severity,
        "solar_damage": 0.05 * severity,  # Electronics degradation
    }


def _meteorite_effects(severity: float) -> Dict[str, float]:
    """Meteorite impacts: potentially catastrophic."""
    return {
        "solar_damage": 0.15 * severity,
        "greenhouse_damage": 0.20 * severity,
        "heating_damage": 0.10 * severity,
        "o2_loss": 5.0 * severity,        # Habitat breach leak
        "water_loss": 10.0 * severity,
    }


def _equipment_failure_effects(severity: float) -> Dict[str, float]:
    """Random equipment failure: affects one system badly."""
    # Pick a random system to fail more
    return {
        "isru_damage": 0.15 * severity,
        "power_loss": 20.0 * severity,
    }


def _seasonal_shift_effects(severity: float) -> Dict[str, float]:
    """Seasonal changes: gradual temperature and solar shifts."""
    return {
        "temp_offset_k": -10.0 * severity,  # Cooling trend
        "solar_multiplier": 1.0 - 0.15 * severity,
    }


def _radiation_spike_effects(severity: float) -> Dict[str, float]:
    """GCR spike: elevated background radiation."""
    return {
        "radiation_msv": 2.0 * severity,
    }


EFFECT_GENERATORS = {
    "dust_storm": _dust_storm_effects,
    "dust_devil": _dust_devil_effects,
    "solar_flare": _solar_flare_effects,
    "meteorite": _meteorite_effects,
    "equipment_failure": _equipment_failure_effects,
    "seasonal_shift": _seasonal_shift_effects,
    "radiation_spike": _radiation_spike_effects,
}

EVENT_DESCRIPTIONS = {
    "dust_storm": [
        "A regional dust storm darkens the sky.",
        "Massive dust plume approaching from the north.",
        "Global dust event — visibility near zero.",
        "Persistent haze reducing solar panel output.",
    ],
    "dust_devil": [
        "Dust devil spotted near the habitat.",
        "Small vortex passed over the solar array.",
    ],
    "solar_flare": [
        "Solar particle event detected — seeking shelter.",
        "Coronal mass ejection — radiation alarm triggered.",
    ],
    "meteorite": [
        "Meteorite impact detected nearby.",
        "Small impactor struck the outer perimeter.",
        "Bolide flash observed — checking for damage.",
    ],
    "equipment_failure": [
        "ISRU unit showing anomalous readings.",
        "Power converter malfunction.",
        "Pump failure in water recycling system.",
    ],
    "seasonal_shift": [
        "Entering Martian autumn — temperatures dropping.",
        "Perihelion approach — increased solar activity.",
        "Aphelion — reduced solar input for the season.",
    ],
    "radiation_spike": [
        "Elevated GCR levels detected.",
        "Background radiation above normal parameters.",
    ],
}


@dataclass
class EventEngine:
    """Manages event lifecycle: generation, ticking, expiry."""
    active_events: List[Event] = field(default_factory=list)
    event_log: List[Dict] = field(default_factory=list)
    rng: random.Random = field(default_factory=lambda: random.Random(42))

    def set_seed(self, seed: int) -> None:
        """Reset the RNG seed."""
        self.rng = random.Random(seed)

    def tick(self, sol: int) -> List[Event]:
        """Advance all events by one sol and generate new ones.

        Returns list of newly generated events this sol.
        """
        # Age existing events
        for event in self.active_events:
            event.remaining_sols -= 1

        # Remove expired
        expired = [e for e in self.active_events if e.expired]
        self.active_events = [e for e in self.active_events if not e.expired]

        for e in expired:
            self.event_log.append({
                "type": e.event_type,
                "started": e.sol_started,
                "ended": sol,
                "severity": e.severity,
            })

        # Generate new events
        new_events = self._generate(sol)
        self.active_events.extend(new_events)

        return new_events

    def _generate(self, sol: int) -> List[Event]:
        """Roll for new events this sol."""
        new_events = []
        active_types = {e.event_type for e in self.active_events}

        for event_type, probability in EVENT_PROBABILITIES.items():
            # No stacking: same event type can't overlap
            if event_type in active_types:
                continue

            if self.rng.random() < probability:
                severity = self.rng.uniform(0.2, 1.0)
                dur_range = EVENT_DURATION_RANGE[event_type]
                duration = self.rng.randint(dur_range[0], dur_range[1])

                # Scale duration with severity for storms
                if event_type == "dust_storm" and severity > 0.7:
                    duration = int(duration * 1.5)

                gen = EFFECT_GENERATORS[event_type]
                effects = gen(severity)

                descriptions = EVENT_DESCRIPTIONS.get(event_type, ["Event occurred."])
                desc = self.rng.choice(descriptions)

                event = Event(
                    event_type=event_type,
                    severity=severity,
                    duration_sols=duration,
                    remaining_sols=duration,
                    effects=effects,
                    description=desc,
                    sol_started=sol,
                )
                new_events.append(event)

        return new_events

    def aggregate_effects(self) -> Dict[str, float]:
        """Aggregate all active event effects into a single dict.

        Multipliers are multiplicative. Additive values are summed.
        """
        result: Dict[str, float] = {}

        for event in self.active_events:
            for key, value in event.effects.items():
                if key.endswith("_multiplier"):
                    # Multiplicative
                    result[key] = result.get(key, 1.0) * value
                elif key.endswith("_offset") or key.endswith("_factor"):
                    # Special: take the max
                    result[key] = max(result.get(key, 0.0), value)
                else:
                    # Additive
                    result[key] = result.get(key, 0.0) + value

        return result

    def active_event_dicts(self) -> List[Dict]:
        """Return active events as plain dicts for colony.apply_events()."""
        return [{"type": e.event_type, "effects": e.effects,
                 "severity": e.severity, "description": e.description}
                for e in self.active_events]
