def biomass_to_co2(biomass_kg):
    """
    Convert biomass (kg) to CO2 equivalent (kg).
    Assumptions:
      - 50% of dry biomass is carbon
      - 1 kg of carbon = 3.67 kg of CO2
    """
    return biomass_kg * 0.5 * 3.67
