"""Mars Barn Opus — Colony Economy with RAPPcoin

Internal currency for colony operations. Crew earn wages.
Modules have operating costs. Trade uses exchange rates.
Budget overruns force difficult choices.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Economy:
    """Colony economic state."""
    balance: float = 10000.0      # Starting RAPPcoin
    income_per_sol: float = 0.0
    expenses_per_sol: float = 0.0
    total_earned: float = 0.0
    total_spent: float = 0.0
    transactions: List[Dict] = field(default_factory=list)
    exchange_rates: Dict[str, float] = field(default_factory=lambda: {
        "o2_kg": 50.0,       # RAPPcoin per kg O2
        "h2o_liter": 30.0,   # per liter H2O
        "food_kcal": 0.02,   # per kcal
        "power_kwh": 10.0,   # per kWh
    })

    def tick(self, sol: int, crew_count: int, module_count: int,
             research_count: int) -> List[str]:
        """Process one sol of economics."""
        events = []
        # Income: base + research bonuses
        self.income_per_sol = 100 + research_count * 25 + module_count * 10
        # Expenses: crew wages + module upkeep
        crew_wages = crew_count * 30
        module_upkeep = module_count * 15
        self.expenses_per_sol = crew_wages + module_upkeep

        net = self.income_per_sol - self.expenses_per_sol
        self.balance += net
        self.total_earned += self.income_per_sol
        self.total_spent += self.expenses_per_sol

        if self.balance < 0:
            events.append(f"BUDGET DEFICIT: {self.balance:.0f} RAPPcoin")
        if self.balance < -5000:
            events.append("CRITICAL: Colony bankrupt — supply shipments halted")

        # Update exchange rates based on supply/demand
        self.exchange_rates["o2_kg"] = max(10, 50 - research_count * 3)
        self.exchange_rates["power_kwh"] = max(3, 10 - module_count * 0.5)

        self.transactions.append({
            "sol": sol, "income": self.income_per_sol,
            "expenses": self.expenses_per_sol, "balance": self.balance,
        })
        if len(self.transactions) > 500:
            self.transactions = self.transactions[-500:]

        return events

    def serialize(self) -> Dict:
        return {
            "balance": round(self.balance, 1),
            "income": round(self.income_per_sol, 1),
            "expenses": round(self.expenses_per_sol, 1),
            "total_earned": round(self.total_earned, 1),
            "total_spent": round(self.total_spent, 1),
            "exchange_rates": self.exchange_rates,
        }
