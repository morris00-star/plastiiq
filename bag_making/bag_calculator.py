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
            area_m2 = (width_m + gusset_m) * height_m

        elif bag_type in ['GUSSETED_BOTTOM', 'LAMINATED_GUSSETED_BOTTOM']:
            # Bottom gusseted: Total length = Height + Gusset
            # Area = Width * (Height + Gusset)
            area_m2 = width_m * (height_m + gusset_m)

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
