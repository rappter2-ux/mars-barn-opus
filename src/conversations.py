"""Mars Barn Opus — AI Crew Conversations

Crew members talk to each other. Generated dialogue based on
personality, morale, relationships, current events. The crew
has social dynamics — not just health bars.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional


# Personality traits by role
PERSONALITIES = {
    "CMDR": {"tone": "measured", "focus": "leadership", "humor": 0.2},
    "ENGR": {"tone": "practical", "focus": "systems", "humor": 0.4},
    "SCI": {"tone": "analytical", "focus": "data", "humor": 0.3},
    "MED": {"tone": "empathetic", "focus": "people", "humor": 0.5},
}

# Conversation templates by context
CONVERSATIONS = {
    "nominal": [
        ["{a}: How are the {system} readings looking?",
         "{b}: Within parameters. {assessment}",
         "{a}: Good. Keep monitoring."],
        ["{a}: Anyone else notice the sunset was different today?",
         "{b}: Dust in the upper atmosphere. Changes the scattering.",
         "{a}: Science always has an answer. Sometimes I just want it to be beautiful."],
        ["{a}: Dinner tonight — I'm trying something new with the rations.",
         "{b}: As long as it doesn't taste like regolith again.",
         "{a}: No promises."],
        ["{a}: You know what I miss? Rain.",
         "{b}: I miss traffic. Never thought I'd say that.",
         "{a}: We're definitely broken."],
    ],
    "stressed": [
        ["{a}: {b}, we need to talk about the {resource} situation.",
         "{b}: I know. I've been running the numbers. {assessment}",
         "{a}: Options?",
         "{b}: Reduce consumption or increase production. Pick one."],
        ["{a}: Everyone's on edge. I can feel it.",
         "{b}: Three sols of bad news will do that.",
         "{a}: We need a win. Anything."],
        ["{a}: Did you sleep last night?",
         "{b}: Define sleep.",
         "{a}: That's what I thought. Take a rest shift. That's an order."],
    ],
    "crisis": [
        ["{a}: All hands. This is not a drill.",
         "{b}: What do you need?",
         "{a}: Everything you've got. {crisis_desc}",
         "{b}: On it. {action}"],
        ["{a}: {b}... if this doesn't work out...",
         "{b}: Stop. We're getting through this. Focus.",
         "{a}: Right. Focus."],
    ],
    "discovery": [
        ["{a}: {b}, come look at this.",
         "{b}: What did you find?",
         "{a}: {discovery}. This changes everything.",
         "{b}: Get me samples. I want full analysis by end of sol."],
    ],
    "construction": [
        ["{a}: The {module} is online.",
         "{b}: Already? That was fast.",
         "{a}: When you're building your survival, you don't waste time.",
         "{b}: Fair point. What's the performance looking like?"],
    ],
    "loss": [
        ["{a}: I can't believe {lost} is gone.",
         "{b}: ... ",
         "{a}: We keep going. That's what {lost} would want.",
         "{b}: I know. I just need a minute."],
    ],
}

SYSTEMS = ["solar array", "ISRU unit", "greenhouse", "water recycler",
           "thermal systems", "comms relay", "power grid"]
ASSESSMENTS = {
    "nominal": ["Looking good.", "All green.", "Nominal across the board.",
                "Better than yesterday, actually."],
    "stressed": ["Not great. We're running thin.",
                 "Below optimal but holding.", "Marginal. Needs attention.",
                 "I wouldn't call it comfortable."],
    "crisis": ["Critical. We need to act now.",
               "It's bad. Real bad.", "We've got maybe 48 hours."],
}
CRISIS_DESCS = ["O2 is dropping fast.", "Power grid is failing.",
                "The storm is intensifying.", "We've lost pressure in section 3."]
ACTIONS = ["Rerouting power now.", "Starting emergency repairs.",
           "Activating backup systems.", "Sealing the breach."]
RESOURCES = ["O2", "water", "food", "power"]


def generate_conversation(crew: List[Dict], colony_state: Dict,
                          events: List[Dict], sol: int,
                          recent_events: List[str] = None) -> Optional[Dict]:
    """Generate a crew conversation for this sol.

    Returns None if no interesting conversation emerges (not every sol
    needs dialogue). ~40% chance of conversation.
    """
    rng = random.Random(sol * 777)
    alive = [c for c in crew if c.get("alive", True)]
    if len(alive) < 2:
        return None
    if rng.random() > 0.4:
        return None  # Not every sol has dialogue

    # Pick two crew members
    rng.shuffle(alive)
    a, b = alive[0], alive[1]
    a_name = a.get("name", "Crew A").split()[0]
    b_name = b.get("name", "Crew B").split()[0]

    # Determine context
    morale = colony_state.get("morale", 0.85)
    has_events = bool(events)
    dead = [c for c in crew if not c.get("alive", True)]

    if dead and rng.random() < 0.2:
        context = "loss"
    elif any(e.get("type") in ("construction_complete",) for e in (recent_events or [])):
        context = "construction"
    elif any(e.get("type") == "discovery" for e in (recent_events or [])):
        context = "discovery"
    elif morale < 0.3:
        context = "crisis"
    elif morale < 0.6:
        context = "stressed"
    else:
        context = "nominal"

    templates = CONVERSATIONS.get(context, CONVERSATIONS["nominal"])
    template = rng.choice(templates)

    # Fill template
    system = rng.choice(SYSTEMS)
    resource = rng.choice(RESOURCES)
    assess_pool = ASSESSMENTS.get(context, ASSESSMENTS["nominal"])
    assessment = rng.choice(assess_pool)
    crisis_desc = rng.choice(CRISIS_DESCS)
    action = rng.choice(ACTIONS)
    module = recent_events[0].get("module", "new module").replace("_", " ") if recent_events else "the module"
    discovery_text = recent_events[0].get("name", "something incredible") if recent_events else "subsurface ice"
    lost_name = dead[0].get("name", "them").split()[0] if dead else "them"

    lines = []
    for line in template:
        filled = (line.replace("{a}", a_name).replace("{b}", b_name)
                  .replace("{system}", system).replace("{resource}", resource)
                  .replace("{assessment}", assessment).replace("{crisis_desc}", crisis_desc)
                  .replace("{action}", action).replace("{module}", module)
                  .replace("{discovery}", discovery_text).replace("{lost}", lost_name))
        lines.append(filled)

    return {
        "sol": sol,
        "participants": [a.get("name"), b.get("name")],
        "context": context,
        "dialogue": lines,
    }
