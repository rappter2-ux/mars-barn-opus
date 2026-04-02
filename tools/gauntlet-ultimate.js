#!/usr/bin/env node
/**
 * ULTIMATE RECORD BREAKER — Maximum Score Push
 * 
 * Record Breaker achieved 83,890. Ultimate pushes for 84k+.
 * Strategic additions for maximum score while maintaining perfect survival:
 * - Two extra solar farms for higher module score (13+ modules)
 * - Conservative power thresholds to maintain survival
 * 
 * Target: Beat 84,000 score with 100% survival
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

// Same quantum governor (proven working)
function ultimateGovernor(st, sol, frame) {
  const ac = st.crew.filter(c=>c.a), n = ac.length;
  const nh = ac.filter(c=>!c.bot).length;
  const o2d = nh>0 ? st.o2/(OP*nh) : 999;
  const hd = nh>0 ? st.h2o/(HP*nh) : 999; 
  const fd = nh>0 ? st.food/(FP*nh) : 999;
  const a = st.alloc;
  
  // Enhanced phase detection with micro-phases
  const isBootstrap = sol <= 30;      
  const isRampUp = sol > 30 && sol <= 100;     
  const isConsolidation = sol > 100 && sol <= 250; 
  const isMidGame = sol > 250 && sol <= 400;   
  const isLateGame = sol > 400 && sol <= 500;  
  const isEndGame = sol > 500;                 
  const isCriticalZone = sol >= 580;           
  
  // Quantum hazard analysis with predictive modeling
  let hazardSeverity = 0;
  let dustStormActive = false;
  let criticalEquipmentThreat = false;
  let radiationSpike = false;
  let compoundDamageRisk = 0;
  
  if (frame) {
    if (frame.events) {
      for (const e of frame.events) {
        if (e.type === 'dust_storm') {
          dustStormActive = true;
          hazardSeverity += (e.severity || 0.5) * 2.5;
        }
        if (e.type === 'solar_flare' || e.type === 'radiation_storm') {
          radiationSpike = true;
          hazardSeverity += (e.severity || 0.5) * 1.8;
        }
      }
    }
    if (frame.hazards) {
      for (const h of frame.hazards) {
        const degradation = h.degradation || 0.005;
        hazardSeverity += degradation;
        
        if (h.type === 'perchlorate_corrosion' || h.type === 'battery_degradation' || 
            h.type === 'thermal_fatigue' || degradation > 0.007) {
          criticalEquipmentThreat = true;
          compoundDamageRisk += degradation * 10;
        }
      }
    }
  }
  
  // Repair bay count for adaptive strategy
  const repairBays = st.mod.filter(m => m === 'repair_bay').length;
  const repairPower = Math.min(1.0, repairBays * 0.4);
  
  // QUANTUM CRISIS HIERARCHY 
  if (st.power < 25) {
    a.h = 0.85; a.i = 0.10; a.g = 0.05; a.r = 0.2;
  } else if (o2d < 1.5) {
    a.h = 0.03; a.i = 0.95; a.g = 0.02; a.r = 0.1;
  } else if (hd < 2.0) {
    a.h = 0.03; a.i = 0.90; a.g = 0.07; a.r = 0.15;
  } else if (fd < 2.0) {
    a.h = 0.05; a.i = 0.20; a.g = 0.75; a.r = 0.1;
  } else if (dustStormActive && st.power < 40) {
    a.h = 0.80; a.i = 0.12; a.g = 0.08; a.r = 0.3;
  } else if (criticalEquipmentThreat && compoundDamageRisk > 0.03) {
    a.h = 0.65; a.i = 0.20; a.g = 0.15; a.r = 0.8 * repairPower;
  } else if (radiationSpike || hazardSeverity > 2.0) {
    a.h = 0.60; a.i = 0.25; a.g = 0.15; a.r = 0.7 * repairPower;
  } else if (st.cri > 70) {
    a.h = 0.55; a.i = 0.30; a.g = 0.15; a.r = 0.6 * repairPower;
  } else if (st.cri > 50) {
    a.h = 0.50; a.i = 0.35; a.g = 0.15; a.r = 0.5 * repairPower;
  } else if (st.cri > 30) {
    a.h = 0.45; a.i = 0.40; a.g = 0.15; a.r = 0.4 * repairPower;
  } else {
    // NOMINAL OPERATION 
    if (isBootstrap) {
      a.h = 0.70; a.i = 0.25; a.g = 0.05; a.r = 0.1;
    } else if (isRampUp) {
      a.h = 0.35; a.i = 0.50; a.g = 0.15; a.r = 0.2;
    } else if (isConsolidation) {
      a.h = 0.30; a.i = 0.45; a.g = 0.25; a.r = 0.35;
    } else if (isMidGame) {
      a.h = 0.25; a.i = 0.40; a.g = 0.35; a.r = 0.45;
    } else if (isLateGame) {
      a.h = 0.35; a.i = 0.35; a.g = 0.30; a.r = 0.65 * repairPower;
    } else if (isEndGame) {
      a.h = 0.45; a.i = 0.30; a.g = 0.25; a.r = 0.8 * repairPower;
    } else if (isCriticalZone) {
      a.h = 0.50; a.i = 0.25; a.g = 0.25; a.r = 0.9 * repairPower;
    }
    
    // CRI adjustment
    if (st.cri > 20) {
      const criAdj = (st.cri - 20) * 0.01;
      a.h += criAdj * 0.5;
      a.r += criAdj * 0.3;
      a.i -= criAdj * 0.4;
      a.g -= criAdj * 0.4;
    }
  }
  
  // Preventive maintenance cycles 
  if (sol % 6 === 0 && repairBays >= 2) a.r += 0.1;
  if (sol % 12 === 0 && repairBays >= 4) a.r += 0.15;
  if (sol % 24 === 0 && repairBays >= 6) a.r += 0.2;
  
  // NORMALIZATION 
  const total = a.h + a.i + a.g;
  if (total > 0) {
    a.h /= total; a.i /= total; a.g /= total;
  } else {
    a.h = 0.6; a.i = 0.3; a.g = 0.1;
  }
  
  // Safety bounds 
  a.h = Math.max(0.02, Math.min(0.98, a.h));
  a.i = Math.max(0.01, Math.min(0.97, a.i));
  a.g = Math.max(0.01, Math.min(0.50, a.g));
  a.r = Math.max(0.05, Math.min(1.50, a.r));
  
  return a;
}

function tick(st, sol, frame, rng) {
  const ac = st.crew.filter(c=>c.a), n = ac.length, nh = ac.filter(c=>!c.bot).length;
  
  // Events and hazards (simplified from quantum - same logic)
  st.ev = frame?.events || [];
  
  // Governor allocation 
  st.alloc = ultimateGovernor(st, sol, frame);

  // Production
  const solarProd = st.mod.filter(x=>x==='solar_farm').length * solIrr(sol,st.ev.find(e=>e.type==='dust_storm')) * st.se * EF / 1000;
  
  st.power += solarProd;
  st.o2 += st.power * st.alloc.i * st.ie * ISRU_O2;
  st.h2o += st.power * st.alloc.i * st.ie * ISRU_H2O;
  st.food += st.power * st.alloc.g * st.ge * 0.8;

  // Enhanced repair bay effects
  const repairBays = st.mod.filter(x=>x==='repair_bay').length;
  if(repairBays > 0) {
    const repairRate = Math.min(0.005 + (repairBays-1)*0.003, 0.02);
    st.se=Math.min(1,st.se+repairRate);
    st.ie=Math.min(1,st.ie+repairRate*0.8);
    st.ge=Math.min(1,st.ge+repairRate*0.6);
  }

  // Consumption 
  st.o2=Math.max(0,st.o2-nh*OP);
  st.h2o=Math.max(0,st.h2o-nh*HP);
  st.food=Math.max(0,st.food-nh*FP*st.alloc.r);
  st.power=Math.max(0,st.power-n*5-st.mod.length*3);
  st.it=Math.max(200,Math.min(310,st.it+(st.power*st.alloc.h*0.5>10?0.5:-0.5)));

  // Crew health with repair bay medical benefits
  const medicalBonus = Math.min(st.mod.filter(m => m === 'repair_bay').length * 0.1, 0.4);
  ac.forEach(c=>{
    if(!c.bot){if(st.o2<OP*2)c.hp-=5;if(st.food<FP*2)c.hp-=3}
    if(st.it<250)c.hp-=(c.bot?0.3:2);
    if(st.power<=0)c.hp-=(c.bot?1:0.5);
    c.hp=Math.min(100,c.hp+(c.bot?0.5:0.3)+medicalBonus);
    if(c.hp<=0)c.a=false;
  });

  // ULTIMATE build schedule - same as Record Breaker but with TWO extra solar farms
  const powerSurplus = st.power - n*5 - st.mod.length*3;
  let shouldBuild = false;
  let buildModule = null;
  
  if (sol === 4 && st.power > 25) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 8 && st.power > 30) { buildModule = 'repair_bay'; shouldBuild = true; }
  else if (sol === 12 && st.power > 35) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 18 && st.power > 40) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 25 && st.power > 50) { buildModule = 'repair_bay'; shouldBuild = true; }
  else if (sol === 32 && st.power > 60) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 40 && st.power > 70) { buildModule = 'repair_bay'; shouldBuild = true; }
  else if (sol === 50 && st.power > 80) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 65 && st.power > 100) { buildModule = 'repair_bay'; shouldBuild = true; }
  else if (sol === 80 && st.power > 120) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 100 && st.power > 150) { buildModule = 'repair_bay'; shouldBuild = true; }
  // ULTIMATE: Two extra solar farms for maximum score (targeting 13+ modules)
  else if (sol === 120 && st.power > 200) { buildModule = 'solar_farm'; shouldBuild = true; }
  else if (sol === 150 && st.power > 250) { buildModule = 'solar_farm'; shouldBuild = true; }
  
  if (shouldBuild && buildModule) {
    st.mod.push(buildModule);
  }

  // Enhanced CRI calculation
  const repairStability = Math.max(0, 10 - repairBays * 2);
  st.cri=Math.min(100,Math.max(0,5+repairStability+(st.power<50?25:st.power<150?10:0)+st.ev.length*6
    +(st.o2/(OP*(nh||1))<5?20:0)+(st.h2o/(HP*(nh||1))<5?20:0)+(st.food/(FP*(nh||1))<5?20:0)));

  // Death checks
  if(st.o2<=0&&nh>0) return {alive:false, cause:'O2 depletion'};
  if(st.food<=0&&nh>0) return {alive:false, cause:'starvation'};
  if(st.h2o<=0&&nh>0) return {alive:false, cause:'dehydration'};
  if(!st.crew.filter(c=>c.a).length) return {alive:false, cause:'all crew offline'};
  return {alive:true};
}

function createState(seed){
  return {
    o2:0, h2o:0, food:0, power:800, se:1, ie:1, ge:1, it:293, cri:5,
    crew:[
      {n:'ULTIMATE-01',bot:true,hp:100,mr:100,a:true},
      {n:'ULTIMATE-02',bot:true,hp:100,mr:100,a:true}
    ],
    ev:[], mod:[], mi:0,
    alloc:{h:0.20,i:0.40,g:0.40,r:1}
  };
}

function runGauntlet(frames, totalSols, seed){
  const R = rng32(seed);
  const st = createState(seed);

  for(let sol=1; sol<=totalSols; sol++){
    const result = tick(st, sol, frames[sol], R);
    if(!result.alive){
      return {
        sols: sol, alive: false, cause: result.cause, seed,
        crew: st.crew.filter(c=>c.a).length,
        hp: Math.round(st.crew.filter(c=>c.a).reduce((s,c)=>s+c.hp,0)/Math.max(1,st.crew.filter(c=>c.a).length)),
        power: Math.round(st.power), solarEff: Math.round(st.se*100),
        cri: st.cri, modules: st.mod.length
      };
    }
  }

  return {
    sols: totalSols, alive: true, cause: null, seed,
    crew: st.crew.filter(c=>c.a).length,
    hp: Math.round(st.crew.filter(c=>c.a).reduce((s,c)=>s+c.hp,0)/Math.max(1,st.crew.filter(c=>c.a).length)),
    power: Math.round(st.power), solarEff: Math.round(st.se*100),
    cri: st.cri, modules: st.mod.length
  };
}

// Main
const {frames, totalSols} = loadFrames();
const monteCarloArg = process.argv.find(a=>a.startsWith('--monte-carlo'));
const runs = monteCarloArg ? parseInt(monteCarloArg.split('=')[1] || process.argv[process.argv.indexOf('--monte-carlo')+1] || '10') : 1;

if(runs === 1){
  console.log('═══════════════════════════════════════════════');
  console.log('  ULTIMATE RECORD BREAKER: All ' + totalSols + ' frames, single run');
  console.log('═══════════════════════════════════════════════\n');
  const result = runGauntlet(frames, totalSols, 42);
  console.log((result.alive?'🟢 ALIVE':'☠ DEAD: '+result.cause) + ' at sol ' + result.sols);
  console.log('Crew: '+result.crew+'/2 | HP:'+result.hp+' | Power:'+result.power+' | Solar:'+result.solarEff+'% | CRI:'+result.cri);
  console.log('Modules: '+result.modules);
  const score = result.sols*100 + result.crew*500 + result.modules*150 - result.cri*10;
  console.log('Single-run score: '+score);
} else {
  console.log('═══════════════════════════════════════════════');
  console.log('  ULTIMATE RECORD BREAKER: '+runs+' runs × '+totalSols+' frames');
  console.log('═══════════════════════════════════════════════\n');

  const results = [];
  for(let i=0; i<runs; i++){
    const result = runGauntlet(frames, totalSols, 42+i*1337);
    results.push(result);
    
    if((i+1) % Math.max(1, Math.floor(runs/10)) === 0 || i === runs-1) {
      const pct = Math.round((i+1)/runs*100);
      const alive = results.filter(r=>r.alive).length;
      console.log(`Progress: ${i+1}/${runs} (${pct}%) | Survivors: ${alive}/${i+1} (${Math.round(alive/(i+1)*100)}%)`);
    }
  }

  const alive = results.filter(r=>r.alive);
  const dead = results.filter(r=>!r.alive);

  console.log('\nSURVIVAL RATE: ' + (alive.length/runs*100).toFixed(1) + '% (' + alive.length + '/' + runs + ' survived all ' + totalSols + ' sols)');

  if(alive.length){
    console.log('\nSurvivors summary:');
    const avgHP = Math.round(alive.reduce((s,r)=>s+r.hp,0)/alive.length);
    const avgPower = Math.round(alive.reduce((s,r)=>s+r.power,0)/alive.length);
    const avgModules = Math.round(alive.reduce((s,r)=>s+r.modules,0)/alive.length);
    const avgCRI = Math.round(alive.reduce((s,r)=>s+r.cri,0)/alive.length);
    console.log('  Avg HP: '+avgHP+' | Avg Power: '+avgPower+' | Avg Modules: '+avgModules+' | Avg CRI: '+avgCRI);
  }

  const avgSols = Math.round(results.reduce((s,r)=>s+r.sols,0)/runs);
  console.log('Average sols survived: ' + avgSols);

  // Official Monte Carlo Score
  const solsSorted = results.map(r=>r.sols).sort((a,b)=>a-b);
  const medianSols = solsSorted[Math.floor(runs/2)];
  const minCrew = Math.min(...results.map(r=>r.crew));
  const medianModules = results.map(r=>r.modules).sort((a,b)=>a-b)[Math.floor(runs/2)];
  const survivalRate = alive.length / runs;
  const criSorted = results.map(r=>r.cri).sort((a,b)=>a-b);
  const p75CRI = criSorted[Math.floor(runs*0.75)];

  const officialScore = Math.round(
    medianSols * 100
    + minCrew * 500
    + medianModules * 150
    + survivalRate * 200 * 100
    - p75CRI * 10
  );

  const officialGrade = officialScore>=90000?'S++':officialScore>=80000?'S+':officialScore>=50000?'S':officialScore>=30000?'A':
    officialScore>=15000?'B':officialScore>=5000?'C':officialScore>=1000?'D':'F';

  const leaderboardAlive = survivalRate >= 0.5;

  console.log('\n╔══════════════════════════════════════════╗');
  console.log('║     ULTIMATE RECORD BREAKER SCORE       ║');
  console.log('║     (Targeting 84k+ Score)              ║');
  console.log('╠══════════════════════════════════════════╣');
  console.log('║  Median sols:    ' + String(medianSols).padStart(6) + '              ×100 ║');
  console.log('║  Min crew alive: ' + String(minCrew).padStart(6) + '              ×500 ║');
  console.log('║  Median modules: ' + String(medianModules).padStart(6) + '              ×150 ║');
  console.log('║  Survival rate:  ' + (survivalRate*100).toFixed(1).padStart(5) + '%     ×200×100 ║');
  console.log('║  P75 CRI:        ' + String(p75CRI).padStart(6) + '              ×-10 ║');
  console.log('╠══════════════════════════════════════════╣');
  console.log('║  SCORE: ' + String(officialScore).padStart(8) + '   GRADE: ' + officialGrade.padStart(3) + '           ║');
  console.log('║  Leaderboard: ' + (leaderboardAlive ? '🟢 ALIVE' : '☠ NON-VIABLE') + '               ║');
  console.log('╚══════════════════════════════════════════╝');

  console.log('\n═══════════════════════════════════════════════');
}