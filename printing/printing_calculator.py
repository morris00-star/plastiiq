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

    # ---------------------------------------------------------------------
    # CMYK FIRST-PRINCIPLES COLOR RECIPES
    #
    # Every color is expressed ONLY as a percentage blend of the 5 real ink
    # stations that exist on a press: Cyan (C), Magenta (M), Yellow (Y),
    # Black/Key (K), and White (W, common 5th station for clear film).
    # No color is ever defined in terms of another named color - each
    # recipe is fully expanded down to C/M/Y/K/W and sums to 100%.
    #
    # Metallics (Gold/Silver/Bronze/Copper) cannot be produced from
    # CMYK+White alone; their 'recipe' is a renormalized CMYK/White hue
    # base for proofing only, with the real metallic pigment tracked
    # separately via metallic_additive_percent.
    # ---------------------------------------------------------------------

    INK_STATION_NAMES = {'C': 'Cyan', 'M': 'Magenta', 'Y': 'Yellow', 'K': 'Black', 'W': 'White'}

    CMYK_COLOR_RECIPES = {
        # Primaries
        'Cyan':    {'category': 'Primary', 'recipe': [('C', 100.0)]},
        'Magenta': {'category': 'Primary', 'recipe': [('M', 100.0)]},
        'Yellow':  {'category': 'Primary', 'recipe': [('Y', 100.0)]},
        'Black':   {'category': 'Primary', 'recipe': [('K', 100.0)]},
        'White':   {'category': 'Primary', 'recipe': [('W', 100.0)]},

        # Secondary (equal-parts 2-primary mix)
        'Red':   {'category': 'Secondary', 'recipe': [('M', 50.0), ('Y', 50.0)]},
        'Green': {'category': 'Secondary', 'recipe': [('C', 50.0), ('Y', 50.0)]},
        'Blue':  {'category': 'Secondary', 'recipe': [('C', 50.0), ('M', 50.0)]},

        # Tertiary (dominant + secondary primary, 2:1 convention)
        'Orange': {'category': 'Tertiary', 'recipe': [('Y', 66.67), ('M', 33.33)]},
        'Purple': {'category': 'Tertiary', 'recipe': [('M', 66.67), ('C', 33.33)]},
        'Teal':   {'category': 'Tertiary', 'recipe': [('C', 66.67), ('Y', 33.33)]},
        'Brown':  {'category': 'Tertiary', 'recipe': [('Y', 50.0), ('M', 37.5), ('C', 12.5)]},
        'Olive':  {'category': 'Tertiary', 'recipe': [('Y', 62.5), ('C', 25.0), ('M', 12.5)]},
        'Maroon': {'category': 'Tertiary', 'recipe': [('M', 60.0), ('Y', 30.0), ('K', 10.0)]},
        'Navy':   {'category': 'Tertiary', 'recipe': [('C', 70.0), ('M', 20.0), ('K', 10.0)]},

        # Tints ("Light" colors): White% + (100-White%) x parent recipe
        'Light Red':    {'category': 'Tint', 'recipe': [('M', 15.0), ('Y', 15.0), ('W', 70.0)]},
        'Light Blue':   {'category': 'Tint', 'recipe': [('C', 12.5), ('M', 12.5), ('W', 75.0)]},
        'Light Green':  {'category': 'Tint', 'recipe': [('C', 10.0), ('Y', 10.0), ('W', 80.0)]},
        'Light Yellow': {'category': 'Tint', 'recipe': [('Y', 40.0), ('W', 60.0)]},
        'Light Orange': {'category': 'Tint', 'recipe': [('Y', 23.33), ('M', 11.67), ('W', 65.0)]},
        'Light Purple': {'category': 'Tint', 'recipe': [('C', 10.0), ('M', 20.0), ('W', 70.0)]},

        # Shades ("Dark" colors): Black% + (100-Black%) x parent recipe
        'Dark Red':    {'category': 'Shade', 'recipe': [('M', 40.0), ('Y', 40.0), ('K', 20.0)]},
        'Dark Blue':   {'category': 'Shade', 'recipe': [('C', 42.5), ('M', 42.5), ('K', 15.0)]},
        'Dark Green':  {'category': 'Shade', 'recipe': [('C', 37.5), ('Y', 37.5), ('K', 25.0)]},
        'Dark Purple': {'category': 'Shade', 'recipe': [('C', 23.33), ('M', 46.67), ('K', 30.0)]},
        'Dark Brown':  {'category': 'Shade', 'recipe': [('C', 11.25), ('M', 33.75), ('Y', 45.0), ('K', 10.0)]},

        # Neutrals
        'Gray':  {'category': 'Neutral', 'recipe': [('K', 15.0), ('W', 85.0)]},
        'Beige': {'category': 'Neutral', 'recipe': [('C', 0.625), ('M', 1.875), ('Y', 12.5), ('W', 85.0)]},
        'Ivory': {'category': 'Neutral', 'recipe': [('Y', 8.0), ('W', 92.0)]},

        # Metallics - hue base only, metallic pigment tracked separately
        'Gold': {'category': 'Metallic', 'recipe': [('Y', 88.89), ('M', 11.11)],
                 'requires_special_ink': True, 'metallic_additive_percent': 10.0,
                 'metallic_name': 'Metallic gold pigment'},
        'Silver': {'category': 'Metallic', 'recipe': [('W', 94.44), ('K', 5.56)],
                   'requires_special_ink': True, 'metallic_additive_percent': 10.0,
                   'metallic_name': 'Metallic silver pigment'},
        'Bronze': {'category': 'Metallic', 'recipe': [('Y', 72.22), ('M', 26.39), ('C', 1.39)],
                   'requires_special_ink': True, 'metallic_additive_percent': 10.0,
                   'metallic_name': 'Metallic bronze pigment'},
        'Copper': {'category': 'Metallic', 'recipe': [('Y', 63.89), ('M', 34.03), ('C', 2.08)],
                   'requires_special_ink': True, 'metallic_additive_percent': 10.0,
                   'metallic_name': 'Metallic copper pigment'},
    }

    @classmethod
    def get_color_recipe(cls, color_name):
        return cls.CMYK_COLOR_RECIPES.get(color_name)

    @classmethod
    def calculate_color_mixing_batch(cls, total_batch_kg, color_name):
        """Resolve a named color into its C/M/Y/K/W component masses for a given batch size."""
        recipe_data = cls.CMYK_COLOR_RECIPES.get(color_name)
        if not recipe_data:
            return None

        components = []
        for station, percent in recipe_data['recipe']:
            components.append({
                'ink_code': station,
                'ink_name': cls.INK_STATION_NAMES[station],
                'percentage': round(percent, 2),
                'mass_kg': round(total_batch_kg * (percent / 100), 6)
            })

        result = {
            'category': recipe_data['category'],
            'components': components,
            'total_batch_kg': total_batch_kg,
            'requires_special_ink': recipe_data.get('requires_special_ink', False)
        }

        if recipe_data.get('requires_special_ink'):
            metallic_pct = recipe_data['metallic_additive_percent']
            result['metallic_name'] = recipe_data['metallic_name']
            result['metallic_additive_percent'] = metallic_pct
            result['metallic_additive_mass_kg'] = round(total_batch_kg * (metallic_pct / 100), 6)

        return result

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

    # ---------------------------------------------------------------------
    # ANILOX INK COVERAGE CROSS-CHECK
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_wet_film_weight_from_anilox(anilox_volume_cm3_m2, transfer_efficiency_percent, ink_density_g_cm3):
        """Wet Film Weight (g/m2) = Anilox Volume (cm3/m2) * Transfer Efficiency% * Ink Density (g/cm3)"""
        return anilox_volume_cm3_m2 * (transfer_efficiency_percent / 100) * ink_density_g_cm3

    # ---------------------------------------------------------------------
    # DOT GAIN / PRINT CONTRAST
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_dot_gain(measured_dot_area_percent, nominal_dot_area_percent):
        """Dot Gain% = Measured Dot Area% - Nominal (plate) Dot Area%"""
        return measured_dot_area_percent - nominal_dot_area_percent

    @staticmethod
    def calculate_print_contrast(solid_density, shadow_density):
        """Print Contrast% = (Solid Density - Shadow Density) / Solid Density * 100"""
        if solid_density <= 0:
            return 0.0
        return ((solid_density - shadow_density) / solid_density) * 100

    # ---------------------------------------------------------------------
    # COLOR DIFFERENCE (DELTA E, CIE76)
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_delta_e_cie76(L1, a1, b1, L2, a2, b2):
        """Delta E (CIE76) = sqrt((L2-L1)^2 + (a2-a1)^2 + (b2-b1)^2)"""
        return math.sqrt((L2 - L1) ** 2 + (a2 - a1) ** 2 + (b2 - b1) ** 2)

    # ---------------------------------------------------------------------
    # REGISTRATION ERROR / REPEAT LENGTH DEVIATION
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_registration_error(measured_position_mm, target_position_mm):
        """Registration Error (mm) = |Measured Position - Target Position|"""
        return abs(measured_position_mm - target_position_mm)

    @staticmethod
    def calculate_repeat_length_deviation(actual_repeat_mm, cylinder_circumference_mm):
        """Repeat Length Deviation% = (Actual Repeat - Cylinder Circumference) / Cylinder Circumference * 100"""
        if cylinder_circumference_mm <= 0:
            return 0.0
        return ((actual_repeat_mm - cylinder_circumference_mm) / cylinder_circumference_mm) * 100

    # ---------------------------------------------------------------------
    # RESIDUAL SOLVENT
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_residual_solvent(solvent_detected_ug, sample_area_m2):
        """Residual Solvent (mg/m2) = Solvent Detected (ug) / Sample Area (m2) / 1000"""
        if sample_area_m2 <= 0:
            return 0.0
        return solvent_detected_ug / sample_area_m2 / 1000

    # ---------------------------------------------------------------------
    # WASTE ALLOWANCE (MASS PLANNING)
    # ---------------------------------------------------------------------

    @staticmethod
    def apply_waste_allowance(net_mass_kg, waste_percent):
        """Gross Required Mass = Net Mass * (1 + Waste% / 100)"""
        waste_mass_kg = net_mass_kg * (waste_percent / 100)
        gross_mass_kg = net_mass_kg + waste_mass_kg
        return {'net_kg': net_mass_kg, 'waste_kg': waste_mass_kg, 'gross_kg': gross_mass_kg}

    # ---------------------------------------------------------------------
    # LINE SPEED VS DRYING/CURING CAPACITY
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_max_safe_speed(dryer_length_m, required_dwell_time_min):
        """Max Safe Speed (m/min) = Dryer/Oven Length (m) / Required Dwell Time (min)"""
        if required_dwell_time_min <= 0:
            return 0.0
        return dryer_length_m / required_dwell_time_min

    # ---------------------------------------------------------------------
    # ROTOGRAVURE CYLINDER COVERAGE & INK CONSUMPTION
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_cylinder_circumference(diameter_mm):
        """Circumference (mm) = pi * Cylinder Diameter (mm)"""
        return math.pi * diameter_mm

    @staticmethod
    def calculate_cylinder_surface_area(diameter_m, face_width_m):
        """Surface Area (m2) = pi * Diameter (m) * Face Width (m)"""
        return math.pi * diameter_m * face_width_m

    @staticmethod
    def calculate_cylinder_revolutions(job_length_m, circumference_m):
        """Revolutions = Job Length (m) / Cylinder Circumference (m)"""
        if circumference_m <= 0:
            return 0.0
        return job_length_m / circumference_m

    @staticmethod
    def calculate_cylinder_coverage_percent(image_area_m2, total_surface_area_m2):
        """Coverage% = (Engraved/Image Area (m2) / Total Cylinder Surface Area (m2)) * 100"""
        if total_surface_area_m2 <= 0:
            return 0.0
        return (image_area_m2 / total_surface_area_m2) * 100

    @staticmethod
    def calculate_ink_volume_per_revolution(cell_volume_cm3_m2, image_area_m2):
        """Ink Volume (cm3) = Cell Volume (cm3/m2) * Image Area (m2) - only engraved area carries ink"""
        return cell_volume_cm3_m2 * image_area_m2

    @staticmethod
    def calculate_ink_mass_per_revolution(ink_volume_cm3, ink_density_g_cm3):
        """Ink Mass (g) = Ink Volume (cm3) * Ink Density (g/cm3)"""
        return ink_volume_cm3 * ink_density_g_cm3

    @staticmethod
    def calculate_total_ink_consumption(ink_mass_per_rev_g, revolutions):
        """Total Ink (kg) = Ink Mass per Revolution (g) * Revolutions / 1000"""
        return (ink_mass_per_rev_g * revolutions) / 1000

    # ---------------------------------------------------------------------
    # CYLINDER WEAR / LIFE PLANNING
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_cell_volume_depletion(original_cell_volume, current_cell_volume):
        """Cell Volume Loss% = ((Original - Current) / Original) * 100"""
        if original_cell_volume <= 0:
            return 0.0
        return ((original_cell_volume - current_cell_volume) / original_cell_volume) * 100

    @staticmethod
    def calculate_max_job_length_per_cylinder_life(rated_life_revolutions, circumference_m):
        """Max Job Length per Cylinder (m) = Rated Cylinder Life (revolutions) * Circumference (m)"""
        return rated_life_revolutions * circumference_m
