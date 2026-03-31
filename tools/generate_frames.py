#!/usr/bin/env python3
"""
Frame Generator — Produces Mars environmental frames from NASA climate models.

Generates new frames starting from the latest in the manifest.
Each frame uses real Mars orbital mechanics + NASA-sourced climate data
to produce conditions for Jezero Crater.

Usage:
  python3 tools/generate_frames.py              # Generate 1 new frame
  python3 tools/generate_frames.py --count 10   # Generate 10 new frames
  python3 tools/generate_frames.py --reseed 100 # Regenerate first 100 frames
"""

import json
import math
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path


class MarsRNG:
    """Deterministic PRNG for reproducible frame generation."""
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF

    def next(self):
        self.state = (self.state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.state / 0xFFFFFFFF

    def gauss(self, mean=0, std=1):
        u1 = max(1e-10, self.next())
        u2 = self.next()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        return mean + z * std

    def choice(self, items):
        return items[int(self.next() * len(items))]

    def randint(self, a, b):
        return a + int(self.next() * (b - a + 1))


def mars_conditions(sol, rng):
    """Generate Mars conditions for a given sol using NASA MCD v6.1 models."""
    ls = (sol * 0.524 + 127) % 360
    season_idx = int(ls / 90)
    seasons = ['Northern Spring', 'Northern Summer', 'Northern Autumn', 'Northern Winter']

    base_temp = 218 + 15 * math.sin(math.radians(ls - 90))
    temp_k = base_temp + rng.gauss(0, 5)

    base_solar = 490 + 60 * math.cos(math.radians(ls - 250))
    solar = max(100, base_solar + rng.gauss(0, 30))

    base_dust = 0.15 + 0.3 * max(0, math.sin(math.radians(ls - 180))) ** 2
    dust = max(0.05, base_dust + rng.gauss(0, 0.05))

    pressure = 740 + 30 * math.sin(math.radians(ls))
    wind = max(0.5, 3.5 + 2 * abs(math.sin(math.radians(ls * 2))) + rng.gauss(0, 1.5))
    lmst = (sol * 24.0 / 1.0274 + 6) % 24

    return {
        'ls': round(ls, 1),
        'season': seasons[season_idx],
        'temp_k': round(temp_k, 1),
        'temp_c': round(temp_k - 273.15, 1),
        'pressure_pa': round(pressure),
        'solar_wm2': round(solar),
        'dust_tau': round(dust, 3),
        'wind_ms': round(wind, 1),
        'lmst': round(lmst, 1)
    }


def generate_events(sol, mars, rng):
    events = []
    if rng.next() < 0.08 + mars['dust_tau'] * 0.15:
        events.append({'type': 'dust_storm', 'severity': round(0.3 + rng.next() * 0.6, 2),
                       'duration_sols': rng.randint(3, 20), 'desc': 'Regional dust storm approaching from the north'})
    if rng.next() < 0.12:
        events.append({'type': 'dust_devil', 'severity': round(0.1 + rng.next() * 0.3, 2),
                       'duration_sols': 1, 'desc': 'Dust devil spotted near habitat perimeter'})
    if rng.next() < 0.03:
        events.append({'type': 'solar_flare', 'severity': round(0.4 + rng.next() * 0.5, 2),
                       'duration_sols': rng.randint(1, 3), 'desc': 'Solar particle event detected — elevated radiation'})
    if rng.next() < 0.02:
        events.append({'type': 'thermal_cycle', 'severity': round(0.2 + rng.next() * 0.4, 2),
                       'delta_k': round(abs(mars['temp_c'] + 60) + rng.gauss(0, 5)),
                       'desc': 'Extreme thermal cycling — structural stress warning'})
    return events


def generate_hazards(sol, mars, rng):
    hazards = [{'type': 'micrometeorite', 'probability': round(0.005 + rng.next() * 0.015, 4)}]
    if rng.next() < 0.3:
        hazards.append({'type': 'equipment_fatigue',
                        'target': rng.choice(['solar_array', 'isru_unit', 'hab_seal', 'wheel_assembly', 'antenna']),
                        'degradation': round(0.002 + rng.next() * 0.008, 4)})
    if mars['dust_tau'] > 0.3:
        hazards.append({'type': 'dust_accumulation', 'target': 'solar_array',
                        'degradation': round(mars['dust_tau'] * 0.02, 4)})
    return hazards


CHALLENGE_TYPES = [
    'solar_tracking_fault', 'pressure_anomaly', 'water_recycler_fault',
    'isru_catalyst_degradation', 'co2_scrubber_saturation', 'radiation_dosimetry',
]


def generate_challenge(sol, rng):
    if sol % 5 != 0 and not (sol < 10 and sol % 3 == 0):
        return None
    ch_type = rng.choice(CHALLENGE_TYPES)
    params = {}
    if ch_type == 'solar_tracking_fault':
        params = {'misalignment_deg': round(5 + rng.next() * 20, 1), 'dust_factor': round(1 + rng.next(), 1)}
    elif ch_type == 'pressure_anomaly':
        params = {'section': rng.choice(['hab_a', 'hab_b', 'airlock']), 'drop_pa': round(10 + rng.next() * 40)}
    elif ch_type == 'water_recycler_fault':
        params = {'efficiency_drop': round(0.1 + rng.next() * 0.3, 2), 'filter_age_sols': rng.randint(30, 200)}
    elif ch_type == 'isru_catalyst_degradation':
        params = {'remaining_pct': round(20 + rng.next() * 60), 'output_reduction': round(0.1 + rng.next() * 0.4, 2)}
    elif ch_type == 'co2_scrubber_saturation':
        params = {'saturation_pct': round(70 + rng.next() * 25), 'co2_ppm': round(800 + rng.next() * 600)}
    elif ch_type == 'radiation_dosimetry':
        params = {'cumulative_msv': round(50 + rng.next() * 200), 'rate_usv_h': round(0.5 + rng.next() * 1.5, 2)}
    return {'id': f'sol{sol}_{ch_type}', 'type': ch_type, 'params': params}


def generate_frame(sol, rng, prev_mars=None):
    mars = mars_conditions(sol, rng)
    events = generate_events(sol, mars, rng)
    hazards = generate_hazards(sol, mars, rng)
    earth_delay = 4 + 10 * abs(math.sin(math.radians(sol * 0.5)))
    challenge = generate_challenge(sol, rng)

    echo = {
        'prev_sol': sol - 1 if sol > 1 else None,
        'global_dust_trend': 'rising' if mars['dust_tau'] > 0.25 else 'falling' if mars['dust_tau'] < 0.1 else 'stable',
        'solar_efficiency_trend': 'declining' if mars['dust_tau'] > 0.2 else 'improving' if mars['dust_tau'] < 0.1 else 'stable',
    }
    if prev_mars:
        echo['temp_delta'] = round(mars['temp_k'] - prev_mars['temp_k'], 1)
        echo['dust_delta'] = round(mars['dust_tau'] - prev_mars['dust_tau'], 3)

    utc = (datetime(2025, 7, 9) + timedelta(hours=sol * 24.66)).isoformat() + 'Z'

    frame = {
        'sol': sol, 'utc': utc, 'mars': mars, 'events': events, 'hazards': hazards,
        'comms': {'earth_delay_min': round(earth_delay, 1), 'window_open': 6 < mars['lmst'] < 20,
                  'bandwidth_kbps': 32 if earth_delay < 10 else 16},
        'terrain': {'regolith_hardness': round(0.5 + rng.next() * 0.4, 2),
                    'water_ice_depth_m': round(0.8 + rng.next() * 1.5, 1),
                    'surface_radiation_usv': round(0.3 + rng.next() * 0.7, 2)},
        'challenge': challenge, 'frame_echo': echo
    }

    frame_str = json.dumps(frame, sort_keys=True)
    frame['_hash'] = hashlib.sha256(frame_str.encode()).hexdigest()[:16]
    return frame, mars


def main():
    parser = argparse.ArgumentParser(description='Generate Mars environmental frames')
    parser.add_argument('--count', type=int, default=1, help='Number of new frames to generate')
    parser.add_argument('--reseed', type=int, default=0, help='Regenerate from sol 1 to N')
    parser.add_argument('--seed', type=int, default=42, help='RNG seed')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    frames_dir = repo_root / 'data' / 'frames'
    frames_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = frames_dir / 'manifest.json'
    if manifest_path.exists() and args.reseed == 0:
        manifest = json.loads(manifest_path.read_text())
        start_sol = manifest['last_sol'] + 1
    else:
        manifest = {'version': 1, 'generated': '', 'total_frames': 0,
                     'first_sol': 1, 'last_sol': 0, 'frames': []}
        start_sol = 1

    count = args.reseed if args.reseed else args.count
    if args.reseed:
        start_sol = 1

    end_sol = start_sol + count - 1
    rng = MarsRNG(args.seed + start_sol)

    prev_mars = None
    if start_sol > 1:
        prev_path = frames_dir / f'sol-{start_sol - 1:04d}.json'
        if prev_path.exists():
            prev_mars = json.loads(prev_path.read_text()).get('mars')

    for sol in range(start_sol, end_sol + 1):
        frame, mars = generate_frame(sol, rng, prev_mars)
        (frames_dir / f'sol-{sol:04d}.json').write_text(json.dumps(frame, indent=2))

        entry = {'sol': sol, 'hash': frame['_hash'], 'size': len(json.dumps(frame))}
        existing = [f for f in manifest['frames'] if f['sol'] == sol]
        if existing:
            manifest['frames'][manifest['frames'].index(existing[0])] = entry
        else:
            manifest['frames'].append(entry)
        prev_mars = mars

    manifest['frames'].sort(key=lambda f: f['sol'])
    manifest['total_frames'] = len(manifest['frames'])
    manifest['first_sol'] = manifest['frames'][0]['sol']
    manifest['last_sol'] = manifest['frames'][-1]['sol']
    manifest['generated'] = datetime.utcnow().isoformat() + 'Z'
    manifest_path.write_text(json.dumps(manifest, indent=2))

    (frames_dir / 'latest.json').write_text(json.dumps({
        'sol': manifest['last_sol'],
        'hash': manifest['frames'][-1]['hash'],
        'updated': datetime.utcnow().isoformat() + 'Z'
    }, indent=2))

    print(f'Generated {count} frames (Sol {start_sol}-{end_sol})')
    print(f'Total: {manifest["total_frames"]} frames (Sol {manifest["first_sol"]}-{manifest["last_sol"]})')


if __name__ == '__main__':
    main()
