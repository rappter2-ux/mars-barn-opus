// EXPERIMENTAL ULTRA-ADAPTIVE MARS GOVERNOR v2.0
// Goal: Push beyond current 627 sol record through advanced pattern recognition
// Incorporates multi-layered CRI analysis, predictive modeling, and dynamic risk response

// ═══════════════════════════════════════════════════════════════════
// ULTRA-ADAPTIVE CRI PATTERN RECOGNITION ENGINE
// ═══════════════════════════════════════════════════════════════════

class UltraAdaptiveCRIEngine {
  constructor() {
    this.criHistory = [];
    this.volatilityHistory = [];
    this.trendHistory = [];
    this.riskProfiles = {
      low: { threshold: 15, repairBonus: 0.3, buildDelay: 0 },
      medium: { threshold: 35, repairBonus: 0.5, buildDelay: 2 },
      high: { threshold: 60, repairBonus: 0.8, buildDelay: 5 },
      critical: { threshold: 85, repairBonus: 1.2, buildDelay: 10 }
    };
    this.currentProfile = 'low';
    this.emergencyMode = false;
  }

  updateCRI(cri, sol) {
    this.criHistory.push({ sol, cri });
    
    // Maintain 100-sol rolling window for deeper analysis
    if (this.criHistory.length > 100) {
      this.criHistory.shift();
    }

    // Calculate volatility using standard deviation over last 20 sols
    this.updateVolatility();
    
    // Calculate trend using linear regression over last 10 sols
    this.updateTrend();
    
    // Update risk profile based on complex analysis
    this.updateRiskProfile(cri, sol);
  }

  updateVolatility() {
    if (this.criHistory.length < 20) return;
    
    const recent = this.criHistory.slice(-20).map(h => h.cri);
    const mean = recent.reduce((a, b) => a + b) / recent.length;
    const variance = recent.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / recent.length;
    const volatility = Math.sqrt(variance);
    
    this.volatilityHistory.push(volatility);
    if (this.volatilityHistory.length > 50) {
      this.volatilityHistory.shift();
    }

    // Emergency mode for extreme volatility spikes
    const recentVol = this.volatilityHistory.slice(-5);
    const avgVol = recentVol.reduce((a, b) => a + b) / recentVol.length;
    this.emergencyMode = avgVol > 25; // Extreme volatility threshold
  }

