class LaminationCalculator:
    """
    Comprehensive lamination calculator for plastic film manufacturing.
    """

    # Default adhesive system configurations
    DEFAULT_ADHESIVE_SYSTEMS = {
        'SOLVENTLESS': {
            'name': 'Solventless (Default)',
            'hardener': {'name': 'Brilliant S621 (NCO)', 'solids': 1.00},
            'adhesive': {'name': 'Brilliant 2S79 (OH)', 'solids': 1.00},
            'mix_ratio': {'A': 100, 'B': 10, 'C': 0},  # A: Adhesive, B: Hardener, C: Solvent
            'is_solvent_based': False
        },
        'SOLVENT_BASE': {
            'name': 'Solvent Base (Default)',
            'hardener': {'name': 'Brilliant H414 (NCO)', 'solids': 0.60},
            'adhesive': {'name': 'Brilliant A405 (OH)', 'solids': 1.00},
            'mix_ratio': {'A': 100, 'B': 10, 'C': 50},  # A: Adhesive, B: Hardener, C: Solvent
            'is_solvent_based': True
        },
        'CUSTOM_SOLVENTLESS': {
            'name': 'Custom Solventless',
            'hardener': {'name': 'Custom Hardener', 'solids': 1.00},
            'adhesive': {'name': 'Custom Adhesive', 'solids': 1.00},
            'mix_ratio': {'A': 100, 'B': 10, 'C': 0},
            'is_solvent_based': False
        },
        'CUSTOM_SOLVENT_BASE': {
            'name': 'Custom Solvent Base',
            'hardener': {'name': 'Custom Hardener', 'solids': 0.60},
            'adhesive': {'name': 'Custom Adhesive', 'solids': 1.00},
            'mix_ratio': {'A': 100, 'B': 10, 'C': 50},
            'is_solvent_based': True
        }
    }

    def get_adhesive_system(self, adhesive_type, custom_ratio_a=None, custom_ratio_b=None, custom_ratio_c=None,
                            custom_adhesive_solids=None, custom_hardener_solids=None,
                            custom_adhesive_name=None, custom_hardener_name=None):
        """
        Get adhesive system configuration, applying custom values if provided.
        """
        if adhesive_type not in self.DEFAULT_ADHESIVE_SYSTEMS:
            raise ValueError(f"Unknown adhesive type: {adhesive_type}")

        system = self.DEFAULT_ADHESIVE_SYSTEMS[adhesive_type].copy()

        # Apply custom values
        if custom_ratio_a is not None and custom_ratio_b is not None and custom_ratio_c is not None:
            system['mix_ratio'] = {
                'A': float(custom_ratio_a),
                'B': float(custom_ratio_b),
                'C': float(custom_ratio_c)
            }

        if custom_adhesive_solids is not None:
            system['adhesive']['solids'] = float(custom_adhesive_solids) / 100.0

        if custom_hardener_solids is not None:
            system['hardener']['solids'] = float(custom_hardener_solids) / 100.0

        if custom_adhesive_name:
            system['adhesive']['name'] = custom_adhesive_name

        if custom_hardener_name:
            system['hardener']['name'] = custom_hardener_name

        return system

    def calculate_adhesive_component_weights(self, adhesive_type, total_mass_kg, coat_weight_gsm,
                                             total_film_gsm, custom_ratio_a=None, custom_ratio_b=None,
                                             custom_ratio_c=None,
                                             custom_adhesive_solids=None, custom_hardener_solids=None,
                                             custom_adhesive_name=None, custom_hardener_name=None):
        """
        Calculates the weights of adhesive components with support for custom ratios.
        Includes solvent (Part C) in the ratio for solvent-based systems.
        """
        # Get the adhesive system with custom values applied
        system = self.get_adhesive_system(
            adhesive_type, custom_ratio_a, custom_ratio_b, custom_ratio_c,
            custom_adhesive_solids, custom_hardener_solids,
            custom_adhesive_name, custom_hardener_name
        )

        component_mix_ratio = system['mix_ratio']
        component_solids = {
            'A': system['adhesive']['solids'],
            'B': system['hardener']['solids'],
            'C': 0.0  # Solvent has 0% solids
        }
        is_solvent_based = system['is_solvent_based']

        # Calculate total area from total mass and GSM
        total_laminate_gsm = total_film_gsm + coat_weight_gsm

        if total_laminate_gsm <= 0:
            return {
                'Resin_A_kg': 0.0,
                'Hardener_B_kg': 0.0,
                'Ethyl_Acetate_kg': 0.0,
                'Adhesive_System': system['adhesive']['name'],
                'Hardener_System': system['hardener']['name'],
                'Dry_Adhesive_Mass_kg': 0.0,
                'Total_Area_m2': 0.0,
                'Mix_Ratio': f"{component_mix_ratio['A']}:{component_mix_ratio['B']}:{component_mix_ratio['C']}",
                'Is_Custom': custom_ratio_a is not None or custom_adhesive_solids is not None
            }

        total_area_m2 = (total_mass_kg * 1000) / total_laminate_gsm

        # Total Dry Adhesive Mass (g) = Coat Weight (g/m²) * Total Area (m²)
        total_dry_mass_g = coat_weight_gsm * total_area_m2
        total_dry_mass_kg = total_dry_mass_g / 1000

        # Total Solids Content calculation
        ratio_sum = component_mix_ratio['A'] + component_mix_ratio['B'] + component_mix_ratio['C']
        wet_A_ratio = component_mix_ratio['A'] / ratio_sum
        wet_B_ratio = component_mix_ratio['B'] / ratio_sum
        wet_C_ratio = component_mix_ratio['C'] / ratio_sum

        dry_A_ratio = wet_A_ratio * component_solids['A']
        dry_B_ratio = wet_B_ratio * component_solids['B']
        dry_C_ratio = wet_C_ratio * component_solids['C']
        total_solids_fraction = dry_A_ratio + dry_B_ratio + dry_C_ratio

        if total_solids_fraction == 0:
            return {
                'Resin_A_kg': 0.0,
                'Hardener_B_kg': 0.0,
                'Ethyl_Acetate_kg': 0.0,
                'Adhesive_System': system['adhesive']['name'],
                'Hardener_System': system['hardener']['name'],
                'Dry_Adhesive_Mass_kg': total_dry_mass_kg,
                'Total_Area_m2': total_area_m2,
                'Mix_Ratio': f"{component_mix_ratio['A']}:{component_mix_ratio['B']}:{component_mix_ratio['C']}",
                'Is_Custom': custom_ratio_a is not None or custom_adhesive_solids is not None
            }

        # Total Wet Adhesive Mass
        total_wet_mass_kg = total_dry_mass_kg / total_solids_fraction

        # Component Weights (Wet)
        wet_A_kg = total_wet_mass_kg * wet_A_ratio
        wet_B_kg = total_wet_mass_kg * wet_B_ratio
        wet_C_kg = total_wet_mass_kg * wet_C_ratio

        # For solvent-based systems, the solvent is part of the ratio
        # For solventless systems, solvent should be 0
        if is_solvent_based:
            ethyl_acetate_kg = wet_C_kg
        else:
            ethyl_acetate_kg = 0.0

        return {
            'Resin_A_kg': round(wet_A_kg, 3),
            'Hardener_B_kg': round(wet_B_kg, 3),
            'Ethyl_Acetate_kg': round(ethyl_acetate_kg, 3),
            'Adhesive_System': system['adhesive']['name'],
            'Hardener_System': system['hardener']['name'],
            'Dry_Adhesive_Mass_kg': round(total_dry_mass_kg, 3),
            'Total_Area_m2': round(total_area_m2, 2),
            'Mix_Ratio': f"{component_mix_ratio['A']}:{component_mix_ratio['B']}:{component_mix_ratio['C']}",
            'Is_Custom': custom_ratio_a is not None or custom_adhesive_solids is not None,
            'Solids_Content': {
                'adhesive': component_solids['A'],
                'hardener': component_solids['B'],
                'solvent': component_solids['C']
            }
        }

    @staticmethod
    def calculate_gsm_from_dimensions(thickness_um, density_g_cm3):
        """
        Calculates Grams per Square Meter (GSM) from material thickness and density.
        GSM (g/m²) = (Thickness (µm) * Density (g/cm³))
        """
        gsm = thickness_um * density_g_cm3
        return gsm

    @staticmethod
    def calculate_layer_mass_from_total(total_mass_kg, total_laminate_gsm, layer_gsm):
        """
        Calculates the mass of a single component within a laminate based on its proportional GSM.
        Mass_layer = Total_Mass * (Layer_GSM / Total_Laminate_GSM)
        """
        if total_laminate_gsm == 0:
            return 0.0
        layer_mass_kg = total_mass_kg * (layer_gsm / total_laminate_gsm)
        return layer_mass_kg

    def calculate_laminate_weight_breakdown(self, total_mass_kg, layer_data, adhesive_gsm_per_layer):
        """
        Calculates the mass contribution of each film and adhesive layer in a laminate.
        layer_data: list of dicts with 'material_name', 'gsm', 'thickness_microns'
        adhesive_gsm_per_layer: GSM of adhesive per bonding layer
        """
        film_gsm_list = [layer['gsm'] for layer in layer_data]
        total_film_gsm = sum(film_gsm_list)

        # Calculate adhesive GSM: (n-1) times the adhesive_gsm_per_layer for n layers
        number_of_layers = len(layer_data)
        total_adhesive_gsm = adhesive_gsm_per_layer * (number_of_layers - 1)

        total_laminate_gsm = total_film_gsm + total_adhesive_gsm

        # Calculate mass for each individual layer
        layer_masses = []
        for layer in layer_data:
            layer_mass_kg = self.calculate_layer_mass_from_total(total_mass_kg, total_laminate_gsm, layer['gsm'])
            layer_masses.append({
                'material_name': layer['material_name'],
                'thickness_microns': layer['thickness_microns'],
                'gsm': layer['gsm'],
                'mass_kg': layer_mass_kg,
                'mass_percent': (layer_mass_kg / total_mass_kg) * 100 if total_mass_kg > 0 else 0
            })

        # Calculate adhesive mass
        total_adhesive_mass_kg = self.calculate_layer_mass_from_total(total_mass_kg, total_laminate_gsm,
                                                                      total_adhesive_gsm)

        total_film_mass_kg = sum(layer['mass_kg'] for layer in layer_masses)

        return {
            'layer_masses': layer_masses,
            'total_film_mass_kg': total_film_mass_kg,
            'total_adhesive_mass_kg': total_adhesive_mass_kg,
            'total_film_gsm': total_film_gsm,
            'total_adhesive_gsm': total_adhesive_gsm,
            'total_laminate_gsm': total_laminate_gsm,
            'number_of_layers': number_of_layers,
            'adhesive_layers_count': number_of_layers - 1,
            'adhesive_gsm_per_layer': adhesive_gsm_per_layer
        }

    # --- LAMINATION TIME, EFFICIENCY, AND YIELD ---

    @staticmethod
    def calculate_lamination_time(roll_length_m, machine_speed_m_min):
        """Calculates theoretical lamination time."""
        if machine_speed_m_min <= 0:
            return float('inf')
        lamination_time_min = roll_length_m / machine_speed_m_min
        return lamination_time_min

    @staticmethod
    def calculate_production_efficiency(lamination_time_min, total_run_time_min):
        """Calculates production efficiency."""
        if total_run_time_min <= 0:
            return 0.0
        efficiency_percent = (lamination_time_min / total_run_time_min) * 100
        return efficiency_percent

    @staticmethod
    def calculate_production_rate_kg_hr(total_mass_produced_kg, total_run_time_min):
        """Calculates production rate in kg/hr."""
        if total_run_time_min == 0:
            return 0.0
        rate_kg_hr = (total_mass_produced_kg / total_run_time_min) * 60
        return rate_kg_hr

    @staticmethod
    def calculate_yield(input_film_mass_kg, output_laminate_mass_kg):
        """Calculates material yield percentage."""
        if input_film_mass_kg <= 0:
            return 0.0
        yield_percent = (output_laminate_mass_kg / input_film_mass_kg) * 100
        return yield_percent

    # Unit Conversion Methods
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
            'g': 0.001, 'kg': 1.0, 'lb': 0.453592
        }
        if from_unit not in conversions or to_unit not in conversions:
            raise ValueError(f"Invalid mass unit: {from_unit} or {to_unit}")
        return value * conversions[from_unit] / conversions[to_unit]

    @staticmethod
    def convert_to_microns(value, unit):
        conversions = {
            'micron': 1.0,
            'mm': 1000.0,
            'cm': 10000.0,
            'mil': 25.4,
            'gauge': 0.254
        }
        if unit not in conversions:
            raise ValueError(f"Invalid thickness unit: {unit}")
        return value * conversions[unit]

    @staticmethod
    def convert_speed(value, from_unit, to_unit):
        """Convert speed between different units"""
        conversions = {
            'm_min': 1.0,
            'm_hr': 1 / 60.0,
            'ft_min': 0.3048,
            'ft_hr': 0.3048 / 60.0
        }
        if from_unit in conversions and to_unit in conversions:
            return value * conversions[from_unit] / conversions[to_unit]
        return value  # Fallback to same value if units not recognized
