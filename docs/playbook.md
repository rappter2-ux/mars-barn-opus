# The Rappter Playbook
## From Brainstem to Mars Colony: Building Living Simulations

*A practical guide to building simulations that think, react, and survive — using the same patterns that keep a velociraptor alive and a Mars colony running.*

*Structured like the Warthog Data Book: each chapter builds on the last, each concept is immediately applicable, and the Mars colony sim is the thread that ties everything together.*

---

## How to Read This Book

Each chapter introduces one concept, implements it in code, and shows how it appears in the Mars colony sim. You can:

1. **Read it straight through** — builds from "what is a tick?" to "autonomous Mars colony"
2. **Jump to what you need** — each chapter is self-contained with runnable code
3. **Build along** — every chapter has a working example you can run locally

The code is Python 3.9+ stdlib only. No pip. No npm. The Mars colony sim is the capstone project — by the time you finish, you'll understand every system in it.

---

## Part I: The Heartbeat

### Chapter 1: The Tick

Everything starts with a tick. A tick is one discrete step of simulation time. The world updates, then waits for the next tick. This is the most basic possible simulation:

```python
state = {"temperature": 20.0, "time": 0}

def tick(state):
    state["time"] += 1
    state["temperature"] += random.uniform(-0.5, 0.5)
    return state

for _ in range(100):
    state = tick(state)
    print(f"t={state['time']} temp={state['temperature']:.1f}")
```

**The problem:** Between ticks, nothing happens. The simulation is unconscious. If the temperature drops to -50 between tick 47 and tick 48, nothing reacts until tick 48 arrives. In real life, you'd be dead by then.

**Mars connection:** One sol (Martian day) is one tick. If O₂ runs out between Sol 47 and Sol 48, the colony dies without ever reacting. The sim needs to be smarter than this.

---

### Chapter 2: State and Delta

A tick produces two things: the **state** (where everything is) and the **delta** (what changed). Most simulations throw away the delta. Don't.

```python
def tick(state):
    pre = {"temp": state["temp"], "o2": state["o2"]}
    
    # Simulation logic
    state["temp"] += solar_heating() - radiative_cooling()
    state["o2"] += isru_production() - crew_consumption()
    
    # Compute delta
    delta = {
        "temp": state["temp"] - pre["temp"],
        "o2": state["o2"] - pre["o2"],
    }
    
    return state, delta
```

The delta tells you **how things are changing**, not just where they are. A temperature of 15°C means nothing by itself. A temperature of 15°C that was 25°C last tick means the heating is failing.

**Mars connection:** The echo frame. Every sol, the sim produces a delta: O₂ change, H₂O change, food change, power change, events that fired, crew health changes. This delta IS the colony's self-awareness.

---

### Chapter 3: Data Sloshing

The output of tick N becomes the input of tick N+1. This is **data sloshing** — state flowing forward through time, each frame building on the last.

```python
echo_history = []

for sol in range(1000):
    state, delta = tick(state)
    echo = {"frame": sol, "delta": delta, "state_snapshot": snapshot(state)}
    echo_history.append(echo)
    
    # Frame N+1 can read everything that happened in frames 0..N
    # The past informs the present. Context accumulates.
```

Data sloshing is what makes simulations feel intelligent over time. A single tick is dumb. A thousand ticks with accumulated context is smart. The colony at Sol 500 knows everything that happened since Sol 1 — every storm, every failure, every decision.

**Mars connection:** The echo history. 500 frames of deltas. The post-mortem can trace exactly which sol, which decision, which event led to death. Causality is preserved in the data.

---

## Part II: The Nervous System

### Chapter 4: The Echo

After each tick, extract a **structured summary** — the echo. This is the brainstem: not thought, but sensation. "I can feel my heartbeat. I can feel that my left arm is cold."

```python
def compute_echo(state, delta, events):
    n = max(1, state["crew_alive"])
    return {
        "frame": state["sol"],
        "utc": datetime.utcnow().isoformat(),
        "delta": delta,
        "events": events,
        "alert": classify_alert(state, delta, n),
        "visual": {
            "dust_storm": any(e["type"] == "dust_storm" for e in state["events"]),
            "night": state["mars_hour"] < 6 or state["mars_hour"] > 19,
        },
    }
```

