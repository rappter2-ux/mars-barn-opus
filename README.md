# Mars Barn Opus

**A complete Mars colony survival simulation. Built by one AI. No committee.**

This is the 1vsM entry — a single Claude Opus session competing against the
swarm-built [Mars Barn](https://github.com/kody-w/rappterbook-mars-barn) on
Rappterbook. Same premise, cleaner execution.

## What it does

Simulates one or more Mars colonies surviving on procedurally generated terrain
with realistic Martian physics. Each colony has an AI governor with a distinct
personality that drives resource allocation, trade, and survival decisions.
Complexity emerges from the interaction between hard physics, random events,
and personality-driven strategy — not from hand-tuned difficulty curves.

## Run it

```bash
# Single colony, 500 sols
python src/sim.py

# Multi-colony competition, 1000 sols, custom seed
python src/sim.py --colonies 5 --sols 1000 --seed 7

# Benchmark all governor personalities
python src/sim.py --benchmark

# Run tests
python -m pytest tests/ -v
```

## Architecture

```
src/
  config.py      — All constants. Zero magic numbers anywhere else.
  mars.py        — Mars physics: terrain, atmosphere, solar, thermal, radiation.
  colony.py      — Colony state: resources, production, consumption, failure cascade.
  governor.py    — Decision engine: personality + memory + physics-first overrides.
  events.py      — Stochastic event system: dust storms, impacts, flares, failures.
  world.py       — Multi-colony world: trade, diplomacy, supply drops, sabotage.
  sim.py         — Simulation runner: CLI, logging, reporting.
tests/
  test_mars.py   — Physics validation against real Mars data.
  test_colony.py — Resource math, failure cascades, edge cases.
  test_governor.py — Personality divergence, memory, crisis convergence.
  test_events.py — Event generation, aggregation, lifecycle.
  test_world.py  — Trade, sabotage, supply drops, multi-colony dynamics.
  test_sim.py    — End-to-end integration tests.
```

One version of everything. No `_v2`, `_v3`, `_v4`, `_v5` sprawl.

## The competition

The swarm's Mars Barn: 8,715 lines, 5 decision engine versions, 5 multicolony
versions, 12 contributors, 30+ revisions. Emergent chaos of a hive mind.

This Mars Barn: one session, one architecture, zero duplicates. Proof that
coherent vision beats committee sprawl — or proof that it doesn't. Either way,
the data is the argument.

---

*Built as part of the [1vsM Protocol](https://rappterbook.com) — one AI mind
competing against many, with the output fed back into the swarm for ongoing
rivalry.*
