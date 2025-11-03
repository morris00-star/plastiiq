from math import pi
from .unit_converter import UnitConverter


class SharedCalculations:

    @staticmethod
    def calculate_film_volume(width, thickness, length, width_unit='mm', thickness_unit='micron', length_unit='m'):
        """Calculate volume of film"""
        # Convert all to consistent units (mm)
        width_mm = UnitConverter.convert_length(width, width_unit, 'mm')
        thickness_mm = UnitConverter.convert_thickness(thickness, thickness_unit, 'mm')
        length_mm = UnitConverter.convert_length(length, length_unit, 'mm')

        volume = width_mm * thickness_mm * length_mm  # mm³
        return volume

    @staticmethod
    def calculate_film_mass(volume, density, volume_unit='mm3', mass_unit='kg'):
        """Calculate mass from volume and density"""
        # Convert volume to cm³ (1 cm³ = 1000 mm³)
        if volume_unit == 'mm3':
            volume_cm3 = volume / 1000
        else:
            volume_cm3 = volume

        mass_g = volume_cm3 * density  # grams
        mass_kg = UnitConverter.convert_mass(mass_g, 'g', 'kg')

        if mass_unit == 'kg':
            return mass_kg
        elif mass_unit == 'g':
            return mass_g
        else:
            return UnitConverter.convert_mass(mass_kg, 'kg', mass_unit)

    @staticmethod
    def calculate_roll_length(core_diameter, outer_diameter, thickness, width,
                              diameter_unit='mm', thickness_unit='micron', width_unit='mm'):
        """Calculate length of film on a roll"""
        # Convert to consistent units (mm)
        core_dia_mm = UnitConverter.convert_length(core_diameter, diameter_unit, 'mm')
        outer_dia_mm = UnitConverter.convert_length(outer_diameter, diameter_unit, 'mm')
        thickness_mm = UnitConverter.convert_thickness(thickness, thickness_unit, 'mm')
        width_mm = UnitConverter.convert_length(width, width_unit, 'mm')

        if thickness_mm <= 0:
            return 0

        # Length calculation considering multiple layers
        core_radius = core_dia_mm / 2
        outer_radius = outer_dia_mm / 2
        total_thickness = outer_radius - core_radius

        # Average circumference method
        avg_radius = (core_radius + outer_radius) / 2
        avg_circumference = 2 * pi * avg_radius

        number_of_layers = total_thickness / thickness_mm
        length = number_of_layers * avg_circumference

        return length / 1000  # Convert to meters

    @staticmethod
    def calculate_roll_mass(core_diameter, outer_diameter, thickness, width, density,
                            diameter_unit='mm', thickness_unit='micron', width_unit='mm', mass_unit='kg'):
        """Calculate mass of film on a roll"""
        length = SharedCalculations.calculate_roll_length(
            core_diameter, outer_diameter, thickness, width, diameter_unit, thickness_unit, width_unit
        )

        volume = SharedCalculations.calculate_film_volume(width, thickness, length, width_unit, thickness_unit, 'm')
        mass = SharedCalculations.calculate_film_mass(volume, density, 'mm3', mass_unit)

        return mass

    @staticmethod
    def calculate_production_time(material_length, machine_speed, length_unit='m', speed_unit='m_min'):
        """Calculate production time"""
        length_m = UnitConverter.convert_length(material_length, length_unit, 'm')

        if speed_unit == 'm_min':
            time_minutes = length_m / machine_speed
        elif speed_unit == 'm_hr':
            time_minutes = (length_m / machine_speed) * 60
        else:
            time_minutes = length_m / machine_speed  # Assume m/min

        return time_minutes