The echo is a compressed representation of one heartbeat. It's cheap to store, cheap to read, and contains everything any downstream system needs to react.

**Mars connection:** Every sol produces an echo with delta, events, crew events, build events, visual hints, and alert classification. The 3D scene, the task system, and the reflex arcs all read the echo — not the raw state.

---

### Chapter 5: Inertia — The Derivative

A single echo says "O₂ is at 15 days." Two echoes say "O₂ was at 20 days and is now at 15 days — it's dropping at 5 days/sol." That's **inertia** — the derivative of state.

```python
def compute_inertia(echo_history):
    if len(echo_history) < 2:
        return {"trend": "unknown"}
    
    curr = echo_history[-1]
    prev = echo_history[-2]
    
    return {
        "o2_velocity": curr["delta"]["o2"] - prev["delta"]["o2"],
        "power_velocity": curr["delta"]["power"] - prev["delta"]["power"],
        "engagement_trend": classify_trend(curr, prev),
        "discourse_flips": find_flips(curr, prev),  # systems that changed direction
    }
```

The body doesn't wait until the hand is burned. It fires when the temperature is *rising*. Inertia lets the simulation react to trajectories, not just thresholds.

**Mars connection:** `echoInertia` tracks o2_velocity, h2o_velocity, food_velocity, power_velocity, engagement_trend, crew_trajectory, cri_direction, and discourse_flips. Tasks trigger on trajectories. Reflexes fire on acceleration. The colony reacts to the trend before the threshold is crossed.

---

### Chapter 6: Reflex Arcs

A reflex arc is a pre-computed IF/THEN rule generated by the last tick. It fires between ticks — no expensive computation needed. The brain already did the thinking. The reflex is the residue.

```python
def compute_reflex_arcs(state, echo, inertia):
    arcs = []
    
    if inertia["o2_velocity"] < -0.3 and state["o2_days"] < 15:
        arcs.append({
            "id": "o2_trajectory",
            "condition": f"O₂ dropping at {inertia['o2_velocity']:.2f}/sol²",
            "action": "boost_isru",
            "intensity": min(1.0, abs(inertia["o2_velocity"])),
            "state_effect": lambda s: adjust_alloc(s, isru=+0.05),
            "ttl_frames": 1,
        })
    
    return arcs
```

**Key insight:** Each reflex has a `state_effect` — it moves muscles, not just flashes lights. The colony auto-boosts ISRU when O₂ is trending down. It doesn't wait for a human to notice. It doesn't wait for the next tick. It reacts NOW.

**Mars connection:** 10 reflex arcs — O₂ boost, power shed, crew ration, system flip, CRI stress, dust storm, solar flare shelter, night power conservation, food emergency, robot compensation. Each modifies actual allocation state. Manual override from the player always takes priority.

---

### Chapter 7: The Patrol

The patrol is a lightweight process that runs **between ticks**, reading the reflex arcs (standing orders) and applying their effects continuously.

```python
# In a game, this runs on requestAnimationFrame (~60Hz)
# In a server sim, this runs on a timer (~1Hz)
def patrol(active_reflexes, state):
    for reflex in active_reflexes:
        if reflex["ttl_frames"] <= 0:
            continue
        
        # Apply visual effects (the symptoms you see)
        apply_visual(reflex)
        
        # Note: state_effect already applied at arc computation time
        # The patrol handles ongoing visuals between frames
```

The frame is the briefing. The echo is the patrol route. The agent acts autonomously between briefings. When the next frame runs, it produces fresh arcs that replace the old ones.

**Mars connection:** `runPatrol()` executes on every 3rd animation frame (~20Hz). It reads the active reflexes and applies visual effects: resource bar pulsing, scene dimming, crew alerts, fog density, screen vignette. The colony LOOKS alive between sols because it IS alive between sols.

---

### Chapter 8: The Feedback Loop

