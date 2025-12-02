import math


class SlittingCalculator:
    """
    Comprehensive slitting calculator with core weight calculations and layer support.
    """

    # Define a constant for pi
    PI = math.pi

    # Default core material properties (if not using CoreMaterial model)
    DEFAULT_CORE_PROPERTIES = {
        'paper': {'density_g_cm3': 0.75, 'wall_thickness_mm': 1.5},
        'plastic': {'density_g_cm3': 0.95, 'wall_thickness_mm': 2.0},
        'steel': {'density_g_cm3': 7.85, 'wall_thickness_mm': 1.0}
    }

    # --- CORE WEIGHT CALCULATIONS ---

    @staticmethod
    def calculate_core_weight_from_dimensions(core_diameter_m, core_width_m,
                                              core_wall_thickness_mm=1.5,
                                              core_material_density_g_cm3=0.75):
        """
        Calculate core weight from core dimensions.

        Args:
            core_diameter_m: Outer diameter of core in meters
            core_width_m: Width of core in meters
            core_wall_thickness_mm: Wall thickness in millimeters
            core_material_density_g_cm3: Density of core material in g/cm³

        Returns:
            Core weight in kilograms
        """
        if core_diameter_m <= 0 or core_width_m <= 0 or core_wall_thickness_mm <= 0:
            return 0.0

        # Convert wall thickness to meters
        wall_thickness_m = core_wall_thickness_mm / 1000

        # Calculate inner diameter
        inner_diameter_m = core_diameter_m - (2 * wall_thickness_m)

        # If inner diameter is negative or zero, it's a solid core
        if inner_diameter_m <= 0:
            # Calculate as solid cylinder
            outer_radius_m = core_diameter_m / 2
            cross_sectional_area_m2 = SlittingCalculator.PI * outer_radius_m ** 2
        else:
            # Calculate as hollow cylinder
            outer_radius_m = core_diameter_m / 2
            inner_radius_m = inner_diameter_m / 2
            cross_sectional_area_m2 = SlittingCalculator.PI * (outer_radius_m ** 2 - inner_radius_m ** 2)

        # Calculate volume
        volume_m3 = cross_sectional_area_m2 * core_width_m

        # Convert density to kg/m³
        density_kg_m3 = core_material_density_g_cm3 * 1000

        # Calculate weight
        core_weight_kg = volume_m3 * density_kg_m3

        return core_weight_kg

    @staticmethod
    def calculate_core_weight_provided(provided_core_weight, provided_core_weight_unit='kg'):
        """
        Convert provided core weight to kg.

        Args:
            provided_core_weight: Core weight in provided unit
            provided_core_weight_unit: Unit of provided weight

        Returns:
            Core weight in kilograms
        """
        if provided_core_weight <= 0:
            return 0.0

        # Convert to kg
        conversions = {
            'g': 0.001,
            'kg': 1.0,
            'lb': 0.453592,
            'ton': 1000.0
        }

        if provided_core_weight_unit not in conversions:
            raise ValueError(f"Invalid weight unit: {provided_core_weight_unit}")

        return provided_core_weight * conversions[provided_core_weight_unit]

    # --- CORE DIMENSIONS CALCULATIONS (Reverse Engineering) ---

    @staticmethod
    def calculate_core_wall_thickness_from_weight(core_weight_kg, core_diameter_m, core_width_m,
                                                  core_material_density_g_cm3=0.75):
        """
        Calculate core wall thickness from core weight and dimensions.

        Args:
            core_weight_kg: Core weight in kg
            core_diameter_m: Outer diameter in meters
            core_width_m: Width in meters
            core_material_density_g_cm3: Density of core material

        Returns:
            Wall thickness in millimeters
        """
        if core_weight_kg <= 0 or core_diameter_m <= 0 or core_width_m <= 0:
            return 1.5  # Return default

        # Convert density
        density_kg_m3 = core_material_density_g_cm3 * 1000

        # Calculate total volume
        volume_m3 = core_weight_kg / density_kg_m3

        # Calculate cross-sectional area
        cross_sectional_area_m2 = volume_m3 / core_width_m

        # Calculate inner radius from: A = π(R² - r²)
        outer_radius_m = core_diameter_m / 2
        inner_radius_squared = outer_radius_m ** 2 - (cross_sectional_area_m2 / SlittingCalculator.PI)

        if inner_radius_squared <= 0:
            # Solid core
            return core_diameter_m / 2 * 1000  # Convert to mm

        inner_radius_m = math.sqrt(inner_radius_squared)
        wall_thickness_m = outer_radius_m - inner_radius_m

        return wall_thickness_m * 1000  # Convert to mm

    # --- UPDATED ROLL MASS CALCULATION WITH CORE WEIGHT ---

    def calculate_roll_mass_from_diameter_with_core(self, outer_diameter_m, core_diameter_m, width_m,
                                                    thickness_um, density_g_cm3,
                                                    core_weight_kg=None,
                                                    core_calculation_method='dimensions',
                                                    core_wall_thickness_mm=1.5,
                                                    core_material_density_g_cm3=0.75,
                                                    provided_core_weight=None,
                                                    provided_core_weight_unit='kg'):
        """
        Calculates roll mass with core weight consideration.

        Args:
            outer_diameter_m: Roll outer diameter in meters
            core_diameter_m: Core outer diameter in meters
            width_m: Roll width in meters
            thickness_um: Material thickness in microns
            density_g_cm3: Material density in g/cm³
            core_weight_kg: Pre-calculated core weight (if None, will calculate)
            core_calculation_method: 'dimensions' or 'provided'
            core_wall_thickness_mm: Core wall thickness (for dimension method)
            core_material_density_g_cm3: Core material density
            provided_core_weight: Provided core weight (for provided method)
            provided_core_weight_unit: Unit of provided core weight

        Returns:
            Dictionary with gross_weight_kg, core_weight_kg, net_weight_kg
        """
        # Validate inputs
        if (outer_diameter_m <= 0 or core_diameter_m <= 0 or width_m <= 0 or
                thickness_um <= 0 or density_g_cm3 <= 0 or outer_diameter_m <= core_diameter_m):
            return {
                'gross_weight_kg': 0.0,
                'core_weight_kg': 0.0,
                'net_weight_kg': 0.0
            }

        # Calculate core weight based on method
        if core_weight_kg is not None:
            # Use pre-calculated core weight
            calculated_core_weight_kg = core_weight_kg
            weight_source = 'precalculated'
        elif core_calculation_method == 'provided' and provided_core_weight is not None:
            # Use provided weight
            calculated_core_weight_kg = self.calculate_core_weight_provided(
                provided_core_weight, provided_core_weight_unit
            )
            weight_source = 'provided'
        else:
            # Calculate from dimensions
            calculated_core_weight_kg = self.calculate_core_weight_from_dimensions(
                core_diameter_m, width_m, core_wall_thickness_mm, core_material_density_g_cm3
            )
            weight_source = 'calculated'

        # Calculate material mass (without core) - using existing function
        material_mass_kg = self.calculate_roll_mass_from_diameter(
            outer_diameter_m, core_diameter_m, width_m, thickness_um, density_g_cm3
        )

        # Calculate total roll mass
        gross_weight_kg = material_mass_kg + calculated_core_weight_kg

        return {
            'gross_weight_kg': gross_weight_kg,
            'core_weight_kg': calculated_core_weight_kg,
            'net_weight_kg': material_mass_kg,
            'weight_source': weight_source,
            'material_mass_kg': material_mass_kg
        }

    # --- UPDATED ROLL DIAMETER CALCULATION WITH CORE WEIGHT ---

    def calculate_outer_diameter_from_mass_with_core(self, gross_mass_kg, core_diameter_m, width_m,
                                                     thickness_um, density_g_cm3,
                                                     core_weight_kg=None,
                                                     core_calculation_method='dimensions',
                                                     core_wall_thickness_mm=1.5,
                                                     core_material_density_g_cm3=0.75,
                                                     provided_core_weight=None,
                                                     provided_core_weight_unit='kg'):
        """
        Calculates roll outer diameter considering core weight.

        Args:
            gross_mass_kg: Total roll mass including core in kg
            core_diameter_m: Core outer diameter in meters
            width_m: Roll width in meters
            thickness_um: Material thickness in microns
            density_g_cm3: Material density in g/cm³
            core_weight_kg: Pre-calculated core weight (if None, will calculate)
            core_calculation_method: 'dimensions' or 'provided'
            core_wall_thickness_mm: Core wall thickness (for dimension method)
            core_material_density_g_cm3: Core material density
            provided_core_weight: Provided core weight (for provided method)
            provided_core_weight_unit: Unit of provided core weight

        Returns:
            Dictionary with outer_diameter_m and weight breakdown
        """
        # Validate inputs
        if (gross_mass_kg <= 0 or core_diameter_m <= 0 or width_m <= 0 or
                thickness_um <= 0 or density_g_cm3 <= 0):
            return {
                'outer_diameter_m': 0.0,
                'core_weight_kg': 0.0,
                'net_weight_kg': 0.0,
                'material_mass_kg': 0.0
            }

        # Calculate core weight
        if core_weight_kg is not None:
            calculated_core_weight_kg = core_weight_kg
            weight_source = 'precalculated'
        elif core_calculation_method == 'provided' and provided_core_weight is not None:
            calculated_core_weight_kg = self.calculate_core_weight_provided(
                provided_core_weight, provided_core_weight_unit
            )
            weight_source = 'provided'
        else:
            calculated_core_weight_kg = self.calculate_core_weight_from_dimensions(
                core_diameter_m, width_m, core_wall_thickness_mm, core_material_density_g_cm3
            )
            weight_source = 'calculated'

        # Calculate net material mass
        net_material_mass_kg = gross_mass_kg - calculated_core_weight_kg

        if net_material_mass_kg <= 0:
            # Core weight is greater than or equal to gross weight
            return {
                'outer_diameter_m': core_diameter_m,
                'core_weight_kg': calculated_core_weight_kg,
                'net_weight_kg': 0.0,
                'material_mass_kg': 0.0,
                'weight_source': weight_source,
                'warning': 'Core weight exceeds total roll weight'
            }

        # Calculate outer diameter from net material mass
        outer_diameter_m = self.calculate_outer_diameter_from_mass(
            net_material_mass_kg, core_diameter_m, width_m, thickness_um, density_g_cm3
        )

        return {
            'outer_diameter_m': outer_diameter_m,
            'core_weight_kg': calculated_core_weight_kg,
            'net_weight_kg': net_material_mass_kg,
            'material_mass_kg': net_material_mass_kg,
            'weight_source': weight_source
        }

    # --- COMPREHENSIVE ROLL ANALYSIS FUNCTION ---

    def analyze_roll_comprehensive(self, **kwargs):
        """
        Comprehensive roll analysis with all weight calculations.

        Args can include:
        - For mass from diameter: outer_diameter, core_diameter, width, thickness, density
        - For diameter from mass: gross_mass, core_diameter, width, thickness, density
        - Core parameters: core_method, core_wall_thickness, core_density, provided_core_weight

        Returns complete analysis dictionary
        """
        calculation_type = kwargs.get('calculation_type', 'mass_from_diameter')

        if calculation_type == 'mass_from_diameter':
            result = self.calculate_roll_mass_from_diameter_with_core(**kwargs)

            # Calculate additional metrics
            if result['gross_weight_kg'] > 0:
                result['core_weight_percentage'] = (result['core_weight_kg'] / result['gross_weight_kg']) * 100
                result['material_weight_percentage'] = (result['net_weight_kg'] / result['gross_weight_kg']) * 100

                # Calculate roll density (average density of entire roll)
                outer_radius_m = kwargs.get('outer_diameter_m', 0) / 2
                core_radius_m = kwargs.get('core_diameter_m', 0) / 2
                width_m = kwargs.get('width_m', 1)

                total_volume_m3 = SlittingCalculator.PI * (outer_radius_m ** 2) * width_m
                core_volume_m3 = SlittingCalculator.PI * (core_radius_m ** 2) * width_m

                if total_volume_m3 > 0:
                    result['average_density_g_cm3'] = (result['gross_weight_kg'] * 1000) / (total_volume_m3 * 1000000)
                else:
                    result['average_density_g_cm3'] = 0

            return result

        elif calculation_type == 'diameter_from_mass':
            result = self.calculate_outer_diameter_from_mass_with_core(**kwargs)

            # Calculate additional metrics if outer diameter is valid
            if result['outer_diameter_m'] > kwargs.get('core_diameter_m', 0):
                outer_radius_m = result['outer_diameter_m'] / 2
                core_radius_m = kwargs.get('core_diameter_m', 0) / 2
                width_m = kwargs.get('width_m', 1)

                total_volume_m3 = SlittingCalculator.PI * (outer_radius_m ** 2) * width_m
                core_volume_m3 = SlittingCalculator.PI * (core_radius_m ** 2) * width_m

                if total_volume_m3 > 0:
                    result['average_density_g_cm3'] = (kwargs.get('gross_mass_kg', 0) * 1000) / (
                                total_volume_m3 * 1000000)
                else:
                    result['average_density_g_cm3'] = 0

            return result

        else:
            raise ValueError(f"Invalid calculation type: {calculation_type}")

    # --- HELPER FUNCTIONS FOR CORE VALIDATION ---

    @staticmethod
    def validate_core_dimensions(core_diameter_m, core_width_m, min_diameter_m=0.05, min_width_m=0.1):
        """
        Validate core dimensions against typical minimums.

        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        errors = []

        if core_diameter_m < min_diameter_m:
            warnings.append(f"Core diameter ({core_diameter_m * 1000:.1f}mm) is unusually small")

        if core_width_m < min_width_m:
            warnings.append(f"Core width ({core_width_m * 1000:.1f}mm) is unusually narrow")

        # Aspect ratio check
        aspect_ratio = core_width_m / core_diameter_m
        if aspect_ratio > 10:
            warnings.append(f"Core aspect ratio ({aspect_ratio:.1f}) is unusually high")
        elif aspect_ratio < 0.5:
            warnings.append(f"Core aspect ratio ({aspect_ratio:.1f}) is unusually low")

        return {
            'is_valid': len(errors) == 0,
            'warnings': warnings,
            'errors': errors
        }

    @staticmethod
    def get_core_weight_summary(core_weight_kg, gross_weight_kg):
        """
        Generate a summary of core weight impact.
        """
        if gross_weight_kg <= 0:
            return {
                'impact': 'N/A',
                'description': 'Invalid weight values'
            }

        percentage = (core_weight_kg / gross_weight_kg) * 100

        if percentage < 1:
            return {
                'impact': 'Very Low',
                'description': f'Core represents only {percentage:.1f}% of total weight'
            }
        elif percentage < 5:
            return {
                'impact': 'Low',
                'description': f'Core represents {percentage:.1f}% of total weight'
            }
        elif percentage < 15:
            return {
                'impact': 'Moderate',
                'description': f'Core represents {percentage:.1f}% of total weight'
            }
        elif percentage < 30:
            return {
                'impact': 'High',
                'description': f'Core represents {percentage:.1f}% of total weight (significant)'
            }
        else:
            return {
                'impact': 'Very High',
                'description': f'Core represents {percentage:.1f}% of total weight (core dominates)'
            }

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
