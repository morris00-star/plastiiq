import math


class PrintingCalculator:
    """
    Comprehensive printing calculations for flexo and gravure solvent-based inks.
    """

    # --- 1. FILM MASS AND LENGTH CALCULATIONS (Based on Density) ---

    @staticmethod
    def calculate_film_mass(width_m, length_m, thickness_um, density_g_cm3):
        """
        Calculates the mass of a film roll using the density formula (Mass = Volume * Density).
        """
        # Convert thickness from µm to m (1 m = 1,000,000 µm)
        thickness_m = thickness_um / 10 ** 6

        # Calculate Volume in cubic meters (m³)
        volume_m3 = width_m * length_m * thickness_m

        # Convert density from g/cm³ to kg/m³
        density_kg_m3 = density_g_cm3 * 1000

        # Calculate Mass in kilograms (kg)
        film_mass_kg = volume_m3 * density_kg_m3

        return film_mass_kg

    @staticmethod
    def calculate_film_length(mass_kg, width_m, thickness_um, density_g_cm3):
        """
        Calculates the length of a film roll by rearranging the mass formula.
        """
        # Calculate GSM from thickness and density
        gsm = PrintingCalculator.calculate_gsm_from_dimensions(thickness_um, density_g_cm3)

        # Convert film mass to grams (g)
        mass_g = mass_kg

        # Calculate Area in square meters (m²)
        area_m2 = mass_g / gsm

        # Calculate Length in meters (m)
        film_length_m = area_m2 / width_m

        return film_length_m

    # --- 2. INK MASS NEEDED (Based on Coverage GSM) ---

    @staticmethod
    def calculate_ink_mass_needed(film_width_m, film_length_m, coverage_percent, ink_coverage_gsm):
        """
        Calculates the total mass of ink required for a printing job.
        """
        # Calculate Total Substrate Area in m²
        total_area_m2 = film_width_m * film_length_m

        # Calculate the Actual Printed Area (where ink is applied) in m²
        printed_area_m2 = total_area_m2 * (coverage_percent / 100)

        # Calculate Actual Ink Mass in grams (g)
        ink_mass_g = printed_area_m2 * ink_coverage_gsm

        # Convert to kilograms (kg)
        ink_mass_kg = ink_mass_g / 1000

        return ink_mass_kg

    @staticmethod
    def calculate_ink_volume(ink_mass_kg, dry_ink_density_g_cm3):
        """
        Calculates the volume of ink from its mass and dry density.
        """
        # Convert ink mass to grams (g)
        ink_mass_g = ink_mass_kg * 1000

        # Convert dry ink density to g/L (1 g/cm³ = 1000 g/L)
        dry_ink_density_g_L = dry_ink_density_g_cm3 * 1000

        # Calculate Volume in Liters (L)
        ink_volume_L = ink_mass_g / dry_ink_density_g_L

        return ink_volume_L

    # --- 3. PRINTING MACHINE SPEED CALCULATION ---

    @staticmethod
    def calculate_machine_speed(length_m, run_time_min):
        """
        Calculates the average machine speed.
        """
        speed_m_min = length_m / run_time_min
        return speed_m_min

    @staticmethod
    def calculate_production_time(total_length_m, machine_speed_m_min):
        """
        Calculates production time for a given length.
        """
        time_minutes = total_length_m / machine_speed_m_min
        time_hours = time_minutes / 60
        return {
            'minutes': time_minutes,
            'hours': time_hours,
            'days': time_hours / 24
        }

    # --- 4. GSM CALCULATIONS (Grams Per Square Meter) ---

    @staticmethod
    def calculate_gsm_from_dimensions(thickness_um, density_g_cm3):
        """
        Calculates theoretical GSM (g/m²) from material thickness and density.
        Correct formula: GSM = Thickness (µm) × Density (g/cm³)
        """
        # Direct calculation: GSM (g/m²) = Thickness (µm) × Density (g/cm³)
        gsm = thickness_um * density_g_cm3
        return gsm

    @staticmethod
    def calculate_gsm_cut_method(sample_mass_g, sample_area_cm2):
        """
        Calculates GSM (g/m²) using the physical cut and weight method.
        """
        # Convert area from cm² to m² (1 m² = 10,000 cm²)
        sample_area_m2 = sample_area_cm2 / 10000

        # GSM (g/m²) = Mass (g) / Area (m²)
        gsm = sample_mass_g / sample_area_m2
        return gsm

    # --- 5. INK MIXING CALCULATIONS ---

    @staticmethod
    def calculate_component_mass(total_mass_kg, percentage):
        """
        Calculate mass of individual component in ink mixing.
        """
        return total_mass_kg * (percentage / 100)

    @staticmethod
    def calculate_solids_percentage(pigment_pct, binder_pct, additives_pct):
        """
        Calculate total solids percentage.
        """
        return pigment_pct + binder_pct + additives_pct

    @staticmethod
    def calculate_viscosity_adjustment(current_viscosity, target_viscosity, current_mass_kg):
        """
        Calculate solvent needed for viscosity adjustment.
        """
        if target_viscosity <= 0:
            return 0
        solvent_added_kg = (current_viscosity / target_viscosity - 1) * current_mass_kg
        return max(solvent_added_kg, 0)  # Ensure non-negative

    @staticmethod
    def calculate_color_strength(pigment_percentage, total_solids_percentage):
        """
        Calculate color strength.
        """
        if total_solids_percentage <= 0:
            return 0
        return (pigment_percentage / total_solids_percentage) * 100

    @staticmethod
    def mix_secondary_color(primary_colors):
        """
        Mix secondary colors from primary CMYK.
        Returns recipe for secondary colors.
        """
        secondary_recipes = {
            'Red': {'Cyan': 0, 'Magenta': 100, 'Yellow': 100, 'Black': 0},
            'Green': {'Cyan': 100, 'Magenta': 0, 'Yellow': 100, 'Black': 0},
            'Blue': {'Cyan': 100, 'Magenta': 100, 'Yellow': 0, 'Black': 0},
            'Orange': {'Cyan': 0, 'Magenta': 50, 'Yellow': 100, 'Black': 0},
            'Purple': {'Cyan': 50, 'Magenta': 100, 'Yellow': 0, 'Black': 0},
            'Brown': {'Cyan': 0, 'Magenta': 75, 'Yellow': 100, 'Black': 25},
        }

        return secondary_recipes

    @staticmethod
    def calculate_ink_mixing_batch(total_batch_kg, formula):
        """
        Calculate individual components for ink mixing batch.
        """
        components = {
            'pigment_kg': PrintingCalculator.calculate_component_mass(total_batch_kg, formula['pigment_pct']),
            'binder_kg': PrintingCalculator.calculate_component_mass(total_batch_kg, formula['binder_pct']),
            'additives_kg': PrintingCalculator.calculate_component_mass(total_batch_kg, formula['additives_pct']),
            'solvent_kg': PrintingCalculator.calculate_component_mass(total_batch_kg, formula['solvent_pct']),
        }

        total_solids = formula['pigment_pct'] + formula['binder_pct'] + formula['additives_pct']
        color_strength = PrintingCalculator.calculate_color_strength(formula['pigment_pct'], total_solids)

        components.update({
            'total_solids_pct': total_solids,
            'color_strength_pct': color_strength,
            'total_batch_kg': total_batch_kg
        })

        return components
