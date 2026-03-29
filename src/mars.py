"""Mars Barn Opus — Mars Physics

Terrain generation, atmosphere model, solar irradiance, thermal dynamics,
and radiation environment. Everything Mars, nothing colony.

All constants from config.py. Zero magic numbers.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

from config import (
    MARS_SURFACE_PRESSURE_PA, MARS_SCALE_HEIGHT_KM, MARS_CO2_FRACTION,
    MARS_SURFACE_TEMP_K, MARS_TEMP_LAPSE_RATE_K_PER_KM,
    MARS_MIN_TEMP_K, MARS_MAX_TEMP_K, MARS_DIURNAL_SWING_K,
    MARS_LATITUDE_TEMP_GRADIENT_K,
    MARS_MIN_ELEVATION_M, MARS_MAX_ELEVATION_M,
    MARS_SOLAR_CONSTANT_W_M2, MARS_SOLAR_MIN_W_M2, MARS_SOLAR_MAX_W_M2,
    MARS_AXIAL_TILT_DEG, MARS_SOL_HOURS, MARS_YEAR_SOLS,
    MARS_SURFACE_RADIATION_MSV_PER_SOL, MARS_SOLAR_FLARE_DOSE_MSV,
    HABITAT_SURFACE_AREA_M2, HABITAT_THERMAL_MASS_KG,
    HABITAT_INSULATION_R_VALUE, HABITAT_WINDOW_EFFICIENCY,
    HABITAT_TARGET_TEMP_K, HABITAT_EMISSIVITY,
)


# =============================================================================
# TERRAIN
# =============================================================================

@dataclass
class TerrainCell:
    """Single terrain cell with elevation and properties."""
    elevation_m: float
    is_crater: bool = False
    is_ridge: bool = False
    regolith_depth_m: float = 2.0
    ice_fraction: float = 0.0


@dataclass
class Terrain:
    """2D Mars terrain grid."""
    grid: List[List[TerrainCell]]
    size: int
    seed: int

    @property
    def elevations(self) -> List[List[float]]:
        """Raw elevation grid."""
        return [[c.elevation_m for c in row] for row in self.grid]

    def cell_at(self, x: int, y: int) -> TerrainCell:
        """Get terrain cell, clamping to bounds."""
        x = max(0, min(x, self.size - 1))
        y = max(0, min(y, self.size - 1))
        return self.grid[y][x]

    def mean_elevation(self) -> float:
        """Average elevation across grid."""
        total = sum(c.elevation_m for row in self.grid for c in row)
        return total / (self.size * self.size)


def generate_terrain(size: int = 32, seed: int = 42) -> Terrain:
    """Generate Mars terrain using diamond-square with geological features.

    Produces a size x size grid of TerrainCells with:
    - Base heightmap from diamond-square interpolation
    - Craters (circular depressions, 50-800m deep)
    - Ridges (linear elevations, 100-1500m tall)
    - Regolith depth variation
    - Polar ice at high latitudes (top/bottom rows)
    """
    rng = random.Random(seed)
    grid = [[0.0] * size for _ in range(size)]

    # Diamond-square simplified: seed corners, interpolate
    grid[0][0] = rng.gauss(0, 1000)
    grid[0][size - 1] = rng.gauss(0, 1000)
    grid[size - 1][0] = rng.gauss(0, 1000)
    grid[size - 1][size - 1] = rng.gauss(0, 1000)

    _diamond_square_fill(grid, size, rng, roughness=0.7)

    # Add craters
    num_craters = rng.randint(3, 8)
    for _ in range(num_craters):
        cx, cy = rng.randint(0, size - 1), rng.randint(0, size - 1)
        radius = rng.randint(2, max(3, size // 6))
        depth = rng.uniform(50, 800)
        for y in range(max(0, cy - radius), min(size, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(size, cx + radius + 1)):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist <= radius:
                    factor = 1.0 - (dist / radius) ** 2
                    grid[y][x] -= depth * factor

    # Add ridges
    num_ridges = rng.randint(1, 3)
    for _ in range(num_ridges):
        x0, y0 = rng.randint(0, size - 1), rng.randint(0, size - 1)
        angle = rng.uniform(0, math.pi)
        length = rng.randint(size // 3, size)
        height = rng.uniform(100, 1500)
        width = rng.randint(1, 3)
        for step in range(length):
            rx = int(x0 + step * math.cos(angle))
            ry = int(y0 + step * math.sin(angle))
            for w in range(-width, width + 1):
                nx = rx + int(w * math.sin(angle))
                ny = ry - int(w * math.cos(angle))
                if 0 <= nx < size and 0 <= ny < size:
                    falloff = 1.0 - abs(w) / (width + 1)
                    grid[ny][nx] += height * falloff

    # Clamp to Mars range and build cells
    cells = []
    for y in range(size):
        row = []
        for x in range(size):
            elev = max(MARS_MIN_ELEVATION_M,
                       min(MARS_MAX_ELEVATION_M, grid[y][x]))
            is_crater = grid[y][x] < -200
            is_ridge = grid[y][x] > 500
            regolith = rng.uniform(0.5, 5.0)
            # Polar ice in top/bottom 15% of grid
            lat_frac = abs(y - size / 2) / (size / 2)
            ice = max(0.0, (lat_frac - 0.85) / 0.15) if lat_frac > 0.85 else 0.0
            row.append(TerrainCell(
                elevation_m=elev,
                is_crater=is_crater,
                is_ridge=is_ridge,
                regolith_depth_m=regolith,
                ice_fraction=ice,
            ))
        cells.append(row)

    return Terrain(grid=cells, size=size, seed=seed)


def _diamond_square_fill(grid: list, size: int, rng: random.Random,
                         roughness: float) -> None:
    """Fill grid using simplified interpolation with random displacement.

    Works with any grid size (not just power-of-2+1).
    Uses progressively finer passes to fill in detail.
    """
    step = max(2, size // 2)
    scale = 1000.0
    while step >= 2:
        half = step // 2
        # Diamond step: fill centers of squares
        for y in range(half, size, step):
            for x in range(half, size, step):
                neighbors = []
                for dy, dx in [(-half, -half), (-half, half),
                               (half, -half), (half, half)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < size and 0 <= nx < size:
                        neighbors.append(grid[ny][nx])
                if neighbors:
                    grid[y][x] = sum(neighbors) / len(neighbors) + rng.gauss(0, scale)
        # Square step: fill edge midpoints
        for y in range(0, size, half):
            x_start = half if (y // half) % 2 == 0 else 0
            for x in range(x_start, size, step):
                neighbors = []
                for dy, dx in [(-half, 0), (half, 0), (0, -half), (0, half)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < size and 0 <= nx < size:
                        neighbors.append(grid[ny][nx])
                if neighbors:
                    grid[y][x] = sum(neighbors) / len(neighbors) + rng.gauss(0, scale)
        step = half
        scale *= roughness
        scale *= roughness


# =============================================================================
# ATMOSPHERE
# =============================================================================

@dataclass
class AtmosphereReading:
    """Atmospheric conditions at a point."""
    pressure_pa: float
    temperature_k: float
    co2_fraction: float
    optical_depth: float
    wind_speed_m_s: float


def atmosphere_at(elevation_m: float, latitude_deg: float = 0.0,
                  sol_of_year: float = 0.0, hour_of_sol: float = 12.0,
                  dust_factor: float = 1.0) -> AtmosphereReading:
    """Compute atmospheric conditions at a given location and time.

    Args:
        elevation_m: Height above areoid datum (m)
        latitude_deg: -90 (south pole) to +90 (north pole)
        sol_of_year: 0 to MARS_YEAR_SOLS
        hour_of_sol: 0 to MARS_SOL_HOURS
        dust_factor: 1.0 = clear, 4.0 = major dust storm
    """
    # Pressure: barometric formula
    altitude_km = elevation_m / 1000.0
    pressure = MARS_SURFACE_PRESSURE_PA * math.exp(
        -altitude_km / MARS_SCALE_HEIGHT_KM
    )

    # Temperature: base + latitude + diurnal + seasonal
    base_temp = MARS_SURFACE_TEMP_K - altitude_km * MARS_TEMP_LAPSE_RATE_K_PER_KM

    # Latitude effect: colder at poles
    lat_effect = -MARS_LATITUDE_TEMP_GRADIENT_K * abs(latitude_deg) / 90.0

    # Diurnal cycle: warmest at ~14:00, coldest at ~05:00
    solar_angle = 2 * math.pi * (hour_of_sol - 14.0) / MARS_SOL_HOURS
    diurnal = MARS_DIURNAL_SWING_K / 2.0 * math.cos(solar_angle)

    # Seasonal effect: +/- 15K based on hemisphere and sol of year
    season_angle = 2 * math.pi * sol_of_year / MARS_YEAR_SOLS
    hemisphere_sign = 1.0 if latitude_deg >= 0 else -1.0
    seasonal = 15.0 * hemisphere_sign * math.cos(season_angle)

    temperature = max(MARS_MIN_TEMP_K, min(MARS_MAX_TEMP_K,
                      base_temp + lat_effect + diurnal + seasonal))

    # Dust reduces pressure slightly, increases optical depth
    pressure *= (1.0 - 0.15 * (dust_factor - 1.0) / 3.0)

    # Optical depth
    base_optical_depth = 0.5
    optical_depth = base_optical_depth * dust_factor

    # Wind: stronger in storms, seasonal variation
    base_wind = 7.0 + 5.0 * abs(math.sin(season_angle))
    wind_speed = base_wind * (1.0 + 0.5 * (dust_factor - 1.0))

    return AtmosphereReading(
        pressure_pa=pressure,
        temperature_k=temperature,
        co2_fraction=MARS_CO2_FRACTION,
        optical_depth=optical_depth,
        wind_speed_m_s=wind_speed,
    )


# =============================================================================
# SOLAR IRRADIANCE
# =============================================================================

def solar_irradiance(latitude_deg: float = 0.0, sol_of_year: float = 0.0,
                     hour_of_sol: float = 12.0,
                     dust_factor: float = 1.0) -> float:
    """Calculate surface solar irradiance (W/m^2).

    Uses Mars solar constant with orbital variation, axial tilt,
    latitude, time of day, and atmospheric attenuation (Beer-Lambert).
    """
    # Orbital variation: perihelion at Ls=251 (~sol 445)
    orbit_angle = 2 * math.pi * (sol_of_year - 445) / MARS_YEAR_SOLS
    orbital_factor = 1.0 + 0.09 * math.cos(orbit_angle)  # ~9% eccentricity
    solar_constant = MARS_SOLAR_CONSTANT_W_M2 * orbital_factor

    # Solar declination
    ls_angle = 2 * math.pi * sol_of_year / MARS_YEAR_SOLS
    declination = math.radians(MARS_AXIAL_TILT_DEG) * math.sin(ls_angle)

    # Hour angle
    hour_angle = 2 * math.pi * (hour_of_sol - MARS_SOL_HOURS / 2) / MARS_SOL_HOURS

    # Solar elevation angle
    lat_rad = math.radians(latitude_deg)
    sin_elevation = (math.sin(lat_rad) * math.sin(declination)
                     + math.cos(lat_rad) * math.cos(declination)
                     * math.cos(hour_angle))

    if sin_elevation <= 0:
        return 0.0  # Night

    # Air mass (simplified for thin Mars atmosphere)
    air_mass = 1.0 / max(sin_elevation, 0.05)

    # Beer-Lambert attenuation
    optical_depth = 0.5 * dust_factor
    transmission = math.exp(-optical_depth * air_mass)

    return solar_constant * sin_elevation * transmission


def daily_mean_irradiance(latitude_deg: float = 0.0,
                          sol_of_year: float = 0.0,
                          dust_factor: float = 1.0,
                          samples: int = 24) -> float:
    """Average irradiance over one sol (W/m^2)."""
    total = 0.0
    for i in range(samples):
        hour = (i + 0.5) * MARS_SOL_HOURS / samples
        total += solar_irradiance(latitude_deg, sol_of_year, hour, dust_factor)
    return total / samples


# =============================================================================
# THERMAL DYNAMICS
# =============================================================================

@dataclass
class ThermalState:
    """Habitat thermal state."""
    interior_temp_k: float = HABITAT_TARGET_TEMP_K
    heating_power_kw: float = 0.0
    solar_gain_kw: float = 0.0
    total_loss_kw: float = 0.0

    @property
    def interior_temp_c(self) -> float:
        """Interior temperature in Celsius."""
        return self.interior_temp_k - 273.15


def compute_thermal(exterior_temp_k: float, irradiance_w_m2: float,
                    interior_temp_k: float = HABITAT_TARGET_TEMP_K,
                    heating_kw: float = 0.0) -> ThermalState:
    """Compute habitat thermal balance for one sol.

    Models:
    - Conduction/convection loss through insulation
    - Radiative loss (Stefan-Boltzmann)
    - Solar gain through windows
    - Active heating system
    - Thermal mass damping

    Returns the resulting ThermalState.
    """
    stefan_boltzmann = 5.67e-8

    # Losses
    conduction_loss_w = (HABITAT_SURFACE_AREA_M2
                         * (interior_temp_k - exterior_temp_k)
                         / HABITAT_INSULATION_R_VALUE)
    conduction_loss_kw = max(0.0, conduction_loss_w / 1000.0)

    # Clamp interior temp for physics stability
    safe_interior = max(100.0, min(400.0, interior_temp_k))
    safe_exterior = max(50.0, min(350.0, exterior_temp_k))

    radiative_loss_w = (HABITAT_EMISSIVITY * stefan_boltzmann
                        * HABITAT_SURFACE_AREA_M2
                        * (safe_interior ** 4 - safe_exterior ** 4))
    radiative_loss_kw = max(0.0, radiative_loss_w / 1000.0)

    total_loss_kw = conduction_loss_kw + radiative_loss_kw

    # Gains
    solar_gain_kw = (irradiance_w_m2 * HABITAT_SURFACE_AREA_M2
                     * HABITAT_WINDOW_EFFICIENCY / 1000.0)

    # Net energy balance
    net_power_kw = heating_kw + solar_gain_kw - total_loss_kw

    # Temperature change (simplified: energy / thermal mass / specific heat)
    # Using ~1000 J/(kg*K) for habitat thermal mass specific heat
    # Clamp dt to prevent runaway (max 20K change per sol)
    energy_j = net_power_kw * 1000.0 * MARS_SOL_HOURS * 3600.0
    dt_k = energy_j / (HABITAT_THERMAL_MASS_KG * 1000.0)
    dt_k = max(-20.0, min(20.0, dt_k))

    new_temp_k = max(100.0, min(350.0, interior_temp_k + dt_k))

    return ThermalState(
        interior_temp_k=new_temp_k,
        heating_power_kw=heating_kw,
        solar_gain_kw=solar_gain_kw,
        total_loss_kw=total_loss_kw,
    )


def required_heating_kw(exterior_temp_k: float,
                        irradiance_w_m2: float) -> float:
    """Calculate heating power needed to maintain target temperature."""
    stefan_boltzmann = 5.67e-8
    target = HABITAT_TARGET_TEMP_K

    conduction_loss = (HABITAT_SURFACE_AREA_M2
                       * (target - exterior_temp_k)
                       / HABITAT_INSULATION_R_VALUE) / 1000.0
    radiative_loss = (HABITAT_EMISSIVITY * stefan_boltzmann
                      * HABITAT_SURFACE_AREA_M2
                      * (target ** 4 - exterior_temp_k ** 4)) / 1000.0
    solar_gain = (irradiance_w_m2 * HABITAT_SURFACE_AREA_M2
                  * HABITAT_WINDOW_EFFICIENCY / 1000.0)

    needed = max(0.0, conduction_loss + radiative_loss - solar_gain)
    return needed


# =============================================================================
# RADIATION
# =============================================================================

def radiation_dose(sol_count: int = 1, in_habitat: bool = True,
                   shielding_factor: float = 0.5,
                   solar_flare: bool = False) -> float:
    """Calculate cumulative radiation dose in millisieverts.

    Args:
        sol_count: Number of sols of exposure
        in_habitat: Whether inside a shielded habitat
        shielding_factor: Fraction of GCR blocked by habitat (0-1)
        solar_flare: Whether a solar particle event is occurring
    """
    gcr_dose = MARS_SURFACE_RADIATION_MSV_PER_SOL * sol_count
    if in_habitat:
        gcr_dose *= (1.0 - shielding_factor)

    flare_dose = 0.0
    if solar_flare:
        flare_dose = MARS_SOLAR_FLARE_DOSE_MSV
        if in_habitat:
            flare_dose *= (1.0 - shielding_factor * 0.8)  # Less effective vs SEP

    return gcr_dose + flare_dose


# =============================================================================
# VISUALIZATION
# =============================================================================

ELEVATION_CHARS = " .:-=+*#%@"


def render_terrain_ascii(terrain: Terrain) -> str:
    """Render terrain as ASCII art."""
    elevs = terrain.elevations
    flat = [e for row in elevs for e in row]
    lo, hi = min(flat), max(flat)
    rng = hi - lo if hi > lo else 1.0

    lines = []
    for row in elevs:
        line = ""
        for e in row:
            idx = int((e - lo) / rng * (len(ELEVATION_CHARS) - 1))
            idx = max(0, min(idx, len(ELEVATION_CHARS) - 1))
            line += ELEVATION_CHARS[idx]
        lines.append(line)
    return "\n".join(lines)


def render_atmosphere_table(latitude_deg: float = 0.0,
                            sol_of_year: float = 0.0) -> str:
    """Render atmosphere profile as formatted table."""
    lines = [f"{'Alt (km)':>10} {'Press (Pa)':>12} {'Temp (K)':>10} {'Temp (C)':>10}"]
    lines.append("-" * 46)
    for alt_km in range(0, 35, 5):
        atm = atmosphere_at(alt_km * 1000.0, latitude_deg, sol_of_year)
        temp_c = atm.temperature_k - 273.15
        lines.append(f"{alt_km:>10} {atm.pressure_pa:>12.1f} "
                      f"{atm.temperature_k:>10.1f} {temp_c:>10.1f}")
    return "\n".join(lines)
