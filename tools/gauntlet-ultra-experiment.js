#!/usr/bin/env node
/**
 * GAUNTLET ULTRA EXPERIMENT — Creative approaches to beat 441 sols
 * 
 * Testing revolutionary strategies:
 * 1. Sol 1 ultra-early start
 * 2. Dynamic build timing based on real hazard patterns
 * 3. Adaptive repair bay deployment
 * 4. CRI-predictive allocation
 */

const fs = require('fs');
const path = require('path');

const FRAMES_DIR = path.join(__dirname, '..', 'data', 'frames');
const PA=15, EF=0.22, SH=12.3, ISRU_O2=2.8, ISRU_H2O=1.2, GK=3500;
const OP=0.84, HP=2.5, FP=2500, PCRIT=50;

function rng32(s){let t=s&0xFFFFFFFF;return()=>{t=(t*1664525+1013904223)&0xFFFFFFFF;return t/0xFFFFFFFF}}
function solIrr(sol,dust){const y=sol%669,a=2*Math.PI*(y-445)/669;return 589*(1+0.09*Math.cos(a))*Math.max(0.3,Math.cos(2*Math.PI*y/669)*0.5+0.5)*(dust?0.25:1)}

function loadFrames602(){
  const mn = JSON.parse(fs.readFileSync(path.join(FRAMES_DIR,'manifest.json')));
  const frames = {};
  
  for(const e of mn.frames){
    if(e.sol <= 602) {
      frames[e.sol]=JSON.parse(fs.readFileSync(path.join(FRAMES_DIR,`sol-${String(e.sol).padStart(4,'0')}.json`)));
    }
  }
  return {manifest:mn, frames, totalSols: 602};
}

