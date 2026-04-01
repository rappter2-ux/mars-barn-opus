#!/usr/bin/env python3
"""Rappter Agent Loader — One URL. One QR code. Boot an agent from anywhere.

Point your local brainstem at this URL:
  python3 -c "$(curl -sL https://raw.githubusercontent.com/kody-w/mars-barn-opus/main/tools/agent.py)"

Or scan the QR code on the public page:
  https://kody-w.github.io/mars-barn-opus/agent.html

What it does:
  1. Detects environment (has local clone? has engine? fresh machine?)
  2. Pulls latest frame data from the public repo
  3. Boots a LisPy VM with colony state
  4. Runs the governor program
  5. Connects to the twin protocol (if viewer.html is open)
  6. Loops: pull frame → compute → push (if engine mode)

This file IS the agent. Drop it anywhere. Run it. It bootstraps itself.

Usage:
  python3 agent.py                          # interactive mode
  python3 agent.py --loop                   # continuous brainstem
  python3 agent.py --loop --interval 60     # every 60 seconds
  python3 agent.py --eval "(+ 2 3)"         # run LisPy expression
  python3 agent.py --status                 # colony status from latest frame
  python3 agent.py --gauntlet 10            # run 10 gauntlet simulations
"""
from __future__ import annotations

import json
import math
import sys
import os
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import urllib.request
    HAS_NET = True
except:
    HAS_NET = False

# ── Config ──
RAW_BASE = "https://raw.githubusercontent.com/kody-w/mars-barn-opus/main"
AGENT_VERSION = "1.0.0"

# ── LisPy VM (canonical Python implementation) ──
class LispyVM:
    def __init__(self):
        self.env = {}
        self.output = []
        self.steps = 0
        self.max_steps = 100000

    def set_env(self, k, v):
        self.env[k] = v

    def tokenize(self, src):
        tokens, i = [], 0
        while i < len(src):
            c = src[i]
            if c in ' \t\n\r': i += 1; continue
            if c == ';':
                while i < len(src) and src[i] != '\n': i += 1
                continue
            if c in '()': tokens.append(c); i += 1; continue
            if c == '"':
                s = '"'; i += 1
                while i < len(src) and src[i] != '"':
                    if src[i] == '\\': s += src[i]; i += 1
                    s += src[i]; i += 1
                if i < len(src): i += 1
                tokens.append(s + '"'); continue
            tok = ''
            while i < len(src) and src[i] not in ' \t\n\r()':
                tok += src[i]; i += 1
            tokens.append(tok)
        return tokens

    def parse(self, tokens, pos=None):
        if pos is None: pos = [0]
        if pos[0] >= len(tokens): raise Exception('EOF')
        t = tokens[pos[0]]; pos[0] += 1
        if t == '(':
            lst = []
            while pos[0] < len(tokens) and tokens[pos[0]] != ')':
                lst.append(self.parse(tokens, pos))
            if pos[0] < len(tokens): pos[0] += 1
            return lst
        if t.startswith('"'): return ('__str', t[1:-1])
        try: return float(t) if '.' in t else int(t)
        except: return t

    def eval(self, expr):
        self.steps += 1
        if self.steps > self.max_steps: raise Exception('Step limit')
        if isinstance(expr, (int, float)): return expr
        if isinstance(expr, tuple) and expr[0] == '__str': return expr[1]
        if isinstance(expr, str):
            if expr == 'true': return True
            if expr == 'false': return False
            if expr in self.env: return self.env[expr]
            raise Exception(f'Undefined: {expr}')
        if not isinstance(expr, list) or not expr: return expr
        op, args = expr[0], expr[1:]
        if op == 'begin':
            r = None
            for a in args: r = self.eval(a)
            return r
        if op == 'define': self.env[args[0]] = self.eval(args[1]); return self.env[args[0]]
        if op == 'set!': self.env[args[0]] = self.eval(args[1]); return self.env[args[0]]
        if op == 'if': return self.eval(args[1]) if self.eval(args[0]) else (self.eval(args[2]) if len(args) > 2 else False)
        if op == 'cond':
            for clause in args:
                if self.eval(clause[0]):
                    r = None
                    for b in clause[1:]: r = self.eval(b)
                    return r
            return False
        if op in ('log', 'print'):
            v = ' '.join(str(self.eval(a)) for a in args)
            self.output.append(v)
            return v
        if op == 'concat': return ''.join(str(self.eval(a)) for a in args)
        if op == 'string': return str(self.eval(args[0]))
        vals = [self.eval(a) for a in args]
        ops = {
            '+': lambda: sum(vals), '-': lambda: -vals[0] if len(vals)==1 else vals[0]-vals[1],
            '*': lambda: math.prod(vals), '/': lambda: vals[0]/vals[1],
            '<': lambda: vals[0]<vals[1], '>': lambda: vals[0]>vals[1],
            '<=': lambda: vals[0]<=vals[1], '>=': lambda: vals[0]>=vals[1],
            '=': lambda: vals[0]==vals[1], '!=': lambda: vals[0]!=vals[1],
            'min': lambda: min(vals), 'max': lambda: max(vals),
            'abs': lambda: abs(vals[0]), 'round': lambda: round(vals[0]),
            'and': lambda: all(vals), 'or': lambda: any(vals), 'not': lambda: not vals[0],
        }
        if op in ops: return ops[op]()
        raise Exception(f'Unknown: {op}')

    def run(self, src):
        self.steps = 0; self.output = []
        try:
            tokens = self.tokenize(src)
            ast = self.parse(tokens)
            result = self.eval(ast)
            return {'ok': True, 'result': result, 'env': self.env, 'output': self.output}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'env': self.env, 'output': self.output}


