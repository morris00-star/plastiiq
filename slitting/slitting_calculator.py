import math


class SlittingCalculator:
    """
    Comprehensive slitting calculator with layer support and material database integration.
    """

    # Define a constant for pi
    PI = math.pi

    # --- CORE ROLL GEOMETRY AND DENSITY CALCULATIONS ---

    @staticmethod
    def calculate_material_thickness_total(layer_thicknesses_um, is_tubular=False):
        """
        Calculates the total effective thickness of the material being slit.
        """
        if not layer_thicknesses_um:
            return 0.0

        total_thickness_um = sum(layer_thicknesses_um)

        if is_tubular:
            # Tubular film means two layers of material per wind (doubles the effective thickness)
            total_thickness_um *= 2

        return total_thickness_um

    @staticmethod
    def calculate_material_density_effective(layer_thicknesses_um, layer_densities_g_cm3):
        """
        Calculates the effective density for laminated materials.
        """
        if not layer_thicknesses_um or not layer_densities_g_cm3:
            return 0.0

        if len(layer_thicknesses_um) == 1:
            # Single layer - return the single density
            return layer_densities_g_cm3[0]

        # Calculate weighted average density for laminated films
        sum_thickness_density = sum(t * d for t, d in zip(layer_thicknesses_um, layer_densities_g_cm3))
        total_thickness = sum(layer_thicknesses_um)

        return sum_thickness_density / total_thickness if total_thickness else 0.0

    @staticmethod
    def calculate_gsm(thickness_um, density_g_cm3):
        """
        Calculate GSM (Grams per Square Meter)
        GSM = thickness in microns × density in g/cm³
        """
        return thickness_um * density_g_cm3

    # --- 1. ROLL RADIUS/DIAMETER FROM ROLL MASS ---

    def calculate_outer_diameter_from_mass(self, roll_mass_kg, core_diameter_m, width_m, thickness_um, density_g_cm3):
        """
        Calculates the final Outer Diameter of a roll given its mass and material properties.
        """
        # Validate inputs
        if roll_mass_kg <= 0 or core_diameter_m <= 0 or width_m <= 0 or thickness_um <= 0 or density_g_cm3 <= 0:
            return 0.0

        # Density conversion: 1 g/cm³ = 1000 kg/m³
        density_kg_m3 = density_g_cm3 * 1000

        # Thickness conversion: 1 µm = 10^-6 m
        thickness_m = thickness_um / 1_000_000

        # Calculate cross-sectional area of the roll (material only, excluding core)
        # Using the formula: Mass = Density × Volume = Density × (Area × Width)
        # So Area = Mass / (Density × Width)
        cross_sectional_area_m2 = roll_mass_kg / (density_kg_m3 * width_m)

        # The cross-sectional area is also: Area = π × (R_outer² - R_core²)
        core_radius_m = core_diameter_m / 2
        core_area_m2 = self.PI * core_radius_m ** 2

        # Total area including core: Area_total = π × R_outer²
        total_area_m2 = cross_sectional_area_m2 + core_area_m2

        # Calculate outer radius
        outer_radius_m = math.sqrt(total_area_m2 / self.PI)
        outer_diameter_m = outer_radius_m * 2

        return outer_diameter_m

    # --- 2. ROLL MASS CALCULATION FROM ROLL RADIUS/DIAMETER ---

    def calculate_roll_mass_from_diameter(self, outer_diameter_m, core_diameter_m, width_m, thickness_um,
                                          density_g_cm3):
        """
        Calculates the mass of a roll given its dimensions and material properties.
        """
        # Validate inputs
        if (outer_diameter_m <= 0 or core_diameter_m <= 0 or width_m <= 0 or
                thickness_um <= 0 or density_g_cm3 <= 0 or outer_diameter_m <= core_diameter_m):
            return 0.0

        outer_radius_m = outer_diameter_m / 2
        core_radius_m = core_diameter_m / 2

        # Thickness conversion: 1 µm = 10^-6 m
        thickness_m = thickness_um / 1_000_000

        # Calculate the cross-sectional area of the material (annular area)
        # Area = π × (R_outer² - R_core²)
        cross_sectional_area_m2 = self.PI * (outer_radius_m ** 2 - core_radius_m ** 2)

        # Calculate volume of material
        volume_m3 = cross_sectional_area_m2 * width_m

        # Density conversion: 1 g/cm³ = 1000 kg/m³
        density_kg_m3 = density_g_cm3 * 1000

        # Calculate mass
        roll_mass_kg = volume_m3 * density_kg_m3

        return roll_mass_kg

    # --- 3. SLITTING TIME, PRODUCTION TIME, AND EFFICIENCY ---

    @staticmethod
    def calculate_slitting_time(roll_length_m, slitting_speed_m_min):
        """
        Calculates the theoretical time required to slit a given length of film.
        """
        if slitting_speed_m_min <= 0:
            return float('inf')

        slitting_time_min = roll_length_m / slitting_speed_m_min
        return slitting_time_min

    @staticmethod
    def calculate_production_efficiency(slitting_time_min, total_run_time_min):
        """
        Calculates the slitting production efficiency.
        """
        if total_run_time_min <= 0:
            return 0.0

        efficiency_percent = (slitting_time_min / total_run_time_min) * 100
        return min(efficiency_percent, 100.0)  # Cap at 100%

    @staticmethod
    def calculate_slitting_production_rate_kg_hr(roll_mass_kg, total_run_time_min):
        """
        Calculates the actual production rate in kilograms per hour.
        """
        if total_run_time_min == 0:
            return 0.0

        rate_kg_min = roll_mass_kg / total_run_time_min
        rate_kg_hr = rate_kg_min * 60
        return rate_kg_hr

    # --- 4. YIELD AND SCRAP CALCULATIONS ---

    @staticmethod
    def calculate_yield_scrap(total_input_kg, good_output_kg):
        """
        Calculates yield percentage and scrap percentage.
        """
        if total_input_kg <= 0:
            return 0.0, 0.0

        yield_percent = (good_output_kg / total_input_kg) * 100
        scrap_percent = 100 - yield_percent

        return min(yield_percent, 100.0), max(scrap_percent, 0.0)

    @staticmethod
    def calculate_film_length_from_mass(mass_kg, width_m, thickness_um, density_g_cm3):
        """
        Calculate film length from mass, width, thickness and density.
        """
        # Validate inputs
        if mass_kg <= 0 or width_m <= 0 or thickness_um <= 0 or density_g_cm3 <= 0:
            return 0.0

        # Convert thickness to meters
        thickness_m = thickness_um / 1_000_000

        # Convert density to kg/m³
        density_kg_m3 = density_g_cm3 * 1000

        # Volume = Mass / Density
        volume_m3 = mass_kg / density_kg_m3

        # Length = Volume / (Width × Thickness)
        if width_m * thickness_m == 0:
            return 0.0

        length_m = volume_m3 / (width_m * thickness_m)
        return length_m

    # --- UNIT CONVERSIONS ---

    @staticmethod
    def convert_length(value, from_unit, to_unit):
        conversions = {
            'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'inch': 0.0254, 'ft': 0.3048
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid length unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    @staticmethod
    def convert_mass(value, from_unit, to_unit):
        conversions = {
            'g': 0.001, 'kg': 1.0, 'lb': 0.453592, 'ton': 1000.0
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid mass unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    @staticmethod
    def convert_thickness(value, from_unit, to_unit='micron'):
        """Convert thickness to microns"""
        to_micron = {
            'micron': 1.0,
            'mm': 1000.0,
            'cm': 10000.0,
            'mil': 25.4,
            'gauge': 0.254  # 1 gauge = 0.254 microns
        }

        if from_unit not in to_micron:
            raise ValueError(f"Invalid thickness unit: {from_unit}")

        value_micron = value * to_micron[from_unit]

        if to_unit != 'micron':
            from_micron = {v: k for k, v in to_micron.items()}
            if to_unit not in from_micron:
                raise ValueError(f"Invalid target thickness unit: {to_unit}")
            return value_micron / to_micron[to_unit]

        return value_micron

    @staticmethod
    def convert_speed(value, from_unit, to_unit):
        conversions = {
            'm_min': 1.0, 'm_hr': 1 / 60.0, 'ft_min': 0.3048, 'ft_hr': 0.3048 / 60.0
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid speed unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]