  updateTrend() {
    if (this.criHistory.length < 10) return;
    
    const recent = this.criHistory.slice(-10);
    const n = recent.length;
    const sumX = recent.reduce((sum, _, i) => sum + i, 0);
    const sumY = recent.reduce((sum, h) => sum + h.cri, 0);
    const sumXY = recent.reduce((sum, h, i) => sum + i * h.cri, 0);
    const sumX2 = recent.reduce((sum, _, i) => sum + i * i, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    this.trendHistory.push(slope);
    
    if (this.trendHistory.length > 30) {
      this.trendHistory.shift();
    }
  }

  updateRiskProfile(cri, sol) {
    const volatility = this.volatilityHistory[this.volatilityHistory.length - 1] || 0;
    const trend = this.trendHistory[this.trendHistory.length - 1] || 0;
    
    // Multi-factor risk assessment
    let adjustedCRI = cri;
    adjustedCRI += volatility * 0.5; // Weight volatility
    adjustedCRI += Math.max(0, trend) * 10; // Weight positive trends more heavily
    
    // Account for emergency conditions
    if (this.emergencyMode) {
      adjustedCRI += 20;
    }

    // Determine profile
    if (adjustedCRI >= this.riskProfiles.critical.threshold) {
      this.currentProfile = 'critical';
    } else if (adjustedCRI >= this.riskProfiles.high.threshold) {
      this.currentProfile = 'high';
    } else if (adjustedCRI >= this.riskProfiles.medium.threshold) {
      this.currentProfile = 'medium';
    } else {
      this.currentProfile = 'low';
    }
  }

  getAdaptiveAllocation(baseAllocation, moduleCount, sol) {
    const profile = this.riskProfiles[this.currentProfile];
    const currentVolatility = this.volatilityHistory[this.volatilityHistory.length - 1] || 0;
    const currentTrend = this.trendHistory[this.trendHistory.length - 1] || 0;
    
    // Base allocation adjustments
    let allocation = { ...baseAllocation };
    
    // Ultra-exponential repair scaling
    const repairCount = moduleCount.repair_bay || 0;
    const exponentialBonus = Math.pow(1.65, repairCount); // Higher exponential base
    const volatilityMultiplier = 1 + (currentVolatility / 100);
    const totalRepairBonus = profile.repairBonus * exponentialBonus * volatilityMultiplier;
    
    // Apply adaptive allocation based on risk profile
    if (this.currentProfile === 'critical') {
      allocation.isru = 0.15;
      allocation.greenhouse = 0.20;
      allocation.heating = 0.65; // Heavy focus on heating/power for critical conditions
      allocation.ration = 0.4; // Emergency rations
    } else if (this.currentProfile === 'high') {
      allocation.isru = 0.25;
      allocation.greenhouse = 0.30;
      allocation.heating = 0.45;
      allocation.ration = 0.6;
    } else if (this.currentProfile === 'medium') {
      allocation.isru = 0.35;
      allocation.greenhouse = 0.40;
      allocation.heating = 0.25;
      allocation.ration = 0.8;
    } else {
      allocation.isru = 0.30;
      allocation.greenhouse = 0.45;
      allocation.heating = 0.25;
      allocation.ration = 1.0;
    }

    return {
      allocation,
      repairBonus: Math.min(2.0, totalRepairBonus), // Cap at 200% bonus
      buildDelay: profile.buildDelay,
      emergencyMode: this.emergencyMode
    };
  }

  shouldPrioritizeRepairBay(moduleCount, sol) {
    // Ultra-aggressive repair bay prioritization
    const repairCount = moduleCount.repair_bay || 0;
    const volatility = this.volatilityHistory[this.volatilityHistory.length - 1] || 0;
    
    // Multiple repair bays for redundancy and exponential scaling
    if (repairCount === 0 && sol > 10) return true;
    if (repairCount === 1 && sol > 30 && this.currentProfile !== 'low') return true;
    if (repairCount === 2 && sol > 60 && (this.currentProfile === 'high' || this.currentProfile === 'critical')) return true;
    if (repairCount === 3 && sol > 120 && volatility > 15) return true;
    
    return false;
  }

  getOptimalBuildOrder(currentModules, sol) {
    const moduleCount = {};
    currentModules.forEach(m => {
      moduleCount[m.type] = (moduleCount[m.type] || 0) + 1;
    });

    // Emergency repair bay prioritization
    if (this.shouldPrioritizeRepairBay(moduleCount, sol)) {
      return 'repair_bay';
    }

    // Ultra-adaptive build order based on risk profile and conditions
    const solarCount = moduleCount.solar_farm || 0;
    const hasISRU = moduleCount.isru_plant > 0;
    const hasGreenhouse = moduleCount.greenhouse_dome > 0;
    
    // Phase 1: Core infrastructure (sols 1-50)
    if (sol <= 50) {
      if (!hasISRU) return 'isru_plant';
      if (solarCount < 2) return 'solar_farm';
      if (!hasGreenhouse) return 'greenhouse_dome';
      return 'repair_bay';
    }
    
    // Phase 2: Scaling and redundancy (sols 51-150)
    if (sol <= 150) {
      if (solarCount < 4) return 'solar_farm'; // More solar for better margins
      if (!moduleCount.water_extractor) return 'water_extractor';
      if (!moduleCount.radiation_shelter) return 'radiation_shelter';
      if (moduleCount.greenhouse_dome < 2 && this.currentProfile !== 'low') return 'greenhouse_dome';
      return 'storage_depot';
    }
    
    // Phase 3: Advanced optimization (sols 151+)
    if (solarCount < 6 && this.currentProfile === 'high') return 'solar_farm';
    if (moduleCount.isru_plant < 2 && this.emergencyMode) return 'isru_plant';
    if (!moduleCount.comms_array) return 'comms_array';
    if (moduleCount.storage_depot < 2) return 'storage_depot';
    
    return 'solar_farm'; // Default to more power
  }
}

// ═══════════════════════════════════════════════════════════════════
// INTEGRATION WITH EXISTING SYSTEM
// ═══════════════════════════════════════════════════════════════════

// This would replace/enhance the existing building logic in viewer.html:
/*
const ultraEngine = new UltraAdaptiveCRIEngine();

// In the main tick function, after CRI calculation:
ultraEngine.updateCRI(colonyRiskIndex, state.sol);
const adaptiveStrategy = ultraEngine.getAdaptiveAllocation(currentAllocation, moduleCount, state.sol);

// Apply adaptive allocation
state.allocation = adaptiveStrategy.allocation;

// Enhanced building logic
if (!state.building && state.sol > 15 && o2d > 8 && fd > 8) {
  const nextBuild = ultraEngine.getOptimalBuildOrder(state.modules, state.sol);
  if (nextBuild && adaptiveStrategy.buildDelay === 0) {
    state.building = { type: nextBuild, remaining: Math.floor(8 + R() * 12) };
    buildEvent = { type: 'construction_start', module: nextBuild };
  }
}
*/

module.exports = { UltraAdaptiveCRIEngine };