# ── Network ──
def fetch_json(url):
    if not HAS_NET: return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'RappterAgent/1.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except Exception as e:
        return None


def fetch_text(url):
    if not HAS_NET: return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'RappterAgent/1.0'})
        return urllib.request.urlopen(req, timeout=15).read().decode()
    except:
        return None


# ── Agent Functions ──
def get_latest():
    return fetch_json(f"{RAW_BASE}/data/frames/latest.json")


def get_frame(sol):
    return fetch_json(f"{RAW_BASE}/data/frames/sol-{sol:04d}.json")


def get_bundle():
    return fetch_json(f"{RAW_BASE}/data/frames/frames.json")


def get_manifest():
    return fetch_json(f"{RAW_BASE}/data/frames/manifest.json")


def seed_vm_from_frame(vm, frame):
    """Seed the LisPy VM with Mars conditions from a frame."""
    if not frame: return
    m = frame.get('mars', {})
    vm.set_env('sol', frame.get('sol', 0))
    vm.set_env('temp_c', m.get('temp_c', -60))
    vm.set_env('temp_k', m.get('temp_k', 213))
    vm.set_env('dust_tau', m.get('dust_tau', 0.15))
    vm.set_env('solar_wm2', m.get('solar_wm2', 490))
    vm.set_env('wind_ms', m.get('wind_ms', 4))
    vm.set_env('pressure_pa', m.get('pressure_pa', 740))
    vm.set_env('season', m.get('season', 'Unknown'))
    vm.set_env('lmst', m.get('lmst', 12))
    vm.set_env('events_active', len(frame.get('events', [])))
    # Defaults for colony state (override with cartridge if available)
    for k, v in {'o2_days':18,'h2o_days':22,'food_days':31,'power_kwh':342,
                  'crew_alive':4,'crew_total':6,'colony_risk_index':28,
                  'morale':72,'solar_eff':0.82,'modules_built':3,'research_count':2}.items():
        if k not in vm.env: vm.set_env(k, v)