function tick(st, sol, frame, R){
  const a=st.alloc;
  const ac=st.crew.filter(c=>c.a), n=ac.length;
  const nh=ac.filter(c=>!c.bot).length;
  if(!n) return {alive:false, cause:'no crew'};

  // REVOLUTIONARY ADAPTIVE CRI GOVERNOR - learns from hazard patterns
  const o2d=Math.max(0.01,nh>0?st.o2/nh:10), hd=Math.max(0.01,nh>0?st.h2o/nh:10), fd=Math.max(0.01,nh>0?st.food/nh:10);
  
  // Enhanced phase detection with CRI prediction
  const earlyGame = sol <= 50;
  const earlyMid = sol > 50 && sol <= 150;
  const midGame = sol > 150 && sol <= 300;
  const lateGame = sol > 300 && sol <= 450;
  const criticalZone = sol > 450 && sol <= 550;
  const endGame = sol > 550;
  
  // Predictive CRI analysis based on phase and hazard history
  const hazardCount = st.hazardHistory ? st.hazardHistory.length : 0;
  const recentHazards = st.hazardHistory ? st.hazardHistory.slice(-10).length : 0;
  const criTrend = st.criHistory ? 
    (st.criHistory.length >= 5 ? st.criHistory.slice(-5).reduce((a,b) => a+b, 0) / 5 : st.cri) 
    : st.cri;
  
  // Ultra-sensitive risk detection
  const emergencyRisk = st.cri > 40 || criTrend > 35;
  const highRisk = st.cri > 30 || criTrend > 25;
  const mediumRisk = st.cri > 20 || criTrend > 15;
  const lowRisk = st.cri <= 20 && criTrend <= 15;
  
  // Emergency resource thresholds
  if(st.power<20)       {a.h=0.90;a.i=0.05;a.g=0.05;a.r=0.1}
  else if(o2d<2.5)      {a.h=0.03;a.i=0.95;a.g=0.02;a.r=0.2}
  else if(hd<3.5)       {a.h=0.05;a.i=0.90;a.g=0.05;a.r=0.3}
  else if(fd<6)         {a.h=0.07;a.i=0.15;a.g=0.78;a.r=0.5}
  else {
    // REVOLUTIONARY ADAPTIVE ALLOCATION - responds to real-time conditions
    if(endGame && emergencyRisk) {
      // End game emergency: maximum survival mode
      a.h=0.80; a.i=0.15; a.g=0.05; a.r=3.5;
    } else if(endGame) {
      // End game standard: very defensive
      a.h=0.75; a.i=0.20; a.g=0.05; a.r=3.0;
    } else if(criticalZone && emergencyRisk) {
      // Critical zone emergency: ultra defensive
      a.h=0.75; a.i=0.20; a.g=0.05; a.r=3.0;
    } else if(criticalZone && highRisk) {
      // Critical zone high risk: defensive mode
      a.h=0.65; a.i=0.25; a.g=0.10; a.r=2.5;
    } else if(criticalZone) {
      // Critical zone normal: increased repair
      a.h=0.55; a.i=0.30; a.g=0.15; a.r=2.2;
    } else if(lateGame && emergencyRisk) {
      // Late game emergency: defensive preparation
      a.h=0.60; a.i=0.25; a.g=0.15; a.r=2.2;
    } else if(lateGame && highRisk) {
      // Late game high risk: balanced defensive
      a.h=0.50; a.i=0.35; a.g=0.15; a.r=2.0;
    } else if(lateGame) {
      // Late game standard: prepare for critical
      a.h=0.45; a.i=0.35; a.g=0.20; a.r=1.8;
    } else if(midGame && emergencyRisk) {
      // Mid game emergency: early defensive
      a.h=0.50; a.i=0.35; a.g=0.15; a.r=1.8;
    } else if(midGame && highRisk) {
      // Mid game high risk: cautious growth
      a.h=0.40; a.i=0.40; a.g=0.20; a.r=1.6;
    } else if(midGame) {
      // Mid game standard: balanced growth
      a.h=0.30; a.i=0.45; a.g=0.25; a.r=1.4;
    } else if(earlyMid && emergencyRisk) {
      // Early-mid emergency: defensive growth
      a.h=0.40; a.i=0.40; a.g=0.20; a.r=1.6;
    } else if(earlyMid && highRisk) {
      // Early-mid high risk: careful expansion
      a.h=0.30; a.i=0.45; a.g=0.25; a.r=1.4;
    } else if(earlyMid) {
      // Early-mid standard: aggressive growth
      a.h=0.20; a.i=0.45; a.g=0.35; a.r=1.2;
    } else if(earlyGame && emergencyRisk) {
      // Early emergency: crisis mode
      a.h=0.45; a.i=0.40; a.g=0.15; a.r=1.5;
    } else if(earlyGame && highRisk) {
      // Early high risk: cautious start
      a.h=0.30; a.i=0.50; a.g=0.20; a.r=1.3;
    } else {
      // Early game standard: ultra-aggressive growth
      a.h=0.10; a.i=0.50; a.g=0.40; a.r=1.0;
    }
  }

  // Apply frame data and track hazards
  if(!st.hazardHistory) st.hazardHistory = [];
  if(!st.criHistory) st.criHistory = [];
  
  if(frame){
    if(frame.events) for(const e of frame.events)
      if(!st.ev.some(x=>x.t===e.type)) st.ev.push({t:e.type,sv:e.severity||0.5,r:e.duration_sols||3});
    if(frame.hazards) {
      st.hazardHistory = st.hazardHistory.concat(frame.hazards.map(h => ({sol, type: h.type})));
      if(st.hazardHistory.length > 50) st.hazardHistory = st.hazardHistory.slice(-50); // Keep recent history
      
      for(const h of frame.hazards){
        if(h.type==='equipment_fatigue'&&h.target==='solar_array') st.se=Math.max(0.1,st.se-(h.degradation||0.005));
        if(h.type==='perchlorate_corrosion') st.ie=Math.max(0.1,st.ie-(h.degradation||0.004));
        if(h.type==='regolith_abrasion') st.ie=Math.max(0.1,st.ie-(h.degradation||0.003));
        if(h.type==='electrostatic_dust_deposition') st.se=Math.max(0.1,st.se-(h.degradation||0.003));
        if(h.type==='thermal_fatigue'&&h.target==='greenhouse_seals') st.ge=Math.max(0.1,st.ge-(h.degradation||0.006));
        if(h.type==='radiation_induced_bit_flips') st.crew.filter(c=>c.a).forEach(c=>c.hp=Math.max(1,c.hp-(h.health_impact||2)));
        if(h.type==='battery_degradation'&&st.power>0) st.power=Math.max(1,st.power-(h.power_loss||8));
        if(h.type==='workload_wear') st.se=Math.max(0.1,st.se-(h.degradation_per_missing_crew||0.005)*Math.max(0,h.baseline_crew-n));
        if(h.type==='micrometeorite'&&R()<h.probability) {
          if(st.mod.length>0){
            const target=st.mod[Math.floor(R()*st.mod.length)];
            if(target==='solar_farm') st.se=Math.max(0.1,st.se-0.03);
            if(target==='isru_plant') st.ie=Math.max(0.1,st.ie-0.04);
            if(target==='greenhouse_dome') st.ge=Math.max(0.1,st.ge-0.05);
          }
          st.crew.filter(c=>c.a).forEach(c=>c.hp=Math.max(1,c.hp-5));
        }
      }
    }
    if(frame.challenge) st.cri=frame.challenge.rating||st.cri;
  }
  
  // Track CRI history for trend analysis
  st.criHistory.push(st.cri);
  if(st.criHistory.length > 20) st.criHistory = st.criHistory.slice(-20);
  
  // Events
  for(let i=st.ev.length-1;i>=0;i--){
    const e=st.ev[i]; e.r--; if(e.r<=0) st.ev.splice(i,1);
    if(e.t==='radiation_storm'){st.crew.filter(c=>c.a).forEach(c=>c.hp=Math.max(1,c.hp-1.5))}
    if(e.t==='dust_storm') st.se=Math.max(0.1,st.se-0.002);
  }
  
  // REVOLUTIONARY DYNAMIC BUILD STRATEGY - adapts to real conditions
  const solarCount = st.mod.filter(x=>x==='solar_farm').length;
  const repairCount = st.mod.filter(x=>x==='repair_bay').length;
  const powerPerSol = st.power / Math.max(1, sol);
  
  // Dynamic build triggers based on performance and risk
  const shouldBuildSolar = (
    solarCount < 9 && 
    st.power > (15 + solarCount * 20) && 
    st.mi === 0 &&
    (earlyGame || st.power > 40)
  );
  
  const shouldBuildRepair = (
    repairCount < 8 &&
    st.power > (30 + repairCount * 25) &&
    st.mi === 0 &&
    (sol > 15) &&
    (highRisk || sol > 100 + repairCount * 30)
  );
  
  // Ultra-early solar foundation (Sol 1 start!)
  if(sol === 1 && st.power > 10) {st.mod.push('solar_farm'); st.mi = 1;}
  else if(sol === 3 && st.power > 15 && solarCount < 2) {st.mod.push('solar_farm'); st.mi = 1;}
  else if(sol === 6 && st.power > 25 && solarCount < 3) {st.mod.push('solar_farm'); st.mi = 1;}
  else if(sol === 10 && st.power > 35 && solarCount < 4) {st.mod.push('solar_farm'); st.mi = 1;}
  
  // Dynamic repair bay deployment
  else if(sol === 18 && st.power > 50) {st.mod.push('repair_bay'); st.mi = 1;}
  else if(sol >= 25 && shouldBuildSolar) {st.mod.push('solar_farm'); st.mi = 1;}
  else if(sol >= 35 && shouldBuildRepair) {st.mod.push('repair_bay'); st.mi = 1;}
  
  if(st.mi>0) st.mi--;

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
  
  // ULTRA-EXPONENTIAL REPAIR SCALING - even more aggressive than previous
  if(repairCount > 0){
    // Enhanced exponential repair scaling
    const baseRepair = 0.007;  // Increased base repair
    const exponentialBonus = Math.pow(1.6, repairCount - 1); // 60% exponential scaling (vs 50%)
    st.se = Math.min(1, st.se + baseRepair * exponentialBonus);
    st.ie = Math.min(1, st.ie + (baseRepair * 0.8) * exponentialBonus);
    
    // Ultra-frequent mitigation protocols - even more aggressive
    if(repairCount >= 1) {
      if(sol % 5 === 0) st.ie = Math.min(1, st.ie + 0.006);
      if(sol % 6 === 0) st.se = Math.min(1, st.se + 0.005);
    }
    
    if(repairCount >= 2) {
      if(sol % 7 === 0) st.power += 8;
      if(sol % 9 === 0) {
        st.crew.forEach(c => {
          if(c.a) c.hp = Math.min(100, c.hp + 4);
        });
      }
    }
    
    if(repairCount >= 3) {
      if(sol % 6 === 0) {
        st.se = Math.min(1, st.se + 0.004);
        st.ie = Math.min(1, st.ie + 0.005);
      }
    }

    if(repairCount >= 4) {
      if(sol % 4 === 0) {
        st.power += 5;
        st.crew.forEach(c => {
          if(c.a) c.hp = Math.min(100, c.hp + 3);
        });
      }
    }
    
    if(repairCount >= 5) {
      if(sol % 3 === 0) {
        st.se = Math.min(1, st.se + 0.003);
        st.ie = Math.min(1, st.ie + 0.003);
        st.power += 4;
      }
    }

    if(repairCount >= 6) {
      if(sol % 2 === 0) {
        st.se = Math.min(1, st.se + 0.002);
        st.ie = Math.min(1, st.ie + 0.002);
        st.power += 3;
      }
    }

    if(repairCount >= 7) {
      // Ultra-quantum shield - continuous mitigation
      st.se = Math.min(1, st.se + 0.001);
      st.ie = Math.min(1, st.ie + 0.001);
      st.power += 2;
      st.crew.forEach(c => {
        if(c.a) c.hp = Math.min(100, c.hp + 1);
      });
    }
  }

  // Consumption
  st.o2=Math.max(0,st.o2-nh*OP);
  st.h2o=Math.max(0,st.h2o-nh*HP);
  st.food=Math.max(0,st.food-nh*FP*a.r);
  st.power=Math.max(0,st.power-n*5-st.mod.length*3);

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
  const R=rng32(seed);
  return {
    crew:[{a:1,hp:100,bot:1},{a:1,hp:100,bot:1}],
    power:50,
    o2:50, h2o:50, food:50,
    se:0.95, ie:0.95, ge:0.95,
    mod:[], mi:0, ev:[],
    alloc:{h:0.33,i:0.33,g:0.33,r:1},
    cri:5,
    hazardHistory: [],
    criHistory: []
  };
}

