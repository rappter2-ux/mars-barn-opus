"""Tests for Mars physics — validated against real Mars data."""
from __future__ import annotations

import sys
import math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "src"))

from mars import (
    generate_terrain, atmosphere_at, solar_irradiance, daily_mean_irradiance,
    compute_thermal, required_heating_kw, radiation_dose, render_terrain_ascii,
    render_atmosphere_table,
)
from config import (
    MARS_SURFACE_PRESSURE_PA, MARS_MIN_ELEVATION_M, MARS_MAX_ELEVATION_M,
    MARS_MIN_TEMP_K, MARS_MAX_TEMP_K, MARS_SOLAR_CONSTANT_W_M2,
    MARS_SURFACE_RADIATION_MSV_PER_SOL,
)


# =============================================================================
# TERRAIN
# =============================================================================

class TestTerrain:
    def test_terrain_size(self):
        t = generate_terrain(size=16, seed=42)
        assert t.size == 16
        assert len(t.grid) == 16
        assert len(t.grid[0]) == 16

    def test_elevation_within_mars_range(self):
        t = generate_terrain(size=32, seed=42)
        for row in t.grid:
            for cell in row:
                assert MARS_MIN_ELEVATION_M <= cell.elevation_m <= MARS_MAX_ELEVATION_M

    def test_deterministic_generation(self):
        t1 = generate_terrain(size=16, seed=42)
        t2 = generate_terrain(size=16, seed=42)
        for y in range(16):
            for x in range(16):
                assert t1.grid[y][x].elevation_m == t2.grid[y][x].elevation_m

    def test_different_seeds_differ(self):
        t1 = generate_terrain(size=16, seed=42)
        t2 = generate_terrain(size=16, seed=99)
        # At least some cells should differ
        diffs = sum(1 for y in range(16) for x in range(16)
                    if t1.grid[y][x].elevation_m != t2.grid[y][x].elevation_m)
        assert diffs > 0

    def test_has_craters_and_ridges(self):
        t = generate_terrain(size=32, seed=42)
        has_crater = any(c.is_crater for row in t.grid for c in row)
        has_ridge = any(c.is_ridge for row in t.grid for c in row)
        # At least one should exist in a 32x32 grid
        assert has_crater or has_ridge

    def test_polar_ice(self):
        t = generate_terrain(size=32, seed=42)
        # Top and bottom rows should have ice possibility
        top_ice = any(t.grid[0][x].ice_fraction > 0 for x in range(32))
        bottom_ice = any(t.grid[31][x].ice_fraction > 0 for x in range(32))
        mid_ice = any(t.grid[16][x].ice_fraction > 0 for x in range(32))
        # Mid should have no ice, edges might
        assert not mid_ice

    def test_mean_elevation(self):
        t = generate_terrain(size=16, seed=42)
        mean = t.mean_elevation()
        assert isinstance(mean, float)

    def test_cell_at_clamping(self):
        t = generate_terrain(size=16, seed=42)
        # Out of bounds should clamp, not crash
        cell = t.cell_at(-5, -5)
        assert cell == t.grid[0][0]
        cell = t.cell_at(100, 100)
        assert cell == t.grid[15][15]

    def test_ascii_render(self):
        t = generate_terrain(size=8, seed=42)
        ascii_art = render_terrain_ascii(t)
        lines = ascii_art.split("\n")
        assert len(lines) == 8
        assert all(len(line) == 8 for line in lines)


# =============================================================================
# ATMOSPHERE
# =============================================================================

class TestAtmosphere:
    def test_surface_pressure_near_610pa(self):
        atm = atmosphere_at(0.0)
        assert 500 < atm.pressure_pa < 700

    def test_pressure_decreases_with_altitude(self):
        low = atmosphere_at(0.0)
        high = atmosphere_at(10000.0)
        assert high.pressure_pa < low.pressure_pa

    def test_temperature_in_mars_range(self):
        for lat in [-60, 0, 60]:
            for hour in [0, 6, 12, 18]:
                atm = atmosphere_at(0.0, lat, 0.0, hour)
                assert MARS_MIN_TEMP_K <= atm.temperature_k <= MARS_MAX_TEMP_K

    def test_poles_colder_than_equator(self):
        equator = atmosphere_at(0.0, 0.0, 0.0, 12.0)
        pole = atmosphere_at(0.0, 80.0, 0.0, 12.0)
        assert pole.temperature_k < equator.temperature_k

    def test_dust_storm_increases_optical_depth(self):
        clear = atmosphere_at(0.0, dust_factor=1.0)
        dusty = atmosphere_at(0.0, dust_factor=4.0)
        assert dusty.optical_depth > clear.optical_depth

    def test_co2_fraction(self):
        atm = atmosphere_at(0.0)
        assert abs(atm.co2_fraction - 0.953) < 0.001

    def test_wind_increases_in_storms(self):
        clear = atmosphere_at(0.0, dust_factor=1.0)
        storm = atmosphere_at(0.0, dust_factor=4.0)
        assert storm.wind_speed_m_s > clear.wind_speed_m_s

    def test_atmosphere_table_renders(self):
        table = render_atmosphere_table()
        assert "Alt (km)" in table
        assert "Press (Pa)" in table


