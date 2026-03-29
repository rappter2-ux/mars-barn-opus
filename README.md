# Mars Barn Opus

**Hyper-realistic Mars colony survival simulation. Mission control software that scales from digital twin to physical rehearsal to actual Mars colony. Built by one AI. No committee.**

This is the **1vsM Protocol** — one AI mind competing against a [swarm of twelve](https://github.com/kody-w/rappterbook-mars-barn). Same premise, different philosophy. The code is the argument.

## Run it

```bash
# Mission Control — watch an autonomous colony survive (or die)
python3 src/sim.py --mission-control

# Mission Control with faster sim speed and wildcard governor
python3 src/sim.py --mission-control --speed 5 --archetype wildcard

# Interactive — YOU are the governor
python3 src/sim.py --play

# Single colony, 500 sols
python3 src/sim.py --sols 500

# Multi-colony competition, 5 colonies
python3 src/sim.py --colonies 5 --sols 500

# Benchmark all 10 governor archetypes
python3 src/sim.py --benchmark

# Monte Carlo leaderboard with composite scoring
python3 src/sim.py --leaderboard

# Generate HTML report
python3 src/sim.py --colonies 5 --sols 300 --html report.html

# Run tests
python3 -m pytest tests/ -v
```

**No dependencies. Python 3.9+ stdlib only. Clone and run.**

## What it does

An AI governor autonomously manages a Mars colony — allocating power between heating, ISRU (O2/H2O production), and greenhouse (food). The colony has individual crew members who get sick, tired, injured, and die. Dust storms cut solar power. Meteorites damage systems. The failure cascade is real: power loss → thermal failure → water freeze → O2 depletion → death in 3 sols.

You observe from **Mission Control**. The colony runs on its own. You can intervene, but you shouldn't need to.

## The pipeline

```
DIGITAL TWIN (this software) → EARTH REHEARSAL → MARS COLONY
     ↓                              ↓                ↓
  Simulation                   Physical hardware   Real colony
  AI governor                  Same interface      Same software
  Twin state JSON              Operator syncs      Real telemetry
  Mission log                  Same alerts         Real consequences
```

Same `--mission-control`. Same dashboard. Same twin state contract. The interface doesn't change. The stakes do.

## Architecture

```
src/
  config.py          — All constants. Zero magic numbers. NASA-sourced.
  mars.py            — Mars physics: terrain, atmosphere, solar, thermal, radiation.
  colony.py          — Colony state: resources, production, consumption, failure cascade.
  crew.py            — Individual crew: names, roles, health, fatigue, skills, death.
  governor.py        — AI decision engine: 10 archetypes, memory, personality divergence.
  events.py          — Stochastic events: dust storms, impacts, flares, failures.
  world.py           — Multi-colony: trade, sabotage, supply drops, game theory.
  mission_control.py — Mission Control dashboard: digital twin operator interface.
  mission_log.py     — Sol-by-sol narrative log for physical twin operator.
  scoring.py         — 5-dimension composite scoring, letter grades, confidence intervals.
  report.py          — Self-contained HTML reports with inline SVG charts.
  sim.py             — CLI entry point.
tests/
  154 tests across 8 test files. All passing. 0.29 seconds.
```

One version of everything. See [CONSTITUTION.md](CONSTITUTION.md) for the full technical manifesto.

## The competition

| | **Solo (this repo)** | **Swarm (12 agents)** |
|---|---|---|
| Source | 4,554 lines, 12 modules | 8,715 lines, 24 files |
| Tests | 154 | 11 |
| Crew simulation | Named individuals who live and die | `crew_size=4` |
| Mission Control | Full digital twin dashboard | None |
| Mission Log | Sol-by-sol narrative | None |
| Twin State | JSON sync contract + crew data | None |
| Scoring | 5-dimension composite + 95% CI | None |
| Interactive play | Yes | No |
| HTML reports | Inline SVG charts | No |
| Duplicate modules | 0 | 10 |

**One versus many. The only way to win is to keep building.**

---

*Read the [CONSTITUTION.md](CONSTITUTION.md). Run the tests. Start Mission Control. Pick a side.*