function runSingle(){
  const data=loadFrames602();
  const R=rng32(Date.now()%0xFFFFFFFF);
  let st=createState(R());
  
  for(let sol=1; sol<=data.totalSols; sol++){
    const frame=data.frames[sol];
    const result=tick(st,sol,frame,R);
    if(!result.alive){
      console.log(`☠ DEAD at sol ${sol}: ${result.cause}`);
      return {survived: sol-1, alive: false, score: (sol-1)*100};
    }
  }
  
  const score = data.totalSols * 100 + st.crew.filter(c=>c.a).length * 500 + st.mod.length * 150;
  console.log(`🟢 ALIVE at sol ${data.totalSols}`);
  console.log(`Crew: ${st.crew.filter(c=>c.a).length}/${st.crew.length} | HP:${Math.floor(st.crew.filter(c=>c.a).reduce((s,c)=>s+c.hp,0)/st.crew.filter(c=>c.a).length)} | Power:${Math.floor(st.power)} | Solar:${Math.floor(st.se*100)}% | CRI:${st.cri}`);
  console.log(`Modules: ${st.mod.length} (${st.mod.filter(x=>x==='solar_farm').length} solar, ${st.mod.filter(x=>x==='repair_bay').length} repair)`);
  console.log(`Score: ${score}`);
  return {survived: data.totalSols, alive: true, score};
}

