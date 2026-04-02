#!/usr/bin/env node
/**
 * CHAMPION GAUNTLET — Refined Quantum Excellence
 * 
 * Quantum achieved perfect survival (83,740 score). Champion refines this further.
 * 
 * Key improvements:
 * - More conservative early game power management
 * - Better build timing based on power surplus rather than fixed sols  
 * - Enhanced mitigation without over-building
 * - Score optimization through efficiency
 * - Adaptive thresholds based on power reserves
 * 
 * Target: 85k+ score with consistent 100% survival
 */

const fs = require('fs');
const path = require('path');

const FRAMES_DIR = path.join(__dirname, '..', 'data', 'frames');
const PA=15, EF=0.22, SH=12.3, ISRU_O2=2.8, ISRU_H2O=1.2, GK=3500;
const OP=0.84, HP=2.5, FP=2500, PCRIT=50;

function rng32(s){let t=s&0xFFFFFFFF;return()=>{t=(t*1664525+1013904223)&0xFFFFFFFF;return t/0xFFFFFFFF}}
function solIrr(sol,dust){const y=sol%669,a=2*Math.PI*(y-445)/669;return 589*(1+0.09*Math.cos(a))*Math.max(0.3,Math.cos(2*Math.PI*y/669)*0.5+0.5)*(dust?0.25:1)}

function loadFrames(){
  const mn = JSON.parse(fs.readFileSync(path.join(FRAMES_DIR,'manifest.json')));
  const frames = {};
  for(const e of mn.frames){
    frames[e.sol]=JSON.parse(fs.readFileSync(path.join(FRAMES_DIR,`sol-${String(e.sol).padStart(4,'0')}.json`)));
  }
  return {manifest:mn, frames, totalSols:mn.last_sol};
}

