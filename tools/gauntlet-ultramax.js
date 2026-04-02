#!/usr/bin/env node
/**
 * ULTRA-MAX GAUNTLET — Maximum infrastructure strategy
 * 
 * Strategy: Ultra-aggressive early build + maximum repair bay deployment 
 * Goals: Push beyond 465 sols through overwhelming infrastructure
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const FRAMES_DIR = path.join(__dirname, '..', 'data', 'frames');
const VERSIONS_PATH = path.join(__dirname, '..', 'data', 'frame-versions', 'versions.json');
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

// Ultra-max tick with overwhelming infrastructure
function tick(st, sol, frame, R){
  const ac=st.crew.filter(c=>c.a), n=ac.length;
  const nh=ac.filter(c=>!c.bot).length;
  if(!n) return {alive:false, cause:'no crew'};

  // Apply frame data
  if(frame){
    if(frame.events) for(const e of frame.events)
      if(!st.ev.some(x=>x.t===e.type)) st.ev.push({t:e.type,sv:e.severity||0.5,r:e.duration_sols||3});
    if(frame.hazards) for(const h of frame.hazards){
      if(h.type==='equipment_fatigue'&&h.target==='solar_array') st.se=Math.max(0.1,st.se-(h.degradation||0.005));
      if(h.type==='dust_accumulation') st.se=Math.max(0.1,st.se-(h.degradation||0.01));
      if(h.type==='perchlorate_corrosion') st.ie=Math.max(0.3,st.ie-(h.degradation||0.005));
      if(h.type==='regolith_abrasion') st.se=Math.max(0.3,st.se-(h.degradation||0.003));
      if(h.type==='electrostatic_dust') st.se=Math.max(0.3,st.se-(h.degradation||0.002));
      if(h.type==='thermal_fatigue') st.power=Math.max(0,st.power-5);
      if(h.type==='radiation_seu'){const alive2=st.crew.filter(c=>c.a&&c.hp>0);if(alive2.length)alive2[0].hp-=3}
      if(h.type==='battery_degradation') st.power*=0.98;
    }
  }
  st.ev=st.ev.filter(e=>{e.r--;return e.r>0});

  if(R()<0.012*(1+st.cri/80)){st.ie*=(1-0.02);st.power=Math.max(0,st.power-2)}

  // ULTRA-SENSITIVE CRI GOVERNOR
  const o2d=nh>0?st.o2/(OP*nh):999, hd=nh>0?st.h2o/(HP*nh):999, fd=nh>0?st.food/(FP*nh):999;
  const a=st.alloc;
  
  if(st.power<20)       {a.h=0.85;a.i=0.10;a.g=0.05;a.r=0.2}
  else if(o2d<2.5)      {a.h=0.04;a.i=0.92;a.g=0.04;a.r=0.2}
  else if(hd<3.5)       {a.h=0.06;a.i=0.88;a.g=0.06;a.r=0.3}
  else if(fd<6)         {a.h=0.08;a.i=0.18;a.g=0.74;a.r=0.5}
  else {
    const emergencyPhase = sol > 420;
    const endGamePhase = sol > 380;
    const criticalPhase = sol > 320;
    const extremeRisk = st.cri > 65;
    const ultraRisk = st.cri > 50;
    const highRisk = st.cri > 35;
    const mediumRisk = st.cri > 15;
    
    if(emergencyPhase && extremeRisk) {
      a.h=0.80; a.i=0.15; a.g=0.05; a.r=3.5;
    } else if(endGamePhase && extremeRisk) {
      a.h=0.75; a.i=0.20; a.g=0.05; a.r=3.2;
    } else if(endGamePhase && ultraRisk) {
      a.h=0.70; a.i=0.25; a.g=0.05; a.r=3.0;
    } else if(criticalPhase && extremeRisk) {
      a.h=0.65; a.i=0.25; a.g=0.10; a.r=2.8;
    } else if(criticalPhase && ultraRisk) {
      a.h=0.60; a.i=0.30; a.g=0.10; a.r=2.6;
    } else if(criticalPhase && highRisk) {
      a.h=0.55; a.i=0.35; a.g=0.10; a.r=2.4;
    } else if(criticalPhase && mediumRisk) {
      a.h=0.45; a.i=0.40; a.g=0.15; a.r=2.2;
    } else if(criticalPhase) {
      a.h=0.35; a.i=0.45; a.g=0.20; a.r=2.0;
    } else if(extremeRisk) {
      a.h=0.60; a.i=0.25; a.g=0.15; a.r=2.0;
    } else if(ultraRisk) {
      a.h=0.50; a.i=0.35; a.g=0.15; a.r=1.8;
    } else if(highRisk) {
      a.h=0.35; a.i=0.45; a.g=0.20; a.r=1.6;
    } else if(mediumRisk) {
      a.h=0.20; a.i=0.45; a.g=0.35; a.r=1.4;
    } else {
      a.h=0.05; a.i=0.50; a.g=0.45; a.r=1.0;
    }
  }

  // Production
  const isDust=st.ev.some(e=>e.t==='dust_storm');
  const sb=1+st.mod.filter(x=>x==='solar_farm').length*0.4;
  st.power+=solIrr(sol,isDust)*PA*EF*SH/1000*st.se*sb;
  if(st.power>PCRIT*0.3){
    const ib=1+st.mod.filter(x=>x==='isru_plant').length*0.4;
    st.o2+=ISRU_O2*st.ie*Math.min(1.5,a.i*2)*ib;
    st.h2o+=ISRU_H2O*st.ie*Math.min(1.5,a.i*2)*ib;
  }
  st.h2o+=st.mod.filter(x=>x==='water_extractor').length*3;
  if(st.power>PCRIT*0.3&&st.h2o>5){
    const gb=1+st.mod.filter(x=>x==='greenhouse_dome').length*0.5;
    st.food+=GK*st.ge*Math.min(1.5,a.g*2)*gb;
  }
  
  // MAXIMUM REPAIR BAY MITIGATION
  const repairCount = st.mod.filter(x=>x==='repair_bay').length;
  if(repairCount > 0){
    st.se = Math.min(1, st.se + 0.008 * repairCount);
    st.ie = Math.min(1, st.ie + 0.006 * repairCount);
    
    const ultraBoost = 1 + (repairCount - 1) * 0.45; // 45% per additional bay!
    
    if(repairCount >= 1) {
      if(sol % Math.max(3, 8 - repairCount) === 0) {
        st.ie = Math.min(1, st.ie + 0.005 * ultraBoost);
      }
      if(sol % Math.max(2, 6 - repairCount) === 0) {
        st.se = Math.min(1, st.se + 0.004 * ultraBoost);
      }
    }
    
    if(repairCount >= 2) {
      if(sol % Math.max(4, 12 - repairCount * 2) === 0) {
        st.power += 8 * ultraBoost;
      }
      if(sol % Math.max(6, 15 - repairCount * 2) === 0) {
        st.crew.forEach(c => {
          if(c.a) c.hp = Math.min(100, c.hp + 4 * ultraBoost);
        });
      }
    }
    
    if(repairCount >= 3) {
      if(sol % 10 === 0) {
        st.se = Math.min(1, st.se + 0.007 * ultraBoost);
        st.ie = Math.min(1, st.ie + 0.007 * ultraBoost);
        st.power += 10 * ultraBoost;
      }
    }
    
    if(repairCount >= 4) {
      if(sol % 8 === 0) {
        st.se = Math.min(1, st.se + 0.006);
        st.ie = Math.min(1, st.ie + 0.006);
        st.ge = Math.min(1, st.ge + 0.004);
      }
    }
    
    if(repairCount >= 5) {
      if(sol % 5 === 0) {
        st.se = Math.min(1, st.se + 0.005);
        st.ie = Math.min(1, st.ie + 0.005);
        st.power += 6;
      }
      if(sol % 10 === 0) {
        st.crew.forEach(c => {
          if(c.a) c.hp = Math.min(100, c.hp + 3);
        });
      }
    }
    
    if(repairCount >= 6) {
      if(sol % 4 === 0) {
        st.se = Math.min(1, st.se + 0.004);
        st.ie = Math.min(1, st.ie + 0.004);
        st.ge = Math.min(1, st.ge + 0.003);
        st.power += 4;
      }
    }
  }

  // Consumption
  st.o2=Math.max(0,st.o2-nh*OP);
  st.h2o=Math.max(0,st.h2o-nh*HP);
  st.food=Math.max(0,st.food-nh*FP*a.r);
  st.power=Math.max(0,st.power-n*5-st.mod.length*3);
  st.it=Math.max(200,Math.min(310,st.it+(st.power*a.h*0.5>10?0.5:-0.5)));

  // Crew health
  ac.forEach(c=>{
    if(!c.bot){if(st.o2<OP*2)c.hp-=5;if(st.food<FP*2)c.hp-=3}
    if(st.it<250)c.hp-=(c.bot?0.3:2);
    if(st.power<=0)c.hp-=(c.bot?1:0.5);
    c.hp=Math.min(100,c.hp+(c.bot?0.5:0.3));
    if(c.hp<=0)c.a=false;
  });

  // MAXIMUM INFRASTRUCTURE STRATEGY
  if(sol===3&&st.power>16)         {st.mod.push('solar_farm')}     
  else if(sol===6&&st.power>23)    {st.mod.push('solar_farm')}     
  else if(sol===10&&st.power>30)   {st.mod.push('solar_farm')}     
  else if(sol===15&&st.power>38)   {st.mod.push('solar_farm')}     
  else if(sol===22&&st.power>55)   {st.mod.push('repair_bay')}     
  else if(sol===30&&st.power>75)   {st.mod.push('solar_farm')}     
  else if(sol===40&&st.power>105)  {st.mod.push('repair_bay')}     
  else if(sol===55&&st.power>140)  {st.mod.push('solar_farm')}     
  else if(sol===70&&st.power>180)  {st.mod.push('repair_bay')}     
  else if(sol===90&&st.power>230)  {st.mod.push('solar_farm')}     
  else if(sol===110&&st.power>280) {st.mod.push('repair_bay')}     
  else if(sol===135&&st.power>340) {st.mod.push('repair_bay')}     
  else if(sol===165&&st.power>420) {st.mod.push('solar_farm')}     
  else if(sol===195&&st.power>500) {st.mod.push('repair_bay')}     
  else if(sol===225&&st.power>580) {st.mod.push('repair_bay')}     
  else if(sol===255&&st.power>660) {st.mod.push('solar_farm')}     
  else if(sol===285&&st.power>740) {st.mod.push('repair_bay')}     

  // CRI
  st.cri=Math.min(100,Math.max(0,5+(st.power<50?25:st.power<150?10:0)+st.ev.length*6
    +(o2d<5?20:0)+(hd<5?20:0)+(fd<5?20:0)));

  // Death
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
      {n:'ULTRAMAX-01',bot:true,hp:100,mr:100,a:true},
      {n:'ULTRAMAX-02',bot:true,hp:100,mr:100,a:true}
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
const runs = parseInt(process.argv[2]) || 10;

console.log('═══════════════════════════════════════════════');
console.log('  ULTRA-MAX GAUNTLET: Maximum Infrastructure');
console.log('  ' + runs + ' runs × ' + totalSols + ' frames');
console.log('═══════════════════════════════════════════════\n');

const results = [];
for(let i=0; i<runs; i++){
  results.push(runGauntlet(frames, totalSols, i*7919+1));
}

const alive = results.filter(r=>r.alive);
const dead = results.filter(r=>!r.alive);
const solsSorted = results.map(r=>r.sols).sort((a,b)=>a-b);
const medianSols = solsSorted[Math.floor(runs/2)];

console.log('SURVIVAL: ' + (alive.length/runs*100).toFixed(1) + '% (' + alive.length + '/' + runs + ')');
console.log('MEDIAN SOLS: ' + medianSols);

const improvement = medianSols - 441;
const improvementOverEnhanced = medianSols - 465;

if(improvement > 0) {
  console.log('🚀 BASELINE RECORD BROKEN! +' + improvement + ' sols over 441!');
}
if(improvementOverEnhanced > 0) {
  console.log('🔥 ENHANCED RECORD BROKEN! +' + improvementOverEnhanced + ' sols over 465!');
} else if(improvementOverEnhanced === 0) {
  console.log('⚖ ENHANCED RECORD TIED! Matches 465.');
} else {
  console.log('📉 Below enhanced: ' + improvementOverEnhanced + ' sols vs 465.');
}

console.log('\n═══════════════════════════════════════════════');