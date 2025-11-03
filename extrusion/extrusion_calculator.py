import math
import statistics


class ExtrusionCalculator:
    """
    Comprehensive film extrusion calculator with unit conversions.
    """

    def __init__(self, density_g_cm3=0.92):
        self.DENSITY_G_CM3 = density_g_cm3
        self.DENSITY_KG_M3 = density_g_cm3 * 1000.0

    # ---------------------------------------------------------------------
    # UNIT CONVERSIONS - ADD MISSING METHODS
    # ---------------------------------------------------------------------

    def convert_length(self, value, from_unit, to_unit):
        conversions = {
            'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'inch': 0.0254, 'ft': 0.3048
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid length unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    def convert_mass(self, value, from_unit, to_unit):
        conversions = {
            'g': 0.001, 'kg': 1.0, 'lb': 0.453592, 'ton': 1000.0
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid mass unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    def convert_to_meters(self, value, unit):
        """Convert various thickness units to meters"""
        conversions = {
            'micron': 1e-6,
            'mm': 1e-3,
            'cm': 1e-2,
            'm': 1.0,
            'mil': 25.4e-6,
            'gauge': 0.254e-6
        }
        if unit not in conversions:
            raise ValueError(f"Invalid thickness unit: {unit}")
        return value * conversions[unit]

    def convert_speed(self, value, from_unit, to_unit):
        conversions = {
            'm_min': 1.0, 'm_hr': 1 / 60.0, 'ft_min': 0.3048, 'ft_hr': 0.3048 / 60.0
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid speed unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    def convert_force(self, value, from_unit, to_unit):
        conversions = {
            'N': 1.0, 'kN': 1000.0, 'lbf': 4.44822, 'kgf': 9.80665
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid force unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    def convert_mass_flow(self, value, from_unit, to_unit):
        conversions = {
            'kg_hr': 1.0, 'kg_min': 60.0, 'lb_hr': 0.453592, 'g_hr': 0.001
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid mass flow unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    # ADD THIS METHOD FOR AREA CONVERSION
    def convert_area(self, value, from_unit, to_unit):
        """Convert area units"""
        conversions = {
            'm2_kg': 1.0,
            'm2_lb': 2.20462,  # 1 kg = 2.20462 lb, so m²/lb = m²/kg * 2.20462
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid area unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    # ---------------------------------------------------------------------
    # ADDITIONAL CALCULATION METHODS
    # ---------------------------------------------------------------------

    def calc_weight_from_length(self, length_m, width_m, thickness_m):
        """Calculate weight from film dimensions"""
        volume = length_m * width_m * thickness_m
        return volume * self.DENSITY_KG_M3

    def calc_roll_radius(self, core_diameter_m, thickness_m, roll_length_m):
        """Calculate outer radius from roll length"""
        if thickness_m <= 0:
            return core_diameter_m / 2

        # Using the formula: L = π * (R² - r²) / thickness
        # Solve for R: R = sqrt((L * thickness / π) + r²)
        core_radius = core_diameter_m / 2
        area_contribution = (roll_length_m * thickness_m) / math.pi
        outer_radius = math.sqrt(area_contribution + core_radius ** 2)
        return outer_radius

    def calc_roll_radius_from_mass(self, core_diameter_m, thickness_m, width_m, total_mass_kg, core_weight_kg=0):
        """Calculate outer radius from total mass"""
        if thickness_m <= 0 or width_m <= 0:
            return core_diameter_m / 2

        # Calculate film mass (excluding core)
        film_mass_kg = total_mass_kg - core_weight_kg
        if film_mass_kg <= 0:
            return core_diameter_m / 2

        # Calculate roll length from mass: L = mass / (density * width * thickness)
        roll_length_m = film_mass_kg / (self.DENSITY_KG_M3 * width_m * thickness_m)

        # Now calculate radius from length
        return self.calc_roll_radius(core_diameter_m, thickness_m, roll_length_m)

    # ---------------------------------------------------------------------
    # MULTI-LAYER FILM CALCULATION
    # ---------------------------------------------------------------------

    @staticmethod
    def calc_composite_density(layer_densities_g_cm3, layer_thicknesses_microns):
        if len(layer_densities_g_cm3) != len(layer_thicknesses_microns):
            raise ValueError("Each layer must have a matching density and thickness")
        total_weight = sum(d * t for d, t in zip(layer_densities_g_cm3, layer_thicknesses_microns))
        total_thickness = sum(layer_thicknesses_microns)
        return total_weight / total_thickness if total_thickness > 0 else 0.0

    # ---------------------------------------------------------------------
    # FILM THICKNESS AND MASS
    # ---------------------------------------------------------------------

    def calc_thickness_cut_and_weigh(self, mass_kg, length_m, width_m):
        area = length_m * width_m
        return mass_kg / (self.DENSITY_KG_M3 * area) if area else 0.0

    def calc_thickness_from_rate(self, mass_flow_rate_kghr, width_m, take_up_speed_m_min):
        mf_kg_s = mass_flow_rate_kghr / 3600
        speed_m_s = take_up_speed_m_min / 60
        return mf_kg_s / (self.DENSITY_KG_M3 * width_m * speed_m_s) if width_m and speed_m_s else 0.0

    def calc_mass_total(self, thickness_m, length_m, width_m):
        return thickness_m * length_m * width_m * self.DENSITY_KG_M3

    def calc_mass_per_piece(self, thickness_m, piece_length_m, piece_width_m):
        return self.calc_mass_total(thickness_m, piece_length_m, piece_width_m) * 2

    def calc_number_of_pieces(self, total_mass_kg, mass_per_piece_kg):
        return math.floor(total_mass_kg / mass_per_piece_kg) if mass_per_piece_kg else 0

    def calc_yield(self, thickness_m):
        return 1 / (self.DENSITY_KG_M3 * thickness_m) if thickness_m else 0

    def calc_basis_weight(self, thickness_m):
        return self.DENSITY_KG_M3 * thickness_m * 1000

    # ---------------------------------------------------------------------
    # BLOWN FILM METRICS
    # ---------------------------------------------------------------------

    def calc_blow_up_ratio(self, lay_flat_width_m, die_diameter_m):
        return (2 * lay_flat_width_m) / (math.pi * die_diameter_m) if die_diameter_m else 0

    def calc_draw_down_ratio(self, die_gap_m, final_thickness_m, bur):
        return die_gap_m / (final_thickness_m * bur) if final_thickness_m and bur else 0

    def calc_extrusion_rate(self, line_speed_m_min, lay_flat_width_m, thickness_m):
        vol_flow_m3_min = thickness_m * lay_flat_width_m * line_speed_m_min
        return vol_flow_m3_min * self.DENSITY_KG_M3 * 60

    # ---------------------------------------------------------------------
    # ROLL AND PRODUCTION
    # ---------------------------------------------------------------------

    def calc_roll_length_from_od(self, od_m, id_m, thickness_m):
        return (math.pi / (4 * thickness_m)) * (od_m ** 2 - id_m ** 2) if thickness_m else 0

    def calc_roll_mass(self, roll_length_m, film_width_m, thickness_m, core_weight_kg=0.0):
        film_mass = roll_length_m * film_width_m * thickness_m * self.DENSITY_KG_M3
        return film_mass + core_weight_kg

    def calc_film_length_from_weight(self, film_weight_kg, film_width_m, thickness_m):
        denom = self.DENSITY_KG_M3 * film_width_m * thickness_m
        return film_weight_kg / denom if denom else 0

    def calc_production_time_for_quantity(self, quantity_required, rate_kghr):
        return quantity_required / rate_kghr if rate_kghr else float("inf")

    def calc_new_take_up_speed(self, old_speed_m_min, old_thickness_m, new_thickness_m):
        return old_speed_m_min * (old_thickness_m / new_thickness_m) if new_thickness_m else 0

    # ---------------------------------------------------------------------
    # QUALITY CONTROL TESTS
    # ---------------------------------------------------------------------

    @staticmethod
    def calc_gauge_variation_cv(thickness_measurements_microns):
        if not thickness_measurements_microns:
            return 0.0
        avg = statistics.mean(thickness_measurements_microns)
        return (statistics.stdev(thickness_measurements_microns) / avg) * 100 if avg else float("inf")

    @staticmethod
    def calc_tensile_strength(max_load_N, width_m, thickness_m):
        area = width_m * thickness_m
        return (max_load_N / area) / 1e6 if area else 0.0

    @staticmethod
    def calc_percent_elongation(L0_m, Lf_m):
        return ((Lf_m - L0_m) / L0_m) * 100 if L0_m else float("inf")

    @staticmethod
    def calc_coefficient_of_friction(F_f, F_n):
        return F_f / F_n if F_n else 0

    @staticmethod
    def calc_dart_impact_m50(weights_g, results_pass_fail):
        fails = [w for w, r in zip(weights_g, results_pass_fail) if not r]
        return statistics.mean(fails) if fails else max(weights_g) if weights_g else 0