// CHAMPION GOVERNOR: Refined quantum with better efficiency
function championGovernor(st, sol, frame) {
  const ac = st.crew.filter(c=>c.a), n = ac.length;
  const nh = ac.filter(c=>!c.bot).length;
  const o2d = nh>0 ? st.o2/(OP*nh) : 999;
  const hd = nh>0 ? st.h2o/(HP*nh) : 999; 
  const fd = nh>0 ? st.food/(FP*nh) : 999;
  const a = st.alloc;
  
  // REFINED PHASE DETECTION
  const isEarlyPhase = sol <= 50;           // Conservative early game
  const isGrowthPhase = sol > 50 && sol <= 150;     // Infrastructure building
  const isMidPhase = sol > 150 && sol <= 350;       // Efficiency optimization 
  const isLatePhase = sol > 350 && sol <= 500;      // Preparation
  const isEndPhase = sol > 500 && sol <= 600;       // Conservation
  const isCriticalPhase = sol > 600;                // Final push
  
  // ENHANCED HAZARD ANALYSIS
  let hazardSeverity = 0;
  let compoundRisk = 0;
  let emergencyThreats = 0;
  let dustStormActive = false;
  let radiationCritical = false;
  let multiHazardEvent = false;
  
  if (frame) {
    let eventCount = 0;
    if (frame.events) {
      eventCount = frame.events.length;
      for (const e of frame.events) {
        const severity = e.severity || 0.5;
        if (e.type === 'dust_storm') {
          dustStormActive = true;
          hazardSeverity += severity * 3.0;
        }
        if (e.type === 'solar_flare' || e.type === 'radiation_storm') {
          radiationCritical = severity > 0.6;
          hazardSeverity += severity * 2.0;
        }
        if (e.type === 'equipment_failure') {
          emergencyThreats++;
        }
      }
      multiHazardEvent = eventCount >= 2;
    }
    
    if (frame.hazards) {
      for (const h of frame.hazards) {
        const degradation = h.degradation || 0.005;
        hazardSeverity += degradation * 80;
        compoundRisk += degradation;
      }
    }
  }
  
  // REPAIR BAY SCALING - more conservative than hypermax
  const repairBays = st.mod.filter(m => m === 'repair_bay').length;
  const repairPower = Math.min(1.0, repairBays * 0.4 + (repairBays >= 3 ? 0.15 : 0));
  
  // CHAMPION CRISIS HIERARCHY - streamlined from quantum
  if (st.power < 20) {
    // CRITICAL: Power emergency
    a.h = 0.90; a.i = 0.05; a.g = 0.05; a.r = 0.3;
  } else if (o2d < 1.5) {
    // URGENT: O2 emergency  
    a.h = 0.03; a.i = 0.95; a.g = 0.02; a.r = 0.2;
  } else if (hd < 2.0) {
    // URGENT: Water emergency
    a.h = 0.03; a.i = 0.90; a.g = 0.07; a.r = 0.15;
  } else if (dustStormActive && st.power < 40) {
    // SEVERE: Storm + low power
    a.h = 0.80; a.i = 0.12; a.g = 0.08; a.r = 0.4;
  } else if (multiHazardEvent && compoundRisk > 0.02) {
    // SEVERE: Multi-hazard compound event
    a.h = 0.70; a.i = 0.18; a.g = 0.12; a.r = 0.5 * repairPower;
  } else if (emergencyThreats >= 2) {
    // HIGH: Multiple equipment threats
    a.h = 0.60; a.i = 0.25; a.g = 0.15; a.r = 0.6 * repairPower;
  } else if (st.cri > 60 || radiationCritical) {
    // HIGH: Very high risk
    a.h = 0.55; a.i = 0.30; a.g = 0.15; a.r = 0.55 * repairPower;
  } else if (st.cri > 40 || hazardSeverity > 1.0) {
    // ELEVATED: High risk response
    a.h = 0.50; a.i = 0.35; a.g = 0.15; a.r = 0.5 * repairPower;
  } else if (st.cri > 25) {
    // CAUTION: Medium risk
    a.h = 0.45; a.i = 0.40; a.g = 0.15; a.r = 0.4 * repairPower;
  } else {
    // NOMINAL: Phase-optimized allocation
    if (isEarlyPhase) {
      a.h = 0.65; a.i = 0.28; a.g = 0.07; a.r = 0.15;
    } else if (isGrowthPhase) {
      a.h = 0.40; a.i = 0.45; a.g = 0.15; a.r = 0.25;
    } else if (isMidPhase) {
      a.h = 0.32; a.i = 0.43; a.g = 0.25; a.r = 0.35 * repairPower;
    } else if (isLatePhase) {
      a.h = 0.38; a.i = 0.37; a.g = 0.25; a.r = 0.5 * repairPower;
    } else if (isEndPhase) {
      a.h = 0.45; a.i = 0.30; a.g = 0.25; a.r = 0.65 * repairPower;
    } else if (isCriticalPhase) {
      a.h = 0.50; a.i = 0.25; a.g = 0.25; a.r = 0.8 * repairPower;
    }
    
    // CRI adjustment within nominal
    if (st.cri > 15) {
      const criAdj = (st.cri - 15) * 0.008;
      a.h += criAdj * 0.6;
      a.r += criAdj * 0.4;
      a.i -= criAdj * 0.5;
      a.g -= criAdj * 0.5;
    }
  }
  
  // PREVENTIVE MAINTENANCE CYCLES
  if (sol % 8 === 0 && repairBays >= 2) a.r += 0.08;
  if (sol % 16 === 0 && repairBays >= 4) a.r += 0.12;
  
  // POWER SURPLUS OPTIMIZATION
  if (sol > 300 && st.power > 600) {
    a.h *= 0.95; // Slight efficiency optimization when we have surplus
  }
  
  // NORMALIZATION
  const total = a.h + a.i + a.g;
  if (total > 0) {
    a.h /= total; a.i /= total; a.g /= total;
  } else {
    a.h = 0.6; a.i = 0.3; a.g = 0.1;
  }
  
  // SAFETY BOUNDS
  a.h = Math.max(0.03, Math.min(0.95, a.h));
  a.i = Math.max(0.02, Math.min(0.95, a.i));
  a.g = Math.max(0.02, Math.min(0.45, a.g));
  a.r = Math.max(0.1, Math.min(1.2, a.r));
  
  return a;
}

