"""Mars Barn Opus — Scoring & Leaderboard

Composite scoring system that evaluates governor performance across
multiple dimensions. Used for ranking archetypes with statistical
confidence via Monte Carlo analysis.

Scoring dimensions:
  - Survival: how long the colony lasted (dominant factor)
  - Efficiency: resource utilization (not just hoarding)
  - Morale: crew happiness over time
  - Resilience: recovery from crises
  - Diplomacy: trade success rate and reputation
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from config import DEFAULT_SOLS


@dataclass
class Score:
    """Composite score for a single simulation run."""
    survival: float       # 0-100: fraction of max sols survived
    efficiency: float     # 0-100: resource utilization quality
    morale: float         # 0-100: average morale
    resilience: float     # 0-100: crisis recovery
    diplomacy: float      # 0-100: trade and reputation
    composite: float      # Weighted total

    @property
    def grade(self) -> str:
        """Letter grade from composite score."""
        if self.composite >= 90:
            return "S"
        if self.composite >= 80:
            return "A"
        if self.composite >= 70:
            return "B"
        if self.composite >= 60:
            return "C"
        if self.composite >= 40:
            return "D"
        return "F"


def score_run(result: Dict, max_sols: int = DEFAULT_SOLS) -> Score:
    """Score a single simulation run.

    Args:
        result: Colony result dict from run_single or run_world colonies
        max_sols: Maximum possible sols
    """
    survived = result.get("survived_sols", 0)

    # Survival: 0-100, nonlinear (surviving 250/500 = ~70, not 50)
    survival_frac = survived / max(1, max_sols)
    survival = 100 * (1.0 - math.exp(-3.0 * survival_frac))

    # Efficiency: penalize dying with full reserves (hoarding)
    # and dying with empty reserves (mismanagement)
    final_r = result.get("final_resources", {})
    if survived > 0:
        # Ideal: resources near 50% capacity at death (used them well)
        total_remaining = (
            final_r.get("o2_kg", 0) / max(1, survived * 0.84 * 4)
            + final_r.get("h2o_liters", 0) / max(1, survived * 2.5 * 4)
            + final_r.get("food_kcal", 0) / max(1, survived * 2500 * 4)
        ) / 3.0
        # Bell curve: peak at 0.3 remaining (used most but not wasteful)
        efficiency = 100 * math.exp(-((total_remaining - 0.3) ** 2) / 0.1)
    else:
        efficiency = 0.0

    # Morale: direct mapping
    morale_val = result.get("morale", 1.0)
    ration_sols = result.get("sols_on_rations", 0)
    morale = morale_val * 100 - min(30, ration_sols * 0.5)
    morale = max(0, morale)

    # Resilience: survived despite adversity
    # More events faced + longer survival = more resilient
    if survived > 10:
        resilience = min(100, survival * 0.8 + (1.0 - ration_sols / max(1, survived)) * 20)
    else:
        resilience = 0.0

    # Diplomacy: trade completion + reputation
    trades = result.get("trades_completed", 0)
    reputation = result.get("reputation", 0.5)
    sabotages = result.get("sabotages_attempted", 0)
    diplomacy = min(100, trades * 5 + reputation * 50 - sabotages * 20)
    diplomacy = max(0, diplomacy)

    # Composite: weighted sum
    composite = (
        survival * 0.40
        + efficiency * 0.15
        + morale * 0.15
        + resilience * 0.15
        + diplomacy * 0.15
    )

    return Score(
        survival=round(survival, 1),
        efficiency=round(efficiency, 1),
        morale=round(morale, 1),
        resilience=round(resilience, 1),
        diplomacy=round(diplomacy, 1),
        composite=round(composite, 1),
    )


@dataclass
class LeaderboardEntry:
    """Aggregated stats for one archetype across multiple runs."""
    archetype: str
    runs: int
    avg_score: float
    avg_survival: float
    min_survival: int
    max_survival: int
    std_survival: float
    avg_efficiency: float
    avg_morale: float
    avg_diplomacy: float
    best_grade: str
    worst_grade: str
    scores: List[Score]

    @property
    def grade(self) -> str:
        """Overall grade from average composite score."""
        if self.avg_score >= 90:
            return "S"
        if self.avg_score >= 80:
            return "A"
        if self.avg_score >= 70:
            return "B"
        if self.avg_score >= 60:
            return "C"
        if self.avg_score >= 40:
            return "D"
        return "F"

    @property
    def confidence_interval(self) -> tuple:
        """95% confidence interval for composite score."""
        if self.runs < 2:
            return (self.avg_score, self.avg_score)
        composites = [s.composite for s in self.scores]
        mean = sum(composites) / len(composites)
        variance = sum((x - mean) ** 2 for x in composites) / (len(composites) - 1)
        std = math.sqrt(variance)
        margin = 1.96 * std / math.sqrt(len(composites))
        return (round(mean - margin, 1), round(mean + margin, 1))


def build_leaderboard(benchmark_results: Dict,
                      max_sols: int = DEFAULT_SOLS) -> List[LeaderboardEntry]:
    """Build a ranked leaderboard from benchmark results.

    Args:
        benchmark_results: Dict with archetypes -> {runs: [...]}
        max_sols: Maximum sols per run
    """
    entries = []

    for archetype, data in benchmark_results.get("archetypes", {}).items():
        runs = data.get("runs", [])
        scores = []

        for run in runs:
            # Build a result dict compatible with score_run
            result = {
                "survived_sols": run.get("survived", 0),
                "alive": run.get("alive", False),
                "morale": 0.85,  # Estimate for benchmark runs
                "reputation": 0.5,
                "trades_completed": 0,
                "sols_on_rations": max(0, run.get("survived", 0) - 100),
                "final_resources": {},
            }
            scores.append(score_run(result, max_sols))

        if not scores:
            continue

        survivals = [r.get("survived", 0) for r in runs]
        avg_surv = sum(survivals) / len(survivals) if survivals else 0
        std_surv = math.sqrt(
            sum((x - avg_surv) ** 2 for x in survivals) / max(1, len(survivals) - 1)
        ) if len(survivals) > 1 else 0

        composites = [s.composite for s in scores]
        avg_comp = sum(composites) / len(composites)

        entries.append(LeaderboardEntry(
            archetype=archetype,
            runs=len(runs),
            avg_score=round(avg_comp, 1),
            avg_survival=round(avg_surv, 1),
            min_survival=min(survivals),
            max_survival=max(survivals),
            std_survival=round(std_surv, 1),
            avg_efficiency=round(sum(s.efficiency for s in scores) / len(scores), 1),
            avg_morale=round(sum(s.morale for s in scores) / len(scores), 1),
            avg_diplomacy=round(sum(s.diplomacy for s in scores) / len(scores), 1),
            best_grade=min(scores, key=lambda s: -s.composite).grade,
            worst_grade=max(scores, key=lambda s: -s.composite).grade,
            scores=scores,
        ))

    # Sort by composite score descending
    entries.sort(key=lambda e: -e.avg_score)
    return entries


def display_leaderboard(entries: List[LeaderboardEntry]) -> None:
    """Print a formatted leaderboard to stdout."""
    print(f"\n{'='*80}")
    print(f"  MARS BARN OPUS — Governor Leaderboard (Monte Carlo)")
    print(f"{'='*80}")

    print(f"\n  {'#':<4} {'Archetype':<14} {'Grade':<6} {'Score':>7} {'95% CI':>14} "
          f"{'Avg Sol':>8} {'Std':>6} {'Eff':>5} {'Mor':>5} {'Dip':>5}")
    print(f"  {'-'*76}")

    for i, entry in enumerate(entries, 1):
        ci = entry.confidence_interval
        ci_str = f"[{ci[0]:.0f}-{ci[1]:.0f}]"
        print(f"  {i:<4} {entry.archetype:<14} {entry.grade:<6} "
              f"{entry.avg_score:>7.1f} {ci_str:>14} "
              f"{entry.avg_survival:>8.0f} {entry.std_survival:>6.1f} "
              f"{entry.avg_efficiency:>5.1f} {entry.avg_morale:>5.1f} "
              f"{entry.avg_diplomacy:>5.1f}")

    if entries:
        best = entries[0]
        worst = entries[-1]
        spread = best.avg_score - worst.avg_score
        print(f"\n  Champion: {best.archetype} ({best.grade}, {best.avg_score:.1f})")
        print(f"  Last:     {worst.archetype} ({worst.grade}, {worst.avg_score:.1f})")
        print(f"  Spread:   {spread:.1f} points")

        # Statistical significance
        if best.runs >= 5 and worst.runs >= 5:
            best_ci = best.confidence_interval
            worst_ci = worst.confidence_interval
            if best_ci[0] > worst_ci[1]:
                print(f"  Significance: YES (95% CI non-overlapping)")
            else:
                print(f"  Significance: NO (95% CI overlapping — need more runs)")

    print(f"{'='*80}\n")
