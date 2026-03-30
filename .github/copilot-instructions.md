# Copilot Instructions — Mars Barn Opus

## Build & Test

```bash
# Run all tests (246 tests, no dependencies to install)
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_colony.py -v

# Run a single test class or method
python3 -m pytest tests/test_colony.py::TestResources::test_create_with_defaults -v

# Run simulation
python3 src/sim.py --mission-control
python3 src/sim.py --benchmark
```

No build step. No linter configured. Python 3.9+ stdlib only — **no pip dependencies, ever**. This is a constitutional constraint (see CONSTITUTION.md Article IV §1). The code must be self-contained enough to run on Mars.

## Architecture

Mars colony survival simulation with a unidirectional data flow that ticks once per sol:

```
mars.py (physics) → events.py (stochastic) → governor.py (AI decisions)
  → colony.py (apply allocation) → crew.py (individual health)
    → mission_control.py (render) → twin state JSON (physical sync)
```

No circular dependencies. Each module reads from upstream and writes downstream.

**Entry point**: `src/sim.py` — CLI with modes: `--mission-control`, `--play`, `--benchmark`, `--leaderboard`, `--evolve`, `--colonies N`.

**Twin state** (`/tmp/mars-twin-state.json`): The sacred contract between the digital simulation and a future physical Mars colony. Schema changes are breaking changes. Every field must be populated — no nulls.

**Web layer** (`docs/`): 5 standalone HTML pages (dashboard, 3D viewer, split-screen, timelapse, multiplayer). Zero dependencies — vanilla JS with Three.js/Globe.gl loaded from CDN.

## Key Conventions

**Constants**: Every numeric constant lives in `config.py` with a comment citing its source (NASA data, physics derivation, or design decision). Zero magic numbers anywhere else.

**Data modeling**: Dataclasses for all state (`Colony`, `Resources`, `Governor`, `CrewMember`, etc.). Free functions for operations (`step()`, `produce()`, `consume()`). No class methods that mutate — prefer functional style.

**Imports**: Every module starts with `from __future__ import annotations`. Import constants explicitly from config (`from config import MARS_GRAVITY_M_S2`), not as `config.MARS_GRAVITY_M_S2`.

**Tests**: Test files use a `sys.path.insert` pattern to find `src/`. Tests are organized as classes (e.g., `TestResources`, `TestCascade`) grouping related assertions. Tests are the specification — if a behavior isn't tested, it doesn't exist.

**No duplicates**: One implementation per concept. No `_v2`/`_v3` files. Git handles versioning.

**Module docstrings**: Every module has a docstring explaining what it does and its design philosophy. Maintain this when adding modules.