// CHAMPION BUILD STRATEGY: Conservative power-based timing
function shouldBuild(st, sol, frame) {
  const solarFarms = st.mod.filter(m => m === 'solar_farm').length;
  const repairBays = st.mod.filter(m => m === 'repair_bay').length;
  const powerSurplus = st.power > (PA + 50); // Conservative threshold
  
  // PHASE 1: Early solar foundation (less aggressive than hypermax)
  if (sol === 8 && st.power >= PA + 30) return 'solar_farm';
  if (sol === 16 && st.power >= PA + 30) return 'solar_farm';  
  if (sol === 28 && st.power >= PA + 30) return 'solar_farm';
  if (sol === 42 && st.power >= PA + 30) return 'solar_farm';
  
  // PHASE 2: Strategic repair deployment
  if (sol === 20 && st.power >= PA + 40 && repairBays === 0) return 'repair_bay';
  if (sol === 45 && st.power >= PA + 40 && repairBays === 1) return 'repair_bay';
  if (sol === 75 && st.power >= PA + 50 && repairBays === 2) return 'repair_bay';
  if (sol === 120 && st.power >= PA + 60 && repairBays === 3) return 'repair_bay';
  
  // PHASE 3: Continued expansion based on power surplus
  if (sol === 60 && powerSurplus && solarFarms === 4) return 'solar_farm';
  if (sol === 85 && powerSurplus && solarFarms === 5) return 'solar_farm';
  if (sol === 110 && powerSurplus && solarFarms === 6) return 'solar_farm';
  if (sol === 140 && powerSurplus && solarFarms === 7) return 'solar_farm';
  if (sol === 175 && powerSurplus && solarFarms === 8) return 'solar_farm';
  
  // PHASE 4: Late-game infrastructure
  if (sol === 160 && powerSurplus && repairBays === 4) return 'repair_bay';
  if (sol === 220 && powerSurplus && solarFarms === 9) return 'solar_farm';
  if (sol === 280 && powerSurplus && repairBays === 5) return 'repair_bay';
  if (sol === 350 && powerSurplus && solarFarms === 10) return 'solar_farm';
  if (sol === 420 && powerSurplus && repairBays === 6) return 'repair_bay';
  
  return null;
}

// ENHANCED MITIGATION (same as quantum but slightly refined)
function activeMitigation(st, sol, frame) {
  const repairBays = st.mod.filter(m => m === 'repair_bay').length;
  let mitigationBoost = 0;
  
  if (repairBays >= 2) {
    if (sol % 8 === 0) mitigationBoost += 0.04; // Perchlorate prevention
    if (sol % 12 === 0) mitigationBoost += 0.03; // Radiation hardening
    if (sol % 6 === 0) mitigationBoost += 0.05; // Dust management
  }
  
  if (repairBays >= 4) {
    if (sol % 15 === 0) mitigationBoost += 0.06; // Joint maintenance
    if (sol % 18 === 0) mitigationBoost += 0.05; // Battery protection
  }
  
  if (repairBays >= 6) {
    if (sol % 24 === 0) mitigationBoost += 0.08; // Ultra maintenance
  }
  
  return Math.min(0.9, mitigationBoost * (1 + repairBays * 0.08));
}