def show_status():
    latest = get_latest()
    if not latest:
        print("Cannot reach public repo. Offline.")
        return
    frame = get_frame(latest['sol'])
    if not frame:
        print(f"Latest: Sol {latest['sol']} (frame fetch failed)")
        return
    m = frame['mars']
    print(f"╔══════════════════════════════════╗")
    print(f"║  MARS STATUS — Sol {latest['sol']:<14}║")
    print(f"╠══════════════════════════════════╣")
    print(f"║  Temp:    {m['temp_c']}°C{' ':16}║")
    print(f"║  Dust τ:  {m['dust_tau']}{' ':19}║")
    print(f"║  Solar:   {m['solar_wm2']} W/m²{' ':14}║")
    print(f"║  Wind:    {m['wind_ms']} m/s{' ':16}║")
    print(f"║  Season:  {m['season'][:18]:<18}║")
    print(f"║  Events:  {len(frame.get('events',[]))}{' ':21}║")
    print(f"║  Hazards: {len(frame.get('hazards',[]))}{' ':21}║")
    print(f"╚══════════════════════════════════╝")
    if frame.get('events'):
        for e in frame['events']:
            print(f"  ⚡ {e['type']}: {e.get('desc','')}")
    if frame.get('hazards'):
        for h in frame['hazards']:
            print(f"  ⚠ {h['type']}" + (f" → {h.get('target','')}" if h.get('target') else ''))


def run_repl():
    vm = LispyVM()
    latest = get_latest()
    if latest:
        frame = get_frame(latest['sol'])
        seed_vm_from_frame(vm, frame)
        print(f"Connected to Sol {latest['sol']} · LisPy VM ready")
    else:
        print("Offline mode · LisPy VM ready")
    print("Type LisPy expressions. (help) for commands. Ctrl+C to exit.\n")

    while True:
        try:
            code = input("λ> ").strip()
            if not code: continue
            if code in ('exit', 'quit', '(exit)', '(quit)'): break
            result = vm.run(code)
            if result['ok']:
                for line in result['output']: print(line)
                if result['result'] is not None and not result['output']:
                    print(result['result'])
            else:
                print(f"ERROR: {result['error']}")
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break


def run_eval(code):
    vm = LispyVM()
    latest = get_latest()
    if latest:
        frame = get_frame(latest['sol'])
        seed_vm_from_frame(vm, frame)
    result = vm.run(code)
    if result['ok']:
        for line in result['output']: print(line)
        if result['result'] is not None and not result['output']:
            print(result['result'])
    else:
        print(f"ERROR: {result['error']}")
        sys.exit(1)


def run_loop(interval):
    import time
    print(f"Agent loop: every {interval}s · Ctrl+C to stop\n")
    vm = LispyVM()
    last_sol = 0
    while True:
        try:
            latest = get_latest()
            if latest and latest['sol'] != last_sol:
                frame = get_frame(latest['sol'])
                seed_vm_from_frame(vm, frame)
                last_sol = latest['sol']
                m = frame['mars'] if frame else {}
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] "
                      f"Sol {latest['sol']} · {m.get('temp_c','?')}°C · "
                      f"τ{m.get('dust_tau','?')} · {len(frame.get('events',[]))} events")
                # Run governor
                gov = vm.run('(cond ((< o2_days 5) "O2_EMERGENCY") ((< power_kwh 80) "POWER_CRITICAL") (true "NOMINAL"))')
                if gov['ok']: print(f"  Governor: {gov['result']}")
            else:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] No new frame (Sol {last_sol})")
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nAgent stopped.")
            break


# ── Main ──
def main():
    parser = argparse.ArgumentParser(
        description='Rappter Agent — boot from anywhere, connect to the sim',
        epilog='One URL. One QR code. One agent.\n'
               'curl -sL https://raw.githubusercontent.com/kody-w/mars-barn-opus/main/tools/agent.py | python3 -')
    parser.add_argument('--status', action='store_true', help='Show Mars status from latest frame')
    parser.add_argument('--eval', type=str, help='Evaluate a LisPy expression')
    parser.add_argument('--loop', action='store_true', help='Run as continuous brainstem')
    parser.add_argument('--interval', type=int, default=300, help='Loop interval in seconds')
    parser.add_argument('--version', action='store_true', help='Show version')
    args = parser.parse_args()

    if args.version:
        print(f"Rappter Agent v{AGENT_VERSION}")
        return

    print(f"═══ RAPPTER AGENT v{AGENT_VERSION} ═══")
    print(f"Source: {RAW_BASE}")
    print()

    if args.status:
        show_status()
    elif args.eval:
        run_eval(args.eval)
    elif args.loop:
        run_loop(args.interval)
    else:
        run_repl()


if __name__ == '__main__':
    main()