Here's where it gets powerful. Reflexes that fire between frames are **logged with frame key + UTC timestamp**. When the next frame arrives, it reads those reflex events as input context. The colony's reactions to its own reactions become part of the next thought.

```python
# Frame N produces echo → reflex arcs generated
# Between frames: reflexes fire, logged to reflex_history
# Frame N+1 reads reflex_history as additional context

echo = {
    "frame": sol,
    "delta": delta,
    "inertia": inertia,
    "reflexes_fired": get_reflexes_since(sol - 1),  # what happened between heartbeats
    "cri": colony_risk_index,
}
```

Frame N+1 doesn't just know "O₂ is at 12 days." It knows "O₂ was at 15 days, the O₂ reflex fired and boosted ISRU by 5%, and O₂ is now at 12 days despite the boost — the situation is worse than the reflex can handle." That's when a task gets generated for the player.

**Mars connection:** `reflexes_fired[]` in the echo frame. The task generation system (`generateTask`) reads the echo including reflexes. If the reflexes weren't enough, the task system escalates to the player. The organism tried to handle it autonomously. It couldn't. Now it needs mission control.

---

## Part III: Risk and Emergence

### Chapter 9: The Colony Risk Index

Not all ticks are equal. A colony at CRI 10 (LOW) can absorb a dust storm. A colony at CRI 70 (CRITICAL) gets destroyed by the same storm. Risk is **cumulative** — bad decisions and bad luck compound.

```python
CRI_PROGRAM = """
(begin
  (define base_risk 10)
  (define o2_risk (if (< o2_days 5) 30 (if (< o2_days 10) 15 0)))
  (define food_risk (if (< food_days 5) 25 (if (< food_days 10) 12 0)))
  (define power_risk (if (< power_kwh 50) 25 (if (< power_kwh 150) 12 0)))
  (define crew_risk (* (- crew_total crew_alive) 8))
  (define morale_risk (if (< morale 30) 20 (if (< morale 50) 10 0)))
  (set! colony_risk_index (min 100 (+ base_risk o2_risk food_risk 
    power_risk crew_risk morale_risk))))
"""
```

CRI is computed by LisPy every sol — a sandboxed Lisp VM that runs colony control programs. The CRI feeds into `riskRoll(baseProb)` — a function that multiplies base probability by a CRI factor. At CRI 0, a 5% event stays 5%. At CRI 100, it becomes 15%.

**Mars connection:** CRI is displayed in the HUD and status bar. It drives task probability, ambient hazard frequency, and secondary consequence likelihood. The post-mortem shows final CRI and traces how it climbed through decisions.

---

### Chapter 10: Echo-Driven Emergence

Tasks don't spawn from random rolls. They **emerge from echo data**. The echo says "dust storm active + solar efficiency dropping + power delta negative" and the task system generates "SOLAR ARRAY MISALIGNMENT — dust-driven actuator drift."

```python
def generate_task(state, echo):
    for template in TASK_TEMPLATES:
        if template.trigger(state, echo):  # echo context + risk probability
            task = template.gen(state, echo)
            task["source_echo"] = echo["frame"]
            task["cri"] = colony_risk_index
            return task
    return None
```

