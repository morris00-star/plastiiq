import math


class BagMakingCalculator:
    """
    Comprehensive bag making calculator with support for various bag types and units.
    """

    # Unit conversion factors
    LENGTH_CONVERSIONS = {
        'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'inch': 0.0254, 'ft': 0.3048
    }

    MASS_CONVERSIONS = {
        'g': 0.001, 'kg': 1.0, 'lb': 0.453592
    }

    THICKNESS_CONVERSIONS = {
        'micron': 1e-6,
        'mm': 1e-3,
        'cm': 1e-2,
        'm': 1.0,
        'mil': 25.4e-6,
        'gauge': 0.254e-6
    }

    def convert_length(self, value, from_unit, to_unit='m'):
        if from_unit not in self.LENGTH_CONVERSIONS or to_unit not in self.LENGTH_CONVERSIONS:
            raise ValueError(f"Invalid length unit: {from_unit} or {to_unit}")
        return value * self.LENGTH_CONVERSIONS[from_unit] / self.LENGTH_CONVERSIONS[to_unit]

    def convert_mass(self, value, from_unit, to_unit='kg'):
        if from_unit not in self.MASS_CONVERSIONS or to_unit not in self.MASS_CONVERSIONS:
            raise ValueError(f"Invalid mass unit: {from_unit} or {to_unit}")
        return value * self.MASS_CONVERSIONS[from_unit] / self.MASS_CONVERSIONS[to_unit]

    def convert_thickness(self, value, from_unit, to_unit='m'):
        if from_unit not in self.THICKNESS_CONVERSIONS or to_unit not in self.THICKNESS_CONVERSIONS:
            raise ValueError(f"Invalid thickness unit: {from_unit} or {to_unit}")
        return value * self.THICKNESS_CONVERSIONS[from_unit] / self.THICKNESS_CONVERSIONS[to_unit]

    # --- CORE BAG GEOMETRY AND WEIGHT CALCULATIONS ---

    def calculate_gsm_from_thickness(self, thickness_um, density_g_cm3):
        """
        Calculates Grams per Square Meter (GSM) from material thickness and density.
        GSM (g/m²) = Thickness (µm) * Density (g/cm³)
        """
        gsm = thickness_um * density_g_cm3
        return gsm

    def calculate_composite_gsm(self, layers_data):
        """
        Calculate composite GSM for laminated materials.
        layers_data: list of dicts with 'thickness_microns' and 'density_g_cm3'
        """
        total_gsm = 0
        for layer in layers_data:
            total_gsm += self.calculate_gsm_from_thickness(
                layer['thickness_microns'],
                layer['density_g_cm3']
            )
        return total_gsm

    def calculate_single_piece_area(self, width, height, bag_type, gusset_width=0,
                                    width_unit='m', height_unit='m', gusset_unit='m'):
        """
        Calculates the total film area used for a single bag piece.
        """
        # Convert all to meters
        width_m = self.convert_length(width, width_unit, 'm')
        height_m = self.convert_length(height, height_unit, 'm')
        gusset_width_m = self.convert_length(gusset_width, gusset_unit, 'm') if gusset_width else 0

        if bag_type in ['TUBULAR', 'LAMINATED_TUBULAR']:
            # Tubular film: Area = (Width * 2) * Height
            area_m2 = width_m * 2 * height_m
        elif bag_type in ['GUSSETED', 'LAMINATED_GUSSETED']:
            # Gusset bags: Area = (Width + Gusset) * Height
            area_m2 = (width_m + gusset_width_m) * height_m
        else:
            # Flat bags (FLAT_SHEET, LAMINATED_FLAT)
            area_m2 = width_m * height_m

        return area_m2

    def calculate_single_piece_weight(self, area_m2, material_gsm):
        """
        Calculates the mass of a single finished bag piece.
        Mass (g) = Area (m²) * GSM (g/m²)
        """
        single_piece_weight_g = area_m2 * material_gsm
        return single_piece_weight_g

    # --- WEIGHT TO PIECES AND VICE VERSA ---

    def calculate_pieces_to_weight(self, num_pieces, single_piece_weight_g, output_unit='kg'):
        """
        Converts a number of pieces to total weight.
        """
        total_weight_g = num_pieces * single_piece_weight_g
        total_weight_kg = total_weight_g / 1000
        return self.convert_mass(total_weight_kg, 'kg', output_unit)

    def calculate_weight_to_pieces(self, total_weight, single_piece_weight_g, weight_unit='kg'):
        """
        Converts a total weight to the number of pieces.
        """
        if single_piece_weight_g <= 0:
            return 0

        total_weight_kg = self.convert_mass(total_weight, weight_unit, 'kg')
        total_weight_g = total_weight_kg * 1000
        num_pieces = total_weight_g / single_piece_weight_g
        return int(round(num_pieces))

    # --- PACKET AND BUNDLE/BALE WEIGHT ---

    def calculate_packet_weight(self, pieces_per_packet, single_piece_weight_g,
                                packet_packaging_weight=0, packaging_unit='g', output_unit='kg'):
        """
        Calculates the total weight of a packet.
        """
        total_piece_weight_g = pieces_per_packet * single_piece_weight_g
        packet_packaging_weight_g = self.convert_mass(packet_packaging_weight, packaging_unit, 'g')
        packet_weight_g = total_piece_weight_g + packet_packaging_weight_g
        packet_weight_kg = packet_weight_g / 1000
        return self.convert_mass(packet_weight_kg, 'kg', output_unit)

    def calculate_bundle_weight(self, packets_per_bundle, packet_weight_kg,
                                bundle_packaging_weight=0, packaging_unit='kg', output_unit='kg'):
        """
        Calculates the total weight of a bundle or bale.
        """
        bundle_packaging_weight_kg = self.convert_mass(bundle_packaging_weight, packaging_unit, 'kg')
        bundle_weight_kg = (packets_per_bundle * packet_weight_kg) + bundle_packaging_weight_kg
        return self.convert_mass(bundle_weight_kg, 'kg', output_unit)

    def reverse_calculate_from_packet_weight(self, packet_weight, pieces_per_packet,
                                             packet_packaging_weight=0, packaging_unit='g',
                                             weight_unit='kg'):
        """
        Reverse calculation: from packet weight to single piece weight.
        """
        packet_weight_kg = self.convert_mass(packet_weight, weight_unit, 'kg')
        packet_weight_g = packet_weight_kg * 1000
        packet_packaging_weight_g = self.convert_mass(packet_packaging_weight, packaging_unit, 'g')

        total_piece_weight_g = packet_weight_g - packet_packaging_weight_g
        single_piece_weight_g = total_piece_weight_g / pieces_per_packet if pieces_per_packet > 0 else 0

        return single_piece_weight_g

    def reverse_calculate_from_bundle_weight(self, bundle_weight, packets_per_bundle,
                                             bundle_packaging_weight=0, packaging_unit='kg',
                                             weight_unit='kg'):
        """
        Reverse calculation: from bundle weight to packet weight.
        """
        bundle_weight_kg = self.convert_mass(bundle_weight, weight_unit, 'kg')
        bundle_packaging_weight_kg = self.convert_mass(bundle_packaging_weight, packaging_unit, 'kg')

        total_packets_weight_kg = bundle_weight_kg - bundle_packaging_weight_kg
        packet_weight_kg = total_packets_weight_kg / packets_per_bundle if packets_per_bundle > 0 else 0

        return packet_weight_kg

    # --- PRODUCTION METRICS ---

    def calculate_production_time(self, total_pieces, machine_speed_pieces_per_min):
        """
        Calculates the theoretical time required to produce bags.
        """
        if machine_speed_pieces_per_min <= 0:
            return float('inf')

        production_time_min = total_pieces / machine_speed_pieces_per_min
        return production_time_min

    def calculate_yield(self, input_film_mass_kg, output_bag_mass_kg):
        """
        Calculates the material yield for the bag making process.
        """
        if input_film_mass_kg <= 0:
            return 0.0

        yield_percent = (output_bag_mass_kg / input_film_mass_kg) * 100
        return yield_percent

    def calculate_efficiency(self, theoretical_time_min, actual_run_time_min):
        """
        Calculates the operational efficiency.
        """
        if actual_run_time_min <= 0:
            return 0.0

        efficiency_percent = (theoretical_time_min / actual_run_time_min) * 100
        return efficiency_percent

    def calculate_production_rate(self, total_pieces_produced, actual_run_time_min):
        """
        Calculates the actual production rate in pieces per hour.
        """
        if actual_run_time_min == 0:
            return 0.0

        rate_pcs_hr = (total_pieces_produced / actual_run_time_min) * 60
        return rate_pcs_hr