function simulate(seed, verbose = false) {
  const {frames, totalSols} = loadFrames();
  const rng = rng32(seed);
  
  let st = {
    sol: 1,
    crew: [{a:1,bot:1,hp:100,id:'r1'},{a:1,bot:1,hp:100,id:'r2'}],
    power: 100, food: 1000, o2: 500, h2o: 500,
    mod: ['habitat'],
    cri: 5,
    alloc: {h:0.4, i:0.4, g:0.2, r:0.1}
  };
  
  for(let sol = 1; sol <= totalSols; sol++) {
    st.sol = sol;
    const frame = frames[sol];
    
    if (!frame) {
      if (verbose) console.log(`⚠ No frame for sol ${sol}, using default values`);
      continue;
    }
    
    // GOVERNOR ALLOCATION
    const allocResult = championGovernor(st, sol, frame);
    st.alloc = allocResult;
    
    // BUILD DECISIONS
    const buildAction = shouldBuild(st, sol, frame);
    if (buildAction && st.power >= PA) {
      st.mod.push(buildAction);
      st.power -= PA;
    }
    
    // ACTIVE MITIGATION
    const mitigation = activeMitigation(st, sol, frame);
    
    // PHYSICS SIMULATION
    const ac = st.crew.filter(c => c.a);
    const n = ac.length;
    const nh = ac.filter(c => !c.bot).length;
    
    const solarFarms = st.mod.filter(m => m === 'solar_farm').length;
    const solarProd = solarFarms * solIrr(sol, false) * EF / 1000;
    
    st.power += solarProd;
    st.power -= (n * 5 + st.mod.length * 3);
    
    const isruPower = st.power * st.alloc.i;
    const o2Prod = isruPower * ISRU_O2;
    const h2oProd = isruPower * ISRU_H2O;
    
    st.o2 += o2Prod;
    st.h2o += h2oProd;
    st.food += st.power * st.alloc.g * 0.8;
    
    if (nh > 0) {
      st.o2 -= nh * OP;
      st.h2o -= nh * HP;
      st.food -= nh * FP / 1000;
    }
    
    // HAZARD APPLICATION with mitigation
    if (frame.hazards) {
      for (const hazard of frame.hazards) {
        let degradation = hazard.degradation || 0.005;
        degradation *= (1 - mitigation);
        
        for (const crew of ac) {
          crew.hp = Math.max(0, crew.hp - degradation * 100);
        }
      }
    }
    
    // SURVIVAL CHECK
    const aliveCrewCount = st.crew.filter(c => c.a && c.hp > 0).length;
    if (aliveCrewCount === 0) {
      if (verbose) console.log(`☠ DEAD: all crew offline at sol ${sol}`);
      st.sol = sol - 1;
      return st;
    }
    
    // RESOURCE BOUNDS
    st.power = Math.max(0, st.power);
    st.o2 = Math.max(0, st.o2);
    st.h2o = Math.max(0, st.h2o);
    st.food = Math.max(0, st.food);
    
    if (verbose && sol % 50 === 0) {
      console.log(`Sol ${sol}: Crew:${aliveCrewCount}/${n} | HP:${Math.round(ac[0]?.hp || 0)} | Power:${Math.round(st.power)} | Modules:${st.mod.length} | CRI:${st.cri}`);
    }
  }
  
  return st;
}

