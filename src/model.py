# src/model.py
import numpy as np

def biomass_to_co2(biomass_kg, carbon_fraction=0.47):
    """
    Convert total biomass (kg) to CO2 equivalent (kg).
    CO2 = biomass * CF * 3.67
    """
    return biomass_kg * carbon_fraction * 3.67

def agb_from_chave(dbh_cm, height_m, wood_density_g_cm3):
    """
    Chave et al. (2014) moist forest AGB (kg):
    AGB = 0.0673 * (ρ * D^2 * H) ^ 0.976
    D in cm, H in m, ρ in g/cm^3
    """
    return 0.0673 * (wood_density_g_cm3 * (dbh_cm**2) * height_m) ** 0.976

def total_biomass_kg(agb_kg, root_to_shoot_ratio=0.27):
    """
    Total biomass = AGB + BGB; BGB = R * AGB
    """
    return agb_kg * (1.0 + root_to_shoot_ratio)

