class UnitConverter:
    # Length conversions
    LENGTH_CONVERSIONS = {
        'mm_to_cm': 0.1,
        'cm_to_mm': 10,
        'mm_to_inch': 0.0393701,
        'inch_to_mm': 25.4,
        'cm_to_inch': 0.393701,
        'inch_to_cm': 2.54,
        'm_to_cm': 100,
        'cm_to_m': 0.01,
    }

    # Mass conversions
    MASS_CONVERSIONS = {
        'g_to_kg': 0.001,
        'kg_to_g': 1000,
        'g_to_lb': 0.00220462,
        'lb_to_g': 453.592,
    }

    # Thickness conversions
    THICKNESS_CONVERSIONS = {
        'micron_to_mm': 0.001,
        'mm_to_micron': 1000,
        'gauge_to_micron': 0.254,  # 1 gauge = 0.254 microns
        'micron_to_gauge': 3.93701,  # 1 micron = 3.93701 gauge
        'gauge_to_mm': 0.000254,
        'mm_to_gauge': 3937.01,
    }

    # Area conversions
    AREA_CONVERSIONS = {
        'sqm_to_sqft': 10.7639,
        'sqft_to_sqm': 0.092903,
    }

    @classmethod
    def convert_length(cls, value, from_unit, to_unit):
        key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        return value * cls.LENGTH_CONVERSIONS.get(key, 1)

    @classmethod
    def convert_mass(cls, value, from_unit, to_unit):
        key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        return value * cls.MASS_CONVERSIONS.get(key, 1)

    @classmethod
    def convert_thickness(cls, value, from_unit, to_unit):
        key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        return value * cls.THICKNESS_CONVERSIONS.get(key, 1)

    @classmethod
    def convert_area(cls, value, from_unit, to_unit):
        key = f"{from_unit.lower()}_to_{to_unit.lower()}"
        return value * cls.AREA_CONVERSIONS.get(key, 1)
