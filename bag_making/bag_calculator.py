import math
from typing import List, Dict, Any, Optional


class BagMakingCalculator:
    """
    Comprehensive bag making calculator with support for various bag types and units.
    Includes flap option for tubular bags, zipper and handle add-ons, and gusset positioning.
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

    def convert_length(self, value: float, from_unit: str, to_unit: str = 'm') -> float:
        """Convert length between units"""
        if from_unit not in self.LENGTH_CONVERSIONS or to_unit not in self.LENGTH_CONVERSIONS:
            raise ValueError(f"Invalid length unit: {from_unit} or {to_unit}")
        return value * self.LENGTH_CONVERSIONS[from_unit] / self.LENGTH_CONVERSIONS[to_unit]

    def convert_mass(self, value: float, from_unit: str, to_unit: str = 'kg') -> float:
        """Convert mass between units"""
        if from_unit not in self.MASS_CONVERSIONS or to_unit not in self.MASS_CONVERSIONS:
            raise ValueError(f"Invalid mass unit: {from_unit} or {to_unit}")
        return value * self.MASS_CONVERSIONS[from_unit] / self.MASS_CONVERSIONS[to_unit]

    def convert_thickness(self, value: float, from_unit: str, to_unit: str = 'm') -> float:
        """Convert thickness between units"""
        if from_unit not in self.THICKNESS_CONVERSIONS or to_unit not in self.THICKNESS_CONVERSIONS:
            raise ValueError(f"Invalid thickness unit: {from_unit} or {to_unit}")
        return value * self.THICKNESS_CONVERSIONS[from_unit] / self.THICKNESS_CONVERSIONS[to_unit]

    # --- CORE BAG GEOMETRY AND WEIGHT CALCULATIONS ---

    def calculate_gsm_from_thickness(self, thickness_um: float, density_g_cm3: float) -> float:
        """
        Calculates Grams per Square Meter (GSM) from material thickness and density.
        GSM (g/m²) = Thickness (µm) * Density (g/cm³)
        """
        return thickness_um * density_g_cm3

    def calculate_composite_gsm(self, layers_data: List[Dict[str, Any]]) -> float:
        """
        Calculate composite GSM for laminated materials.
        layers_data: list of dicts with 'thickness_microns' and 'density_g_cm3'
        """
        total_gsm = 0
        for layer in layers_data:
            # Convert thickness to microns if needed
            thickness_um = layer['thickness_microns']
            if layer.get('thickness_unit') and layer['thickness_unit'] != 'micron':
                thickness_m = self.convert_thickness(
                    layer['thickness_microns'],
                    layer['thickness_unit'],
                    'm'
                )
                thickness_um = thickness_m * 1e6

            total_gsm += self.calculate_gsm_from_thickness(
                thickness_um,
                layer['density_g_cm3']
            )
        return total_gsm

    def calculate_single_piece_area(
            self,
            width: float,
            height: float,
            bag_type: str,
            gusset_width: float = 0,
            gusset_type: str = 'side',
            flap_length: float = 0,
            width_unit: str = 'm',
            height_unit: str = 'm',
            gusset_unit: str = 'm',
            flap_unit: str = 'm'
    ) -> float:
        """
        Calculates the total film area used for a single bag piece.
        Supports different bag types with proper geometry.
        """
        # Convert all to meters
        width_m = self.convert_length(width, width_unit, 'm')
        height_m = self.convert_length(height, height_unit, 'm')
        gusset_m = self.convert_length(gusset_width, gusset_unit, 'm') if gusset_width else 0
        flap_m = self.convert_length(flap_length, flap_unit, 'm') if flap_length else 0

        # Handle different bag types
        if bag_type in ['TUBULAR', 'LAMINATED_TUBULAR']:
            # Tubular film: Area = (Width * 2) * Height
            area_m2 = width_m * 2 * height_m

        elif bag_type in ['TUBULAR_WITH_FLAP', 'LAMINATED_TUBULAR_FLAP']:
            # Tubular with flap: Area = (Width * 2) * (Height + Flap/2)
            # Flap adds half its length to the height for the front side only
            effective_height = height_m + (flap_m / 2)
            area_m2 = width_m * 2 * effective_height

        elif bag_type in ['GUSSETED_SIDE', 'LAMINATED_GUSSETED_SIDE']:
            # Side gusseted: Total width = Width + Gusset (both sides)
            # Area = (Width + Gusset) * Height
            area_m2 = (width_m + gusset_m) * height_m * 2

        elif bag_type in ['GUSSETED_BOTTOM', 'LAMINATED_GUSSETED_BOTTOM']:
            # Bottom gusseted: Total length = Height + Gusset
            # Area = Width * (Height + Gusset)
            area_m2 = width_m * (height_m + gusset_m) * 2

        elif bag_type in ['GUSSETED_BOTTOM_FLAP', 'LAMINATED_GUSSETED_BOTTOM_FLAP']:
            # Bottom gusseted with flap: combines the bottom-gusset extra length with
            # the flap's half-length addition (same convention as TUBULAR_WITH_FLAP)
            # Area = Width * (Height + Gusset + Flap/2)
            effective_height = height_m + gusset_m + (flap_m / 2)
            area_m2 = width_m * effective_height * 2

        else:
            # Flat bags (FLAT_SHEET, LAMINATED_FLAT)
            area_m2 = width_m * height_m

        return area_m2

    def calculate_single_piece_weight(
            self,
            area_m2: float,
            material_gsm: float,
            addon_weight_g: float = 0
    ) -> float:
        """
        Calculates the mass of a single finished bag piece including add-ons.
        Mass (g) = Area (m²) * GSM (g/m²) + Addon Weight (g)
        """
        bag_weight_g = area_m2 * material_gsm
        total_weight_g = bag_weight_g + addon_weight_g
        return total_weight_g

    # --- ADD-ON CALCULATIONS ---

    def calculate_addon_weight(
            self,
            zipper_data: Optional[Dict[str, Any]] = None,
            handle_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate total add-on weight for zippers and handles.

        For zipper: weight = length * weight_per_unit_length
        For handles: weight = number_of_handles * weight_per_handle
        """
        total_addon_weight_g = 0

        if zipper_data and zipper_data.get('enabled'):
            zipper_length = zipper_data.get('length', 0)
            length_unit = zipper_data.get('length_unit', 'cm')
            weight_per_cm = zipper_data.get('weight_per_cm', 0)

            # Convert length to cm for calculation
            if length_unit != 'cm':
                length_cm = self.convert_length(zipper_length, length_unit, 'cm')
            else:
                length_cm = zipper_length

            zipper_weight = length_cm * weight_per_cm
            total_addon_weight_g += zipper_weight

        if handle_data and handle_data.get('enabled'):
            num_handles = handle_data.get('quantity', 2)
            weight_per_handle = handle_data.get('weight_per_handle_g', 0)

            handle_weight = num_handles * weight_per_handle
            total_addon_weight_g += handle_weight

        return total_addon_weight_g

    def reverse_calculate_zipper_weight(
            self,
            total_addon_weight_g: float,
            zipper_length: float,
            length_unit: str = 'cm',
            num_handles: int = 0,
            handle_weight_g: float = 0
    ) -> Dict[str, Any]:
        """
        Reverse calculate zipper weight per cm or handle weight from total add-on weight.
        """
        result = {}

        # Convert zipper length to cm
        if zipper_length > 0:
            length_cm = self.convert_length(zipper_length, length_unit, 'cm')

            if num_handles > 0 and handle_weight_g > 0:
                # Both zipper and handles present
                total_handle_weight = num_handles * handle_weight_g
                zipper_weight = total_addon_weight_g - total_handle_weight
                if length_cm > 0:
                    result['zipper_weight_per_cm'] = round(zipper_weight / length_cm, 4)
                    result['zipper_total_weight_g'] = round(zipper_weight, 2)
                result['handle_total_weight_g'] = round(total_handle_weight, 2)
                result['handle_weight_per_handle_g'] = handle_weight_g

            elif length_cm > 0:
                # Only zipper
                result['zipper_weight_per_cm'] = round(total_addon_weight_g / length_cm, 4)
                result['zipper_total_weight_g'] = round(total_addon_weight_g, 2)

            elif num_handles > 0:
                # Only handles
                result['handle_weight_per_handle_g'] = round(total_addon_weight_g / num_handles, 4)
                result['handle_total_weight_g'] = round(total_addon_weight_g, 2)

        return result

    # --- WEIGHT TO PIECES AND VICE VERSA ---

    def calculate_pieces_to_weight(
            self,
            num_pieces: int,
            single_piece_weight_g: float,
            output_unit: str = 'kg'
    ) -> float:
        """Converts a number of pieces to total weight."""
        total_weight_g = num_pieces * single_piece_weight_g
        total_weight_kg = total_weight_g / 1000
        return self.convert_mass(total_weight_kg, 'kg', output_unit)

    def calculate_weight_to_pieces(
            self,
            total_weight: float,
            single_piece_weight_g: float,
            weight_unit: str = 'kg'
    ) -> int:
        """Converts a total weight to the number of pieces."""
        if single_piece_weight_g <= 0:
            return 0

        total_weight_kg = self.convert_mass(total_weight, weight_unit, 'kg')
        total_weight_g = total_weight_kg * 1000
        num_pieces = total_weight_g / single_piece_weight_g
        return int(round(num_pieces))

    # --- PACKET AND BUNDLE/BALE WEIGHT ---

    def calculate_packet_weight(
            self,
            pieces_per_packet: int,
            single_piece_weight_g: float,
            packet_packaging_weight: float = 0,
            packaging_unit: str = 'g',
            output_unit: str = 'kg'
    ) -> Dict[str, Any]:
        """Calculates the total weight of a packet including packaging."""
        # Convert all to grams first
        total_piece_weight_g = pieces_per_packet * single_piece_weight_g
        packet_packaging_weight_g = self.convert_mass(packet_packaging_weight, packaging_unit, 'kg') * 1000

        # Calculate gross and net weights
        gross_weight_g = total_piece_weight_g + packet_packaging_weight_g
        net_weight_g = total_piece_weight_g

        # Calculate packaging percentage
        packaging_percentage = (packet_packaging_weight_g / gross_weight_g * 100) if gross_weight_g > 0 else 0

        # Convert to output unit
        gross_weight_output = self.convert_mass(gross_weight_g / 1000, 'kg', output_unit)
        net_weight_output = self.convert_mass(net_weight_g / 1000, 'kg', output_unit)
        packaging_weight_output = self.convert_mass(packet_packaging_weight_g / 1000, 'kg', output_unit)

        return {
            'gross_weight': round(gross_weight_output, 4),
            'net_weight': round(net_weight_output, 4),
            'packaging_weight': round(packet_packaging_weight_g, 4),
            'packaging_percentage': round(packaging_percentage, 4),
            'total_piece_weight_g': round(total_piece_weight_g, 4),
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'pieces_per_packet': pieces_per_packet,
            'output_unit': output_unit,
            'packaging_unit': 'g'
        }

    def calculate_bundle_weight(
            self,
            packets_per_bundle: int,
            packet_weight_kg: float,
            bundle_packaging_weight: float = 0,
            packaging_unit: str = 'kg',
            output_unit: str = 'kg'
    ) -> Dict[str, Any]:
        """Calculates the total weight of a bundle or bale including packaging."""
        # Convert all to kilograms
        bundle_packaging_weight_kg = self.convert_mass(bundle_packaging_weight, packaging_unit, 'kg')

        # Calculate net and gross weights
        net_bundle_weight_kg = packets_per_bundle * packet_weight_kg
        gross_bundle_weight_kg = net_bundle_weight_kg + bundle_packaging_weight_kg

        # Calculate packaging percentage
        packaging_percentage = (
                    bundle_packaging_weight_kg / gross_bundle_weight_kg * 100) if gross_bundle_weight_kg > 0 else 0

        # Convert to output unit
        gross_bundle_weight_output = self.convert_mass(gross_bundle_weight_kg, 'kg', output_unit)
        net_bundle_weight_output = self.convert_mass(net_bundle_weight_kg, 'kg', output_unit)
        packaging_weight_output = self.convert_mass(bundle_packaging_weight_kg, 'kg', output_unit)

        return {
            'gross_weight': round(gross_bundle_weight_output, 4),
            'net_weight': round(net_bundle_weight_output, 4),
            'packaging_weight': round(bundle_packaging_weight_kg, 4),
            'packaging_percentage': round(packaging_percentage, 2),
            'net_packets_weight_kg': round(net_bundle_weight_kg, 4),
            'packet_weight_kg': round(packet_weight_kg, 4),
            'packets_per_bundle': packets_per_bundle,
            'output_unit': output_unit,
            'packaging_unit': 'kg'
        }

    def reverse_calculate_from_packet_weight(
            self,
            packet_weight: float,
            pieces_per_packet: int,
            packet_packaging_weight: float = 0,
            packaging_unit: str = 'g',
            weight_unit: str = 'kg'
    ) -> Dict[str, Any]:
        """Reverse calculation: from packet gross weight to single piece weight."""
        # Convert packet weight to grams
        packet_weight_kg = self.convert_mass(packet_weight, weight_unit, 'kg')
        packet_weight_g = packet_weight_kg * 1000

        # Convert packaging weight to grams
        packet_packaging_weight_g = self.convert_mass(packet_packaging_weight, packaging_unit, 'kg') * 1000

        # Calculate net bag weight
        net_bag_weight_g = packet_weight_g - packet_packaging_weight_g

        # Calculate single piece weight
        single_piece_weight_g = net_bag_weight_g / pieces_per_packet if pieces_per_packet > 0 else 0

        # Calculate packaging percentage
        packaging_percentage = (packet_packaging_weight_g / packet_weight_g * 100) if packet_weight_g > 0 else 0

        return {
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'net_bag_weight_g': round(net_bag_weight_g, 4),
            'gross_packet_weight_g': round(packet_weight_g, 4),
            'packaging_weight_g': round(packet_packaging_weight_g, 4),
            'packaging_percentage': round(packaging_percentage, 4),
            'pieces_per_packet': pieces_per_packet
        }

    def reverse_calculate_from_bundle_weight(
            self,
            bundle_weight: float,
            packets_per_bundle: int,
            bundle_packaging_weight: float = 0,
            packaging_unit: str = 'kg',
            weight_unit: str = 'kg'
    ) -> Dict[str, Any]:
        """Reverse calculation: from bundle gross weight to packet weight."""
        bundle_weight_kg = self.convert_mass(bundle_weight, weight_unit, 'kg')
        bundle_packaging_weight_kg = self.convert_mass(bundle_packaging_weight, packaging_unit, 'kg')

        # Calculate net packets weight
        net_packets_weight_kg = bundle_weight_kg - bundle_packaging_weight_kg

        # Calculate packet weight
        packet_weight_kg = net_packets_weight_kg / packets_per_bundle if packets_per_bundle > 0 else 0

        # Calculate packaging percentage
        packaging_percentage = (bundle_packaging_weight_kg / bundle_weight_kg * 100) if bundle_weight_kg > 0 else 0

        return {
            'packet_weight_kg': round(packet_weight_kg, 4),
            'net_packets_weight_kg': round(net_packets_weight_kg, 4),
            'gross_bundle_weight_kg': round(bundle_weight_kg, 4),
            'packaging_weight_kg': round(bundle_packaging_weight_kg, 4),
            'packaging_percentage': round(packaging_percentage, 2),
            'packets_per_bundle': packets_per_bundle
        }

    # --- PRODUCTION METRICS ---

    def calculate_production_time(self, total_pieces: int, machine_speed_pieces_per_min: float) -> float:
        """Calculates the theoretical time required to produce bags."""
        if machine_speed_pieces_per_min <= 0:
            return float('inf')
        return total_pieces / machine_speed_pieces_per_min

    def calculate_yield(self, input_film_mass_kg: float, output_bag_mass_kg: float) -> float:
        """Calculates the material yield for the bag making process."""
        if input_film_mass_kg <= 0:
            return 0.0
        return (output_bag_mass_kg / input_film_mass_kg) * 100

    def calculate_efficiency(self, theoretical_time_min: float, actual_run_time_min: float) -> float:
        """Calculates the operational efficiency."""
        if actual_run_time_min <= 0:
            return 0.0
        return (theoretical_time_min / actual_run_time_min) * 100

    def calculate_production_rate(self, total_pieces_produced: int, actual_run_time_min: float) -> float:
        """Calculates the actual production rate in pieces per hour."""
        if actual_run_time_min == 0:
            return 0.0
        return (total_pieces_produced / actual_run_time_min) * 60

    # ---------------------------------------------------------------------
    # ACCESSORY & CUT-OUT WEIGHT CALCULATIONS
    # (see accessories_and_cutouts spec for full derivation and business rules)
    # ---------------------------------------------------------------------

    # Configurable default coefficients / fixed weights - all override-able per calculation
    ACCESSORY_DEFAULTS = {
        'ZIPPER_18MM': {'label': '18mm x 100mm Zipper', 'Cz_g_per_100mm': 0.72},
        'ZIPPER_14MM': {'label': '14mm x 100mm Zipper', 'Cz_g_per_100mm': 0.50},
        'TAPE_TEMPORARY': {'label': 'Temporary Adhesive Tape (18mm x 100mm)', 'Ct_g_per_100mm': 0.05},
        'TAPE_PERMANENT_10MM': {'label': 'Permanent Adhesive Tape (10mm x 100mm)', 'Ct_g_per_100mm': 0.14},
        'TAPE_PERMANENT_18MM': {'label': 'Permanent Adhesive Tape (18mm x 100mm)', 'Ct_g_per_100mm': 0.252},
        'SPOUT_ASSEMBLY': {'label': 'Spout Assembly (Spout + Cap)', 'weight_g': 2.99},
        'CARRY_HANDLE': {'label': 'Plastic Carry Handle (Injection-Molded)', 'weight_g': 8.03},
        'LOOP_HANDLE': {'label': 'Plastic Loop Handle (LDPE)', 'weight_g': 1.26},
        'BREATHER_VENT': {'label': 'Breather / Vent', 'weight_g': 0.59},
    }

    CARRY_HANDLE_DPUNCH_NAME = 'D Punch (30mm x 75mm)'  # the D Punch always deducted before adding a Carry Handle

    @staticmethod
    def calculate_cutout_k(area_cm2, density_g_cm3, layers=2):
        """K (g/um) = (rho x A x L) / 10000"""
        return (density_g_cm3 * area_cm2 * layers) / 10000

    @staticmethod
    def calculate_cutout_weight(k_g_per_um, thickness_um):
        """Cut-Out Weight (g) = K x Film Thickness (um)"""
        return k_g_per_um * thickness_um

    @staticmethod
    def back_calculate_area(mass_g, density_g_cm3, layers, thickness_um):
        """
        A (cm2) = (Mass x 10000) / (rho x L x Thickness)
        Used once to derive a new die geometry's stored Area from a physical sample -
        not used again afterward, since the resulting Area is then persisted.
        """
        denom = density_g_cm3 * layers * thickness_um
        if denom <= 0:
            return 0.0
        return (mass_g * 10000) / denom

    def calculate_zipper_weight(self, bag_width_mm, cz_g_per_100mm):
        """Zipper Weight (g) = (Bag Width mm / 100) x Cz"""
        return (bag_width_mm / 100) * cz_g_per_100mm

    def calculate_tape_weight(self, tape_length_mm, ct_g_per_100mm):
        """Tape Weight (g) = (Tape Length mm / 100) x Ct"""
        return (tape_length_mm / 100) * ct_g_per_100mm

    # ---------------------------------------------------------------------
    # BAG FILL VOLUME / CAPACITY
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_gusseted_bag_volume_cm3(width_cm, gusset_cm, height_cm):
        """Box approximation: Volume (cm3) = Width x Gusset x Height"""
        return width_cm * gusset_cm * height_cm

    @staticmethod
    def calculate_flat_bag_volume_cm3(width_cm, height_cm):
        """Elliptical cross-section approximation: Volume (cm3) = (Width^2 x Height) / pi"""
        return (width_cm ** 2 * height_cm) / math.pi

    @staticmethod
    def calculate_fill_weight_from_volume(volume_liters, bulk_density_kg_m3):
        """Fill Weight (kg) = Volume (L) x Density (kg/L); Density kg/L = Density kg/m3 / 1000"""
        density_kg_l = bulk_density_kg_m3 / 1000
        return volume_liters * density_kg_l

    @staticmethod
    def calculate_volume_needed_for_weight(target_weight_kg, bulk_density_kg_m3):
        """Reverse: Volume (L) = Target Weight (kg) / Density (kg/L)"""
        density_kg_l = bulk_density_kg_m3 / 1000
        if density_kg_l <= 0:
            return 0.0
        return target_weight_kg / density_kg_l

    # ---------------------------------------------------------------------
    # BAGS PER ROLL / ROLL REQUIREMENT
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_bag_repeat_length(height_m, seal_allowance_m=0.003):
        """Bag Repeat Length (m) = Height + Seal/Trim Allowance"""
        return height_m + seal_allowance_m

    @staticmethod
    def calculate_bags_per_roll(roll_length_m, bag_repeat_length_m):
        """Bags per Roll = floor(Roll Length / Bag Repeat Length)"""
        if bag_repeat_length_m <= 0:
            return 0
        return math.floor(roll_length_m / bag_repeat_length_m)

    @staticmethod
    def calculate_rolls_required(total_bags_needed, bags_per_roll):
        """Rolls Required = ceil(Total Bags Needed / Bags per Roll)"""
        if bags_per_roll <= 0:
            return 0
        return math.ceil(total_bags_needed / bags_per_roll)

    @staticmethod
    def calculate_total_film_length_required(total_bags_needed, bag_repeat_length_m):
        """Total Film Length Required (m) = Total Bags Needed x Bag Repeat Length"""
        return total_bags_needed * bag_repeat_length_m

    @staticmethod
    def calculate_roll_length_from_diameter(outer_radius_m, core_radius_m, thickness_m):
        """Roll Length (m) = pi x (Outer Radius^2 - Core Radius^2) / Thickness - same convention as Extrusion/Slitting"""
        if thickness_m <= 0:
            return 0.0
        return math.pi * (outer_radius_m ** 2 - core_radius_m ** 2) / thickness_m

    # ---------------------------------------------------------------------
    # HEAT SEAL STRENGTH
    # ---------------------------------------------------------------------

    @staticmethod
    def calculate_seal_strength(seal_force_n, sample_width_mm, standard_width_mm=15.0):
        """Seal Strength (N/15mm) = Seal Force (N) / (Sample Width mm / 15) - same convention as Lamination's Peel Strength"""
        if sample_width_mm <= 0:
            return 0.0
        return seal_force_n / (sample_width_mm / standard_width_mm)

    # ---------------------------------------------------------------------
    # BIN LINER SIZING
    # Designs a bag spec from bin dimensions, per the Bin Liner Sizing spec.
    # All internal math is done in INCHES (the spec's native unit); callers
    # convert at the boundary.
    # ---------------------------------------------------------------------

    IN3_PER_LITRE = 61.024
    BIN_LINER_DEFAULT_FILL_FACTOR = 0.55
    BIN_LINER_DEFAULT_FW_OVERLAP_IN = 3.0

    @staticmethod
    def bin_liner_overhang_in(capacity_liters):
        """Overhang by bin size: <=30L -> 3in, 31-120L -> 5in, 121L+ -> 7in"""
        if capacity_liters <= 30:
            return 3.0
        elif capacity_liters <= 120:
            return 5.0
        return 7.0

    @classmethod
    def bin_liner_volume_to_in3(cls, liters):
        return liters * cls.IN3_PER_LITRE

    @classmethod
    def bin_liner_in3_to_liters(cls, in3):
        return in3 / cls.IN3_PER_LITRE

    @classmethod
    def bin_liner_dims_from_volume(cls, liters, shape):
        """
        Derive bin dimensions when only volume is given.
        Round:       V = pi x (D/2)^2 x H, assuming D = 0.55 x H
        Square/Rect: V = Wb x Db x Hb,     assuming Wb = Db = 0.55 x Hb
        Returns dict of inches.
        """
        v_in3 = cls.bin_liner_volume_to_in3(liters)

        if shape == 'ROUND':
            # V = pi x (0.55H/2)^2 x H = pi x 0.075625 x H^3
            h = (v_in3 / (math.pi * (0.55 / 2) ** 2)) ** (1 / 3)
            return {'diameter_in': 0.55 * h, 'height_in': h}

        # V = (0.55H)^2 x H = 0.3025 x H^3
        h = (v_in3 / (0.55 ** 2)) ** (1 / 3)
        w = 0.55 * h
        return {'bin_width_in': w, 'bin_depth_in': w, 'bin_height_in': h}

    @classmethod
    def bin_liner_volume_from_dims(cls, shape, diameter_in=0, height_in=0,
                                    bin_width_in=0, bin_depth_in=0, bin_height_in=0):
        """Bin's own geometric volume in litres, from its dimensions."""
        if shape == 'ROUND':
            v_in3 = math.pi * (diameter_in / 2) ** 2 * height_in
        else:
            v_in3 = bin_width_in * bin_depth_in * bin_height_in
        return cls.bin_liner_in3_to_liters(v_in3)

    @classmethod
    def bin_liner_full_width(cls, shape, diameter_in=0, bin_width_in=0, bin_depth_in=0, overlap_in=None):
        """
        FW (full/flat width needed to wrap the bin).
        Round:       half circumference + overlap
        Square/Rect: (Wb + Db) + overlap
        """
        overlap_in = cls.BIN_LINER_DEFAULT_FW_OVERLAP_IN if overlap_in is None else overlap_in
        if shape == 'ROUND':
            return (math.pi * diameter_in) / 2 + overlap_in
        return (bin_width_in + bin_depth_in) + overlap_in

    @staticmethod
    def bin_liner_side_gusset(shape, diameter_in=0, bin_depth_in=0):
        """Side gusset: 0.6 x D (round) or = bin depth (square/rect)."""
        if shape == 'ROUND':
            return 0.6 * diameter_in
        return bin_depth_in

    @classmethod
    def bin_liner_practical_liters(cls, bag_type, width_in, length_in,
                                    side_gusset_in=0, bottom_gusset_in=0, fill_factor=None):
        """
        Practical (usable) capacity in litres for a candidate bag spec.

        SIDE-GUSSETED:   cross-section = Width x Gusset (rectangular when opened over the bin)
        BOTTOM-GUSSETED: cross-section = Width x (BottomGusset/2 + Width/4) (box-bottom shape)
        FLAT:            cross-section = Width^2 / pi

        NOTE ON THE FLAT FORMULA: the original written spec used
        Width x (Width/2) = 0.500 x W^2 for flat bags. A flat bag fills to an
        elliptical/round cross-section, not a rectangle, giving W^2/pi =
        0.318 x W^2 - the same model already used by this app's Bag Capacity
        calculator. The spec's version overestimates flat volume by ~57%
        (which is why its own worked Example 3 needed two manual iterations to
        converge). The geometrically correct form is used here.
        """
        fill_factor = cls.BIN_LINER_DEFAULT_FILL_FACTOR if fill_factor is None else fill_factor

        if bag_type == 'SIDE_GUSSETED':
            cross_section = width_in * side_gusset_in
        elif bag_type == 'BOTTOM_GUSSETED':
            cross_section = width_in * (bottom_gusset_in / 2 + width_in / 4)
        else:  # FLAT
            cross_section = (width_in ** 2) / math.pi

        theoretical_in3 = cross_section * length_in
        theoretical_liters = cls.bin_liner_in3_to_liters(theoretical_in3)
        return theoretical_liters, theoretical_liters * fill_factor

    @staticmethod
    def bin_liner_base_gauge(capacity_liters):
        """Volume-based base gauge per spec."""
        if capacity_liters <= 15:
            return 100
        elif capacity_liters <= 30:
            return 120
        elif capacity_liters <= 80:
            return 135   # spec says 120-150 range; midpoint
        elif capacity_liters <= 120:
            return 150
        elif capacity_liters <= 240:
            return 175   # spec says 150-200 range; midpoint
        return 200

    @staticmethod
    def bin_liner_waste_adjustment(waste_type):
        """Gauge adjustment by waste type per spec (midpoints used for ranges)."""
        adjustments = {
            'LIGHT': -10,
            'GENERAL': 0,
            'HEAVY': 10,
            'WET': 10,
            'SHARP': 25,       # spec: +20-30g
            'INDUSTRIAL': 40,  # spec: +30-50g
        }
        return adjustments.get(waste_type, 0)

    @classmethod
    def bin_liner_final_gauge(cls, capacity_liters, waste_type):
        base = cls.bin_liner_base_gauge(capacity_liters)
        adjustment = cls.bin_liner_waste_adjustment(waste_type)
        final = base + adjustment
        final = max(final, 100)  # spec: minimum 100g
        return int(round(final / 10.0) * 10), base, adjustment

    @classmethod
    def bin_liner_solve_spec(cls, bag_type, shape, required_liters,
                              diameter_in=0, bin_height_in=0,
                              bin_width_in=0, bin_depth_in=0,
                              overlap_in=None, fill_factor=None,
                              overhang_in=None, max_iterations=25):
        """
        Design a bin liner spec and auto-iterate until practical capacity is
        within +/-15% of required litres.

        Iteration rule (per spec): if practical < required, scale up 10%;
        if practical exceeds required by >25%, reduce length. Returns the
        converged spec plus the full iteration trail.
        """
        overhang_in = cls.bin_liner_overhang_in(required_liters) if overhang_in is None else overhang_in
        fill_factor = cls.BIN_LINER_DEFAULT_FILL_FACTOR if fill_factor is None else fill_factor

        fw = cls.bin_liner_full_width(shape, diameter_in, bin_width_in, bin_depth_in, overlap_in)
        side_gusset = cls.bin_liner_side_gusset(shape, diameter_in, bin_depth_in)

        # Initial candidate per bag type
        if bag_type == 'SIDE_GUSSETED':
            width = fw - side_gusset
            # Constraint: width must be at least 40% of FW - reduce gusset if not
            if width < 0.4 * fw:
                side_gusset = 0.6 * fw
                width = 0.4 * fw
            length = bin_height_in + overhang_in
            bottom_gusset = 0
        elif bag_type == 'BOTTOM_GUSSETED':
            base_width = (math.pi * diameter_in) / 2 if shape == 'ROUND' else bin_width_in
            width = base_width + 2.5  # spec: 2-3in slack
            length = bin_height_in + overhang_in
            bottom_gusset = bin_depth_in if (shape != 'ROUND' and bin_depth_in) else 0.5 * width
            side_gusset = 0
        else:  # FLAT
            width = fw
            length = bin_height_in + overhang_in
            side_gusset = 0
            bottom_gusset = 0

        iterations = []
        for i in range(max_iterations):
            theoretical_l, practical_l = cls.bin_liner_practical_liters(
                bag_type, width, length, side_gusset, bottom_gusset, fill_factor
            )
            deviation_pct = ((practical_l - required_liters) / required_liters) * 100 if required_liters else 0

            iterations.append({
                'iteration': i + 1,
                'width_in': round(width, 2),
                'side_gusset_in': round(side_gusset, 2),
                'bottom_gusset_in': round(bottom_gusset, 2),
                'length_in': round(length, 2),
                'theoretical_liters': round(theoretical_l, 1),
                'practical_liters': round(practical_l, 1),
                'deviation_percent': round(deviation_pct, 1),
            })

            if abs(deviation_pct) <= 15:
                break

            if practical_l < required_liters:
                width *= 1.10
                length *= 1.10
                if side_gusset:
                    side_gusset *= 1.10
                if bottom_gusset:
                    bottom_gusset *= 1.10
            elif deviation_pct > 25:
                length *= 0.90
            else:
                break

        # Round to nearest half inch
        def round_half(v):
            return round(v * 2) / 2

        width = round_half(width)
        length = round_half(length)
        side_gusset = round_half(side_gusset)
        bottom_gusset = round_half(bottom_gusset)

        theoretical_l, practical_l = cls.bin_liner_practical_liters(
            bag_type, width, length, side_gusset, bottom_gusset, fill_factor
        )

        return {
            'bag_type': bag_type,
            'width_in': width,
            'length_in': length,
            'side_gusset_in': side_gusset,
            'bottom_gusset_in': bottom_gusset,
            'full_width_in': round_half(width + side_gusset) if bag_type == 'SIDE_GUSSETED' else None,
            'full_length_in': round_half(length + bottom_gusset) if bag_type == 'BOTTOM_GUSSETED' else None,
            'fw_in': round(fw, 2),
            'overhang_in': overhang_in,
            'fill_factor': fill_factor,
            'theoretical_liters': round(theoretical_l, 1),
            'practical_liters': round(practical_l, 1),
            'deviation_percent': round(((practical_l - required_liters) / required_liters) * 100, 1) if required_liters else 0,
            'iterations': iterations,
            'converged': abs(((practical_l - required_liters) / required_liters) * 100) <= 15 if required_liters else True,
        }

    @staticmethod
    def convert_volume_to_liters(value, unit):
        """Convert a volume to litres. Accepts L, ml, m3, cm3, in3, ft3, gal."""
        conversions = {
            'L': 1.0, 'ml': 0.001, 'm3': 1000.0, 'cm3': 0.001,
            'in3': 0.016387, 'ft3': 28.3168, 'gal': 3.78541,
        }
        if unit not in conversions:
            raise ValueError(f"Invalid volume unit: {unit}")
        return value * conversions[unit]

    @staticmethod
    def convert_thickness_to_gauge(value, unit):
        """Convert a thickness to gauge. 1 gauge = 0.254 micron."""
        if unit == 'gauge':
            return value
        if unit == 'micron':
            return value / 0.254
        if unit == 'mm':
            return (value * 1000) / 0.254
        raise ValueError(f"Invalid thickness unit: {unit}")

    @staticmethod
    def convert_gauge_to_microns(gauge):
        return gauge * 0.254

    # ---------------------------------------------------------------------
    # BIN LINER SIZING — mm/micron-first wrapper
    # ---------------------------------------------------------------------

    @staticmethod
    def bin_liner_length_to_inches(value, unit):
        """Convert a length to inches. Accepts mm (default), cm, m, inch."""
        conversions_to_mm = {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'inch': 25.4}
        if unit not in conversions_to_mm:
            raise ValueError(f"Invalid length unit: {unit}")
        return (value * conversions_to_mm[unit]) / 25.4

    @staticmethod
    def bin_liner_inches_to_mm(value_in):
        return value_in * 25.4

    @classmethod
    def bin_liner_design(cls, bag_type, shape, waste_type='GENERAL',
                          required_volume=None, volume_unit='L',
                          diameter=0, diameter_unit='mm',
                          bin_height=0, bin_height_unit='mm',
                          bin_width=0, bin_width_unit='mm',
                          bin_depth=0, bin_depth_unit='mm',
                          overlap=None, overlap_unit='mm',
                          fill_factor=None, overhang=None, overhang_unit='mm'):
        """
        mm/micron-first entry point for Bin Liner Sizing. Converts all inputs
        to inches, runs the validated spec math, then converts the result
        back to mm (primary) and microns (primary thickness), keeping the
        inch/gauge spec-format values alongside.
        """
        diameter_in = cls.bin_liner_length_to_inches(diameter, diameter_unit) if diameter else 0
        bin_height_in = cls.bin_liner_length_to_inches(bin_height, bin_height_unit) if bin_height else 0
        bin_width_in = cls.bin_liner_length_to_inches(bin_width, bin_width_unit) if bin_width else 0
        bin_depth_in = cls.bin_liner_length_to_inches(bin_depth, bin_depth_unit) if bin_depth else 0
        overlap_in = cls.bin_liner_length_to_inches(overlap, overlap_unit) if overlap else None
        overhang_in = cls.bin_liner_length_to_inches(overhang, overhang_unit) if overhang else None

        # Resolve required volume in litres, from dims if not given directly
        if required_volume:
            required_liters = cls.convert_volume_to_liters(required_volume, volume_unit)
        else:
            required_liters = cls.bin_liner_volume_from_dims(
                shape, diameter_in, bin_height_in, bin_width_in, bin_depth_in, bin_height_in
            )

        # If dimensions weren't given, derive them from volume (still in inches)
        if shape == 'ROUND' and not diameter_in:
            dims = cls.bin_liner_dims_from_volume(required_liters, 'ROUND')
            diameter_in, bin_height_in = dims['diameter_in'], dims['height_in']
        elif shape != 'ROUND' and not bin_width_in:
            dims = cls.bin_liner_dims_from_volume(required_liters, shape)
            bin_width_in, bin_depth_in, bin_height_in = dims['bin_width_in'], dims['bin_depth_in'], dims['bin_height_in']

        spec = cls.bin_liner_solve_spec(
            bag_type, shape, required_liters,
            diameter_in=diameter_in, bin_height_in=bin_height_in,
            bin_width_in=bin_width_in, bin_depth_in=bin_depth_in,
            overlap_in=overlap_in, fill_factor=fill_factor, overhang_in=overhang_in
        )

        gauge, base_gauge, waste_adjustment = cls.bin_liner_final_gauge(required_liters, waste_type)
        thickness_microns = cls.convert_gauge_to_microns(gauge)

        # mm conversions of every dimension the output format needs
        to_mm = cls.bin_liner_inches_to_mm
        spec['width_mm'] = round(to_mm(spec['width_in']), 1)
        spec['length_mm'] = round(to_mm(spec['length_in']), 1)
        spec['side_gusset_mm'] = round(to_mm(spec['side_gusset_in']), 1) if spec['side_gusset_in'] else 0
        spec['bottom_gusset_mm'] = round(to_mm(spec['bottom_gusset_in']), 1) if spec['bottom_gusset_in'] else 0
        spec['full_width_mm'] = round(to_mm(spec['full_width_in']), 1) if spec['full_width_in'] else None
        spec['full_length_mm'] = round(to_mm(spec['full_length_in']), 1) if spec['full_length_in'] else None
        spec['fw_mm'] = round(to_mm(spec['fw_in']), 1)
        spec['overhang_mm'] = round(to_mm(spec['overhang_in']), 1)

        for it in spec['iterations']:
            it['width_mm'] = round(to_mm(it['width_in']), 1)
            it['length_mm'] = round(to_mm(it['length_in']), 1)
            it['side_gusset_mm'] = round(to_mm(it['side_gusset_in']), 1) if it['side_gusset_in'] else 0
            it['bottom_gusset_mm'] = round(to_mm(it['bottom_gusset_in']), 1) if it['bottom_gusset_in'] else 0

        spec['required_liters'] = round(required_liters, 1)
        spec['bin_shape'] = shape
        spec['waste_type'] = waste_type
        spec['gauge'] = gauge
        spec['thickness_microns'] = round(thickness_microns, 1)
        spec['base_gauge'] = base_gauge
        spec['waste_gauge_adjustment'] = waste_adjustment
        spec['bin_dimensions_in'] = {
            'diameter_in': round(diameter_in, 2) if shape == 'ROUND' else None,
            'bin_width_in': round(bin_width_in, 2) if shape != 'ROUND' else None,
            'bin_depth_in': round(bin_depth_in, 2) if shape != 'ROUND' else None,
            'bin_height_in': round(bin_height_in, 2),
        }
        spec['bin_dimensions_mm'] = {
            'diameter_mm': round(to_mm(diameter_in), 1) if shape == 'ROUND' else None,
            'bin_width_mm': round(to_mm(bin_width_in), 1) if shape != 'ROUND' else None,
            'bin_depth_mm': round(to_mm(bin_depth_in), 1) if shape != 'ROUND' else None,
            'bin_height_mm': round(to_mm(bin_height_in), 1),
        }

        return spec