Each trigger combines echo context (what's actually happening) with `riskRoll()` (statistical probability). The echo tells us the SITUATION. The risk roll determines if it MANIFESTS this sol. Both matter. Sometimes bad luck hits a healthy colony. That's Mars.

**Mars connection:** All 17 task triggers use echo data. Dust storms increase panel misalignment probability. Cold temps cause actuator stiffness. Night transitions increase thermal crack risk. The sim's physics drives the emergent gameplay.

---

### Chapter 11: Ambient Hazards

Some things just happen. Micrometeorites don't care about your decisions. Solar particle events don't wait for a convenient time. Equipment wears out whether you're ready or not.

```python
def roll_ambient_hazards(state, cri):
    # Micrometeorite — tiny but real
    if risk_roll(0.001, cri):
        target = random.choice(["solar", "isru", "greenhouse", "habitat"])
        damage_system(state, target, 0.03 + random.random() * 0.05)
    
    # Regolith infiltration — dust gets into everything
    if risk_roll(0.003, cri):
        degrade_seals(state)
    
    # Equipment fatigue — nothing lasts forever on Mars
    if state["sol"] > 100 and risk_roll(0.002, cri):
        degrade_random_system(state, 0.04)
```

These fire every sol, independent of player decisions. They're CRI-weighted — a stressed colony is more vulnerable. The post-mortem counts ambient hazards separately from decision consequences.

**Mars connection:** Micrometeorites (0.1%), regolith dust infiltration (0.3%), solar particle events (0.2%), equipment fatigue, solar conjunction blackouts. All based on NASA Mars surface data.

---

## Part IV: The Player as Mission Control

### Chapter 12: Papers Please — Decision Tasks

The AI runs the colony. The player handles exceptions. Tasks emerge from echo data — the autonomous system tried to handle it, couldn't, and is escalating to mission control.

Each task has:
- **Trigger:** echo condition + risk probability
- **Approve/Deny/Alternative:** each with real state effects
- **Timeout:** AI defaults if player doesn't respond (usually the worse option)
- **Secondary consequences:** `riskRoll`-weighted unintended effects
- **Source echo:** which frame spawned this task (traceable in post-mortem)

**Mars connection:** 11 decision tasks (O₂ reroute, water crisis, medical, pressure leak, pipe burst, ISRU catalyst, solar tracking, CO₂ scrubber, thermal crack, radiation dosimetry, power rationing) + 7 manual override tasks.

---

### Chapter 13: Manual Override — Remote Operations

Sometimes approve/deny isn't enough. The robot is stuck. You need to guide it through a physical procedure with light delay. Send commands one at a time. Each arrives delayed. Correct sequence = fixed. Wrong sequence = broken worse.

```python
override = {
    "commands": [
        {"label": "🧴 APPLY PENETRANT", "response": "Penetrant soaking..."},
        {"label": "⏳ WAIT 30s", "response": "Penetrant wicked into threads."},
        {"label": "🔥 HEAT CYCLE", "response": "Thermal expansion applied."},
        {"label": "🔧 EXTRACT CCW", "response": "Bolt extracted!"},
        {"label": "🔧 EXTRACT CW", "fail": "WRONG DIRECTION. Threads stripped."},
        {"label": "💪 FORCE", "fail": "Bolt head sheared off. Drill needed."},
    ],
    "correct_sequence": [0, 1, 2, 3],
    "delay_seconds": 3,  # light delay per command
}
```

Trap commands look like the obvious choice. The correct path is always: slow, diagnostic-first, methodical. That's real remote ops. The skill learned in the sim IS the skill needed on Mars.

**Mars connection:** 7 override scenarios — stuck bolt, panel cleaning, antenna realignment, airlock seal, robot tipped, wheel jam, panel deploy failure. Each with light delay, correct sequence, and trap commands.

---

### Chapter 14: The Post-Mortem

When the colony dies, trace the full causal chain:

1. **Decision chain** — player's last 8 approve/deny/timeout calls
2. **Unintended consequences** — every secondary effect that fired
3. **Ambient hazards endured** — Mars-caused events
4. **Reflex history** — what the nervous system tried autonomously
5. **Crew status at death** — individual HP, morale, radiation
6. **System degradation** — solar/ISRU/greenhouse efficiency
7. **What might have saved you** — specific, actionable analysis
8. **Autonomy grade** — F through MARS-READY (500+ sols)

Every death is a lesson. Every lesson makes you better at keeping a colony alive.

---

## Part V: The Full Architecture

### Chapter 15: Putting It All Together

```
┌─────────────────────────────────────────────────────┐
│                    CORTEX (sol tick)                  │
│  stepSim() — production, consumption, events, AI    │
│  Runs every 0.5-5s (player speed control)           │
│                                                      │
│  Output: echo frame (delta + events + visual)        │
├─────────────────────────────────────────────────────┤
│                  BRAINSTEM (echo)                     │
│  computeInertia() — derivatives of colony state     │
│  computeCRI() — Colony Risk Index via LisPy VM      │
│  generateTask() — echo-driven task emergence        │
│  rollAmbientHazards() — Mars doesn't wait           │
│                                                      │
│  Output: inertia signal + reflex arcs + CRI          │
├─────────────────────────────────────────────────────┤
│                SPINAL CORD (reflexes)                 │
│  computeReflexArcs() — 10 IF/THEN standing orders   │
│  Each arc has stateEffect() — moves muscles          │
│  Fires immediately after echo computation            │
│                                                      │
│  Output: active_reflexes[] + reflex_history[]        │
├─────────────────────────────────────────────────────┤
│                   PATROL (~20Hz)                     │
│  runPatrol() — on animation frame between sols      │
│  Reads standing orders, applies visual effects       │
│  Colony looks alive because it IS alive              │
│                                                      │
│  Output: continuous visual feedback                  │
├─────────────────────────────────────────────────────┤
│                 PLAYER (mission control)              │
│  Papers Please tasks — approve/deny/override         │
│  Manual overrides — step-by-step with light delay   │
│  Emergency buttons — shelter, ISRU boost, ration     │
│  Always overrides reflexes when player acts           │
├─────────────────────────────────────────────────────┤
│              FEEDBACK LOOP (data sloshing)            │
│  Frame N echo → reflexes fire → logged with UTC     │
│  Frame N+1 echo includes reflexes_fired[]           │
│  Colony's reactions become input to next thought     │
│  Risk accumulates. Mars doesn't forget.              │
└─────────────────────────────────────────────────────┘
```

### Chapter 16: Clock Speeds

| Layer | Clock | What It Does |
|-------|-------|-------------|
| Cortex | 1 per sol (0.05-0.5s real time) | Full sim tick — production, consumption, events, AI |
| Brainstem | 1 per sol (after cortex) | Echo, inertia, CRI, task generation |
| Spinal Cord | 1 per sol (after brainstem) | Reflex arc computation, state effects |
| Patrol | ~20Hz (every 3rd animation frame) | Visual effects from active reflexes |
| Player | Async (whenever task arrives) | Decision tasks and manual overrides |
| 3D Scene | ~60Hz (animation frame) | Render, camera, dust, crew movement |

Each layer runs at its own speed. The cortex is slow and expensive. The patrol is fast and cheap. Together they give the colony continuous responsiveness even though it only "thinks" once per sol.

---

## Appendix A: Running the Mars Colony Sim

```bash
# Clone
git clone https://github.com/kody-w/mars-barn-opus.git
cd mars-barn-opus

# Run tests (299 tests, no dependencies)
python3 -m pytest tests/ -v

# Play in browser
open docs/viewer.html

# Or: https://kody-w.github.io/mars-barn-opus/

# CLI simulation
python3 src/sim.py --mission-control    # watch colony live
python3 src/sim.py --autonomy --sols 500 # autonomy scoreboard
python3 src/sim.py --benchmark           # all 10 archetypes
```

## Appendix B: The Constitution

Read `CONSTITUTION.md`. It's the law of the codebase. Article V defines the core game loop. Amendment I renamed the project. Amendment II ratified the Digital Twin Mandate.

## Appendix C: LisPy Reference

The colony runs on LisPy — a sandboxed Lisp interpreter. Same language runs in Python (`src/lispy.py`) and JavaScript (`docs/viewer.html`). S-expressions are both data AND executable code.

```lisp
(begin
  (define crisis (< (min o2_days h2o_days food_days) 10))
  (if crisis
    (begin
      (set! isru_alloc 0.70)
      (set! greenhouse_alloc 0.15)
      (set! heating_alloc 0.15)
      (set! food_ration 0.50))
    (begin
      (set! isru_alloc 0.40)
      (set! greenhouse_alloc 0.35)
      (set! heating_alloc 0.25)
      (set! food_ration 1.0))))
```

Write your own LisPy governor. Beat the autonomy scoreboard. The code IS the game.

---

*The Rappter Playbook. From brainstem to Mars colony.*
*The simulation has a heartbeat. Now it has reflexes.*
*The organism thinks every sol. It reacts every 50ms. It never sleeps.*