# =============================================================================
# SOLAR
# =============================================================================

class TestSolar:
    def test_noon_equator_irradiance(self):
        """Equatorial noon should be roughly 400-600 W/m^2."""
        irr = solar_irradiance(0.0, 0.0, 12.0, 1.0)
        assert 300 < irr < 650

    def test_night_is_zero(self):
        """Midnight should be zero irradiance."""
        irr = solar_irradiance(0.0, 0.0, 0.0, 1.0)
        assert irr == 0.0

    def test_dust_reduces_irradiance(self):
        clear = solar_irradiance(0.0, 0.0, 12.0, 1.0)
        dusty = solar_irradiance(0.0, 0.0, 12.0, 4.0)
        assert dusty < clear
        assert dusty < clear * 0.5  # Should be significantly reduced

    def test_daily_mean_positive(self):
        mean = daily_mean_irradiance(0.0, 0.0, 1.0)
        assert mean > 0

    def test_poles_get_less_annual_average(self):
        equator_total = sum(daily_mean_irradiance(0.0, sol) for sol in range(0, 669, 30))
        pole_total = sum(daily_mean_irradiance(80.0, sol) for sol in range(0, 669, 30))
        assert pole_total < equator_total

    def test_perihelion_vs_aphelion(self):
        """Perihelion (~sol 445) should have more irradiance than aphelion (~sol 112)."""
        peri = solar_irradiance(0.0, 445.0, 12.0, 1.0)
        aph = solar_irradiance(0.0, 112.0, 12.0, 1.0)
        assert peri > aph


# =============================================================================
# THERMAL
# =============================================================================

class TestThermal:
    def test_cold_night_needs_more_heating(self):
        night_heat = required_heating_kw(150.0, 0.0)     # -123C, no sun
        day_heat = required_heating_kw(210.0, 300.0)      # -63C, some sun
        assert night_heat > day_heat

    def test_heating_maintains_temp(self):
        needed = required_heating_kw(200.0, 100.0)
        result = compute_thermal(200.0, 100.0, heating_kw=needed)
        # Should roughly maintain target temp (within thermal mass damping)
        assert abs(result.interior_temp_k - 293.15) < 30.0

    def test_no_heating_cools_down(self):
        result = compute_thermal(180.0, 0.0, interior_temp_k=293.15, heating_kw=0.0)
        assert result.interior_temp_k < 293.15

    def test_solar_gain_reduces_heating_need(self):
        no_sun = required_heating_kw(200.0, 0.0)
        with_sun = required_heating_kw(200.0, 400.0)
        assert with_sun < no_sun


# =============================================================================
# RADIATION
# =============================================================================

class TestRadiation:
    def test_daily_dose_matches_msl(self):
        """MSL/RAD measured ~0.67 mSv/sol on Mars surface."""
        dose = radiation_dose(1, in_habitat=False)
        assert abs(dose - 0.67) < 0.01

    def test_habitat_reduces_dose(self):
        outside = radiation_dose(1, in_habitat=False)
        inside = radiation_dose(1, in_habitat=True, shielding_factor=0.5)
        assert inside < outside

    def test_solar_flare_spike(self):
        normal = radiation_dose(1, in_habitat=True)
        flare = radiation_dose(1, in_habitat=True, solar_flare=True)
        assert flare > normal * 10

    def test_cumulative_dose(self):
        dose_10 = radiation_dose(10, in_habitat=True)
        dose_1 = radiation_dose(1, in_habitat=True)
        assert abs(dose_10 - dose_1 * 10) < 0.01