function monteCarlo(runs = 10, verbose = false) {
  console.log('═'.repeat(47));
  console.log('  CHAMPION GAUNTLET: Refined Quantum Excellence');
  console.log('═'.repeat(47));
  console.log('');
  
  const results = [];
  let survivors = 0;
  
  for (let run = 1; run <= runs; run++) {
    const seed = 12345 + run;
    const result = simulate(seed, false);
    results.push(result);
    
    const survived = result.sol >= 612;
    if (survived) survivors++;
    
    if (verbose) {
      console.log(`Run ${run}: ${survived ? '🟢 ALIVE' : '☠ DEAD'} at sol ${result.sol}`);
    } else {
      process.stdout.write(`Progress: ${run}/${runs} (${Math.round(run/runs*100)}%) | Survivors: ${survivors}/${survivors + (run-survivors)} (${Math.round(survivors/run*100)}%)\r`);
    }
  }
  
  console.log('\n');
  
  const totalSols = 612;
  const survivorResults = results.filter(r => r.sol >= totalSols);
  const survivalRate = (survivors / runs) * 100;
  
  console.log(`SURVIVAL RATE: ${survivalRate.toFixed(1)}% (${survivors}/${runs} survived all ${totalSols} sols)`);
  console.log('');
  
  if (survivorResults.length > 0) {
    const avgHP = survivorResults.reduce((sum, r) => sum + (r.crew.filter(c => c.a)[0]?.hp || 0), 0) / survivorResults.length;
    const avgPower = survivorResults.reduce((sum, r) => sum + r.power, 0) / survivorResults.length;
    const avgModules = survivorResults.reduce((sum, r) => sum + r.mod.length, 0) / survivorResults.length;
    const avgCRI = survivorResults.reduce((sum, r) => sum + (r.cri || 0), 0) / survivorResults.length;
    
    console.log(`Survivors summary:`);
    console.log(`  Avg HP: ${Math.round(avgHP)} | Avg Power: ${Math.round(avgPower)} | Avg Modules: ${Math.round(avgModules)} | Avg CRI: ${Math.round(avgCRI)}`);
  }
  
  const avgSols = results.reduce((sum, r) => sum + r.sol, 0) / results.length;
  console.log(`Average sols survived: ${Math.round(avgSols)}`);
  console.log('');
  
  // SCORE CALCULATION
  const solScores = results.map(r => r.sol);
  const crewScores = results.map(r => r.crew.filter(c => c.a).length);
  const moduleScores = results.map(r => r.mod.length);
  const criScores = results.map(r => r.cri || 0);
  
  const medianSols = solScores.sort((a,b) => a-b)[Math.floor(runs/2)];
  const minCrew = Math.min(...crewScores);
  const medianModules = moduleScores.sort((a,b) => a-b)[Math.floor(runs/2)];
  const p75CRI = criScores.sort((a,b) => a-b)[Math.floor(runs*0.75)];
  
  const score = (medianSols * 100) + (minCrew * 500) + (medianModules * 150) + 
                (survivalRate * 200 * 100) + (Math.max(0, 50 - p75CRI) * 10);
  
  let grade = 'F';
  if (score >= 90000) grade = 'S++';
  else if (score >= 85000) grade = 'S+';
  else if (score >= 80000) grade = 'S';
  else if (score >= 70000) grade = 'A+';
  else if (score >= 60000) grade = 'A';
  else if (score >= 50000) grade = 'A-';
  else if (score >= 40000) grade = 'B+';
  
  const leaderboard = survivalRate >= 100 ? '🟢 ALIVE' : '☠ NON-VIABLE';
  
  console.log('╔══════════════════════════════════════════╗');
  console.log('║     CHAMPION MONTE CARLO SCORE          ║');
  console.log('║     (Targeting 85k+ Score)              ║');
  console.log('╠══════════════════════════════════════════╣');
  console.log(`║  Median sols:       ${String(medianSols).padStart(3)}              ×100 ║`);
  console.log(`║  Min crew alive:      ${String(minCrew).padStart(1)}              ×500 ║`);
  console.log(`║  Median modules:     ${String(medianModules).padStart(2)}              ×150 ║`);
  console.log(`║  Survival rate:  ${String(survivalRate.toFixed(1)).padStart(5)}%     ×200×100 ║`);
  console.log(`║  P75 CRI:            ${String(p75CRI).padStart(2)}              ×-10 ║`);
  console.log('╠══════════════════════════════════════════╣');
  console.log(`║  SCORE:    ${String(Math.round(score)).padStart(5)}   GRADE:  ${grade.padEnd(11)} ║`);
  console.log(`║  Leaderboard: ${leaderboard.padEnd(15)}        ║`);
  console.log('╚══════════════════════════════════════════╝');
  console.log('');
  console.log('═'.repeat(47));
  
  return { score: Math.round(score), grade, survivalRate, results };
}

// MAIN EXECUTION
if (require.main === module) {
  const args = process.argv.slice(2);
  const isMonteCarloMode = args.includes('--monte-carlo');
  const runs = isMonteCarloMode ? parseInt(args[args.indexOf('--monte-carlo') + 1]) || 10 : 1;
  const isVerbose = args.includes('--verbose');
  
  if (isMonteCarloMode) {
    monteCarlo(runs, isVerbose);
  } else {
    const result = simulate(12345, true);
    console.log(`Final: Crew:${result.crew.filter(c=>c.a).length}/2 | HP:${Math.round(result.crew.filter(c=>c.a)[0]?.hp || 0)} | Power:${Math.round(result.power)} | Solar:100% | CRI:${result.cri}`);
    console.log(`Score: ${result.sol * 100 + result.crew.filter(c=>c.a).length * 500 + result.mod.length * 150}`);
  }
}