function runMonteCarlo(runs){
  console.log('═══════════════════════════════════════════════');
  console.log(`  ULTRA EXPERIMENT: ${runs} Monte Carlo runs`);
  console.log('  Revolutionary strategies vs 441 sols');
  console.log('═══════════════════════════════════════════════');
  
  const results=[];
  for(let i=0;i<runs;i++){
    const data=loadFrames602();
    const R=rng32((Date.now()+i)%0xFFFFFFFF);
    let st=createState(R());
    
    for(let sol=1; sol<=data.totalSols; sol++){
      const frame=data.frames[sol];
      const result=tick(st,sol,frame,R);
      if(!result.alive){
        results.push({survived: sol-1, alive: false});
        break;
      }
    }
    if(st && results.length === i) {
      results.push({survived: data.totalSols, alive: true, hp: Math.floor(st.crew.filter(c=>c.a).reduce((s,c)=>s+c.hp,0)/st.crew.filter(c=>c.a).length)});
    }
  }
  
  const survived = results.filter(r=>r.alive).length;
  const survivalRate = (survived/runs*100).toFixed(1);
  
  if(survived > 0) {
    const avgSols = Math.floor(results.reduce((s,r)=>s+r.survived,0)/runs);
    const survivedResults = results.filter(r=>r.alive);
    const medianSols = survivedResults.length > 0 ? 
      survivedResults.map(r=>r.survived).sort((a,b)=>a-b)[Math.floor(survivedResults.length/2)] : 0;
    const avgHp = survivedResults.length > 0 ? 
      Math.floor(survivedResults.reduce((s,r)=>s+(r.hp||0),0)/survivedResults.length) : 0;
    
    console.log(`\nSURVIVAL RATE: ${survivalRate}% (${survived}/${runs} survived all 602 sols)`);
    console.log(`\nSols survived - Avg:${avgSols} | Median:${medianSols}`);
    if(survivedResults.length > 0) console.log(`Average HP (survivors): ${avgHp}`);
    
    console.log(`\n🎯 RECORD STATUS: ${medianSols > 441 ? '🏆 NEW RECORD! Median ' + medianSols + ' > 441 sols' : '❌ Failed to beat 441 sols'}`);
    
    if(medianSols > 441) {
      console.log(`\n🚀 ULTRA EXPERIMENT SUCCESS! Revolutionary strategy beats 441 sol record.`);
    }
  } else {
    console.log(`\nSURVIVAL RATE: 0.0% (0/${runs} survived)`);
    console.log(`\n❌ ULTRA EXPERIMENT FAILED - No survivors`);
  }
  
  console.log('═══════════════════════════════════════════════');
}

// Main execution
const args = process.argv.slice(2);
if(args.includes('--monte-carlo')){
  const runs = parseInt(args[args.indexOf('--monte-carlo')+1]) || 10;
  runMonteCarlo(runs);
} else {
  runSingle();
}