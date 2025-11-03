from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import ExtrusionCalculation, ThicknessMeasurement
from .extrusion_calculator import ExtrusionCalculator
import json
import statistics
import math


# Safe float conversion utility function
def safe_float(value, default=0.0):
    """Safely convert value to float, handling empty strings and invalid inputs."""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    """Safely convert value to int, handling empty strings and invalid inputs."""
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


@login_required
def extrusion_home(request):
    calculators = [
        {'id': 'pieces_weight', 'name': 'Pieces to Weight', 'icon': 'fas fa-cubes'},
        {'id': 'thickness', 'name': 'Thickness Calculation', 'icon': 'fas fa-ruler'},
        {'id': 'takeup', 'name': 'Take-up Speed Adjustment', 'icon': 'fas fa-sync'},
        {'id': 'roll_calc', 'name': 'Roll Radius & Mass', 'icon': 'fas fa-circle'},
        {'id': 'film_length', 'name': 'Film Length from Weight', 'icon': 'fas fa-ruler-horizontal'},
        {'id': 'production_time', 'name': 'Production Time', 'icon': 'fas fa-clock'},
        {'id': 'bur_ddr', 'name': 'Blown Film Ratios', 'icon': 'fas fa-expand'},
        {'id': 'tensile', 'name': 'Tensile Strength', 'icon': 'fas fa-weight-hanging'},
        {'id': 'elongation', 'name': 'Percent Elongation', 'icon': 'fas fa-arrows-alt-v'},
        {'id': 'cof', 'name': 'Coefficient of Friction', 'icon': 'fas fa-sliders-h'},
        {'id': 'dart_impact', 'name': 'Dart Impact', 'icon': 'fas fa-bomb'},
        {'id': 'gauge_variation', 'name': 'Gauge Variation', 'icon': 'fas fa-chart-line'},
        {'id': 'composite_density', 'name': 'Composite Density', 'icon': 'fas fa-layer-group'},
        {'id': 'yield_basis', 'name': 'Yield & Basis Weight', 'icon': 'fas fa-balance-scale'},
    ]

    materials = PlasticMaterial.objects.filter(material_type='FILM')

    return render(request, 'extrusion/home.html', {
        'section_name': 'Extrusion',
        'calculators': calculators,
        'materials': materials
    })


@login_required
@csrf_exempt
def calculate_pieces_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')
            piece_length = safe_float(data.get('piece_length', 0))
            piece_length_unit = data.get('piece_length_unit', 'm')
            piece_width = safe_float(data.get('piece_width', 0))
            piece_width_unit = data.get('piece_width_unit', 'm')
            calculation_type = data.get('calculation_type', 'pieces_to_mass')

            # Handle empty values safely
            total_pieces = safe_int(data.get('total_pieces', 0))
            total_mass = safe_float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            # Convert to base units
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)
            piece_length_m = calculator.convert_length(piece_length, piece_length_unit, 'm')
            piece_width_m = calculator.convert_length(piece_width, piece_width_unit, 'm')

            if calculation_type == 'pieces_to_mass':
                # Calculate mass from pieces
                if total_pieces <= 0:
                    return JsonResponse({'success': False, 'error': 'Number of pieces must be greater than 0'})

                mass_per_piece = calculator.calc_mass_per_piece(thickness_m, piece_length_m, piece_width_m)
                total_mass_kg = mass_per_piece * total_pieces
                result = {
                    'mass_per_piece_kg': round(mass_per_piece, 6),
                    'mass_per_piece_g': round(mass_per_piece * 1000, 3),
                    'total_mass_kg': round(total_mass_kg, 3),
                    'total_mass_g': round(total_mass_kg * 1000, 1),
                    'calculation_type': 'pieces_to_mass'
                }
            else:
                # Calculate pieces from mass
                if total_mass <= 0:
                    return JsonResponse({'success': False, 'error': 'Total mass must be greater than 0'})

                total_mass_kg = calculator.convert_mass(total_mass, total_mass_unit, 'kg')
                mass_per_piece = calculator.calc_mass_per_piece(thickness_m, piece_length_m, piece_width_m)

                if mass_per_piece <= 0:
                    return JsonResponse(
                        {'success': False, 'error': 'Mass per piece is zero or negative - check inputs'})

                total_pieces_calc = calculator.calc_number_of_pieces(total_mass_kg, mass_per_piece)
                result = {
                    'mass_per_piece_kg': round(mass_per_piece, 6),
                    'mass_per_piece_g': round(mass_per_piece * 1000, 3),
                    'total_pieces': total_pieces_calc,
                    'calculation_type': 'mass_to_pieces'
                }

            # Save calculation if user is authenticated
            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='PIECES_WEIGHT',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Invalid number format: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_roll_radius_from_mass(request):
    """Calculate roll outer radius/diameter from mass"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            core_diameter = safe_float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'mm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')
            width = safe_float(data.get('width', 0))
            width_unit = data.get('width_unit', 'mm')
            total_mass = safe_float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')
            core_weight = safe_float(data.get('core_weight', 0))
            core_weight_unit = data.get('core_weight_unit', 'kg')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)
            width_m = calculator.convert_length(width, width_unit, 'm')
            total_mass_kg = calculator.convert_mass(total_mass, total_mass_unit, 'kg')
            core_weight_kg = calculator.convert_mass(core_weight, core_weight_unit, 'kg')

            outer_radius_m = calculator.calc_roll_radius_from_mass(
                core_diameter_m, thickness_m, width_m, total_mass_kg, core_weight_kg
            )
            outer_diameter_m = outer_radius_m * 2

            # Calculate roll length for reference
            roll_length_m = calculator.calc_roll_length_from_od(outer_diameter_m, core_diameter_m, thickness_m)

            result = {
                'outer_radius_mm': round(outer_radius_m * 1000, 1),
                'outer_radius_cm': round(outer_radius_m * 100, 2),
                'outer_radius_inch': round(calculator.convert_length(outer_radius_m, 'm', 'inch'), 2),
                'outer_diameter_mm': round(outer_diameter_m * 1000, 1),
                'outer_diameter_cm': round(outer_diameter_m * 100, 2),
                'outer_diameter_inch': round(calculator.convert_length(outer_diameter_m, 'm', 'inch'), 2),
                'roll_length_m': round(roll_length_m, 2),
                'total_mass_kg': total_mass_kg
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='ROLL_RADIUS_FROM_MASS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_thickness(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            method = data.get('method', 'cut_weigh')

            # Validate material selection
            if not material_id:
                return JsonResponse({'success': False, 'error': 'Please select a material'})

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            if method == 'cut_weigh':
                # Support both old and new field names for backward compatibility
                mass = safe_float(data.get('cut_mass', data.get('mass', 0)))
                mass_unit = data.get('cut_mass_unit', data.get('mass_unit', 'kg'))
                length = safe_float(data.get('cut_length', data.get('length', 0)))
                length_unit = data.get('cut_length_unit', data.get('length_unit', 'm'))
                width = safe_float(data.get('cut_width', data.get('width', 0)))
                width_unit = data.get('cut_width_unit', data.get('width_unit', 'm'))

                # Validate inputs
                if mass <= 0 or length <= 0 or width <= 0:
                    return JsonResponse({'success': False, 'error': 'Mass, length, and width must be greater than 0'})

                mass_kg = calculator.convert_mass(mass, mass_unit, 'kg')
                length_m = calculator.convert_length(length, length_unit, 'm')
                width_m = calculator.convert_length(width, width_unit, 'm')

                # Additional validation after conversion
                if mass_kg <= 0 or length_m <= 0 or width_m <= 0:
                    return JsonResponse({'success': False, 'error': 'Invalid values after unit conversion'})

                thickness_m = calculator.calc_thickness_cut_and_weigh(mass_kg, length_m, width_m)

                if thickness_m <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Calculation resulted in invalid thickness. Please check your inputs.'
                    })

                thickness_microns = thickness_m * 1_000_000

                result = {
                    'thickness_microns': round(thickness_microns, 2),
                    'thickness_mm': round(thickness_m * 1000, 4),
                    'thickness_mil': round(thickness_microns / 25.4, 3),
                    'method': 'cut_weigh',
                    'inputs_used': {
                        'mass_kg': round(mass_kg, 6),
                        'length_m': round(length_m, 4),
                        'width_m': round(width_m, 4),
                        'density_kg_m3': calculator.DENSITY_KG_M3
                    }
                }

            else:  # extrusion_rate
                # Support both old and new field names for backward compatibility
                mass_flow = safe_float(data.get('extrusion_mass_flow', data.get('mass_flow', 0)))
                mass_flow_unit = data.get('extrusion_mass_flow_unit', data.get('mass_flow_unit', 'kg_hr'))
                width = safe_float(data.get('extrusion_width', data.get('width', 0)))
                width_unit = data.get('extrusion_width_unit', data.get('width_unit', 'm'))
                takeup_speed = safe_float(data.get('extrusion_takeup_speed', data.get('takeup_speed', 0)))
                takeup_speed_unit = data.get('extrusion_takeup_speed_unit', data.get('takeup_speed_unit', 'm_min'))

                # Validate inputs
                if mass_flow <= 0 or width <= 0 or takeup_speed <= 0:
                    return JsonResponse(
                        {'success': False, 'error': 'Mass flow, width, and take-up speed must be greater than 0'})

                width_m = calculator.convert_length(width, width_unit, 'm')
                takeup_speed_m_min = calculator.convert_speed(takeup_speed, takeup_speed_unit, 'm_min')

                if mass_flow_unit == 'kg_hr':
                    mass_flow_kghr = mass_flow
                else:
                    mass_flow_kghr = calculator.convert_mass_flow(mass_flow, mass_flow_unit, 'kg_hr')

                # Additional validation after conversion
                if mass_flow_kghr <= 0 or width_m <= 0 or takeup_speed_m_min <= 0:
                    return JsonResponse({'success': False, 'error': 'Invalid values after unit conversion'})

                thickness_m = calculator.calc_thickness_from_rate(mass_flow_kghr, width_m, takeup_speed_m_min)

                if thickness_m <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Calculation resulted in invalid thickness. Please check your inputs.'
                    })

                thickness_microns = thickness_m * 1_000_000

                result = {
                    'thickness_microns': round(thickness_microns, 2),
                    'thickness_mm': round(thickness_m * 1000, 4),
                    'thickness_mil': round(thickness_microns / 25.4, 3),
                    'method': 'extrusion_rate',
                    'inputs_used': {
                        'mass_flow_kghr': round(mass_flow_kghr, 2),
                        'width_m': round(width_m, 4),
                        'takeup_speed_m_min': round(takeup_speed_m_min, 2),
                        'density_kg_m3': calculator.DENSITY_KG_M3
                    }
                }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='THICKNESS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Invalid number format: {str(e)}'})
        except PlasticMaterial.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected material not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Calculation error: {str(e)}'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_takeup_speed(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_speed = safe_float(data.get('old_speed', 0))
            old_speed_unit = data.get('old_speed_unit', 'm_min')
            old_thickness = safe_float(data.get('old_thickness', 0))
            old_thickness_unit = data.get('old_thickness_unit', 'micron')
            new_thickness = safe_float(data.get('new_thickness', 0))
            new_thickness_unit = data.get('new_thickness_unit', 'micron')

            calculator = ExtrusionCalculator()

            old_speed_m_min = calculator.convert_speed(old_speed, old_speed_unit, 'm_min')
            old_thickness_m = calculator.convert_to_meters(old_thickness, old_thickness_unit)
            new_thickness_m = calculator.convert_to_meters(new_thickness, new_thickness_unit)

            new_speed_m_min = calculator.calc_new_take_up_speed(old_speed_m_min, old_thickness_m, new_thickness_m)

            result = {
                'new_speed_m_min': round(new_speed_m_min, 2),
                'new_speed_m_hr': round(new_speed_m_min * 60, 2),
                'new_speed_ft_min': round(calculator.convert_speed(new_speed_m_min, 'm_min', 'ft_min'), 2),
                'speed_change_percent': round(((new_speed_m_min - old_speed_m_min) / old_speed_m_min) * 100, 1)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='TAKEUP_SPEED',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_roll_properties(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            calculation_type = data.get('calculation_type', 'length')  # 'length' or 'mass'

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            core_diameter = safe_float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'mm')
            outer_diameter = safe_float(data.get('outer_diameter', 0))
            outer_diameter_unit = data.get('outer_diameter_unit', 'mm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')
            width = safe_float(data.get('width', 0))
            width_unit = data.get('width_unit', 'mm')
            core_weight = safe_float(data.get('core_weight', 0))
            core_weight_unit = data.get('core_weight_unit', 'kg')

            # Convert to base units
            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            outer_diameter_m = calculator.convert_length(outer_diameter, outer_diameter_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)
            width_m = calculator.convert_length(width, width_unit, 'm')
            core_weight_kg = calculator.convert_mass(core_weight, core_weight_unit, 'kg')

            if calculation_type == 'length':
                roll_length_m = calculator.calc_roll_length_from_od(outer_diameter_m, core_diameter_m, thickness_m)
                roll_mass_kg = calculator.calc_roll_mass(roll_length_m, width_m, thickness_m, core_weight_kg)
                result = {
                    'roll_length_m': round(roll_length_m, 2),
                    'roll_length_ft': round(calculator.convert_length(roll_length_m, 'm', 'ft'), 2),
                    'roll_length_yd': round(calculator.convert_length(roll_length_m, 'm', 'ft') / 3, 2),
                    'roll_mass_kg': round(roll_mass_kg, 2),
                    'roll_mass_lb': round(calculator.convert_mass(roll_mass_kg, 'kg', 'lb'), 2),
                    'net_film_mass_kg': round(roll_mass_kg - core_weight_kg, 2),
                    'calculation_type': 'length_mass'
                }
            else:
                roll_length_m = calculator.calc_roll_length_from_od(outer_diameter_m, core_diameter_m, thickness_m)
                roll_mass_kg = calculator.calc_roll_mass(roll_length_m, width_m, thickness_m, core_weight_kg)
                result = {
                    'roll_mass_kg': round(roll_mass_kg, 2),
                    'roll_mass_lb': round(calculator.convert_mass(roll_mass_kg, 'kg', 'lb'), 2),
                    'net_film_mass_kg': round(roll_mass_kg - core_weight_kg, 2),
                    'calculation_type': 'mass'
                }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='ROLL_RADIUS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_film_length(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            film_weight = safe_float(data.get('film_weight', 0))
            film_weight_unit = data.get('film_weight_unit', 'kg')
            film_width = safe_float(data.get('film_width', 0))
            film_width_unit = data.get('film_width_unit', 'm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            film_weight_kg = calculator.convert_mass(film_weight, film_weight_unit, 'kg')
            film_width_m = calculator.convert_length(film_width, film_width_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)

            film_length_m = calculator.calc_film_length_from_weight(film_weight_kg, film_width_m, thickness_m)

            result = {
                'film_length_m': round(film_length_m, 2),
                'film_length_ft': round(calculator.convert_length(film_length_m, 'm', 'ft'), 2),
                'film_length_yd': round(calculator.convert_length(film_length_m, 'm', 'ft') / 3, 2),
                'film_length_km': round(film_length_m / 1000, 4)
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='FILM_LENGTH',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_production_time(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            quantity = safe_float(data.get('quantity', 0))
            quantity_unit = data.get('quantity_unit', 'kg')
            production_rate = safe_float(data.get('production_rate', 0))
            production_rate_unit = data.get('production_rate_unit', 'kg_hr')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            quantity_kg = calculator.convert_mass(quantity, quantity_unit, 'kg')
            production_rate_kghr = calculator.convert_mass_flow(production_rate, production_rate_unit, 'kg_hr')

            production_time_hr = calculator.calc_production_time_for_quantity(quantity_kg, production_rate_kghr)

            # Convert to different time units
            production_time_min = production_time_hr * 60
            production_time_sec = production_time_min * 60

            result = {
                'production_time_hr': round(production_time_hr, 2),
                'production_time_min': round(production_time_min, 2),
                'production_time_sec': round(production_time_sec, 2),
                'production_days': round(production_time_hr / 24, 2),
                'efficiency_note': 'Normal production' if production_time_hr <= 8 else 'Extended run required'
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='PRODUCTION_TIME',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_bur_ddr(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            lay_flat_width = safe_float(data.get('lay_flat_width', 0))
            lay_flat_width_unit = data.get('lay_flat_width_unit', 'm')
            die_diameter = safe_float(data.get('die_diameter', 0))
            die_diameter_unit = data.get('die_diameter_unit', 'm')
            die_gap = safe_float(data.get('die_gap', 0))
            die_gap_unit = data.get('die_gap_unit', 'mm')
            final_thickness = safe_float(data.get('final_thickness', 0))
            final_thickness_unit = data.get('final_thickness_unit', 'micron')

            lay_flat_width_m = calculator.convert_length(lay_flat_width, lay_flat_width_unit, 'm')
            die_diameter_m = calculator.convert_length(die_diameter, die_diameter_unit, 'm')
            die_gap_m = calculator.convert_length(die_gap, die_gap_unit, 'm')
            final_thickness_m = calculator.convert_to_meters(final_thickness, final_thickness_unit)

            bur = calculator.calc_blow_up_ratio(lay_flat_width_m, die_diameter_m)
            ddr = calculator.calc_draw_down_ratio(die_gap_m, final_thickness_m, bur)

            result = {
                'blow_up_ratio': round(bur, 2),
                'draw_down_ratio': round(ddr, 2),
                'bubble_diameter_m': round((lay_flat_width_m * 2) / math.pi, 3),
                'recommendation': get_bur_recommendation(bur)
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='BUR_DDR',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_bur_recommendation(bur):
    if bur < 1.5:
        return "Low BUR - Good for stiffness, lower impact strength"
    elif bur < 2.5:
        return "Medium BUR - Balanced properties"
    else:
        return "High BUR - Good for toughness, higher impact strength"


@login_required
@csrf_exempt
def calculate_tensile_strength(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            max_load = safe_float(data.get('max_load', 0))
            load_unit = data.get('load_unit', 'N')
            width = safe_float(data.get('width', 0))
            width_unit = data.get('width_unit', 'mm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            calculator = ExtrusionCalculator()

            # Convert to base units
            max_load_N = calculator.convert_force(max_load, load_unit, 'N')
            width_m = calculator.convert_length(width, width_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)

            tensile_strength = calculator.calc_tensile_strength(max_load_N, width_m, thickness_m)

            result = {
                'tensile_strength_mpa': round(tensile_strength, 2),
                'tensile_strength_psi': round(tensile_strength * 145.038, 2),
                'strength_category': get_tensile_category(tensile_strength)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='TENSILE',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_tensile_category(strength_mpa):
    if strength_mpa < 10:
        return "Low Strength (e.g., LDPE)"
    elif strength_mpa < 30:
        return "Medium Strength (e.g., HDPE, PP)"
    elif strength_mpa < 50:
        return "High Strength (e.g., PET, Nylon)"
    else:
        return "Very High Strength (e.g., BOPP, BOPET)"


@csrf_exempt
def calculate_elongation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            initial_length = safe_float(data.get('initial_length', 0))
            initial_length_unit = data.get('initial_length_unit', 'mm')
            final_length = safe_float(data.get('final_length', 0))
            final_length_unit = data.get('final_length_unit', 'mm')

            calculator = ExtrusionCalculator()

            # Convert to base units
            L0_m = calculator.convert_length(initial_length, initial_length_unit, 'm')
            Lf_m = calculator.convert_length(final_length, final_length_unit, 'm')

            elongation_percent = calculator.calc_percent_elongation(L0_m, Lf_m)

            result = {
                'elongation_percent': round(elongation_percent, 2),
                'elongation_ratio': round((Lf_m - L0_m) / L0_m, 3),
                'elongation_category': get_elongation_category(elongation_percent)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='ELONGATION',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_elongation_category(elongation_percent):
    if elongation_percent < 50:
        return "Low Elongation (Brittle)"
    elif elongation_percent < 200:
        return "Medium Elongation (Semi-ductile)"
    elif elongation_percent < 500:
        return "High Elongation (Ductile)"
    else:
        return "Very High Elongation (Elastic)"


@csrf_exempt
def calculate_cof(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            friction_force = safe_float(data.get('friction_force', 0))
            friction_force_unit = data.get('friction_force_unit', 'N')
            normal_force = safe_float(data.get('normal_force', 0))
            normal_force_unit = data.get('normal_force_unit', 'N')

            calculator = ExtrusionCalculator()

            F_f = calculator.convert_force(friction_force, friction_force_unit, 'N')
            F_n = calculator.convert_force(normal_force, normal_force_unit, 'N')

            cof = calculator.calc_coefficient_of_friction(F_f, F_n)

            result = {
                'coefficient_of_friction': round(cof, 3),
                'friction_type': get_friction_type(cof),
                'interpretation': get_cof_interpretation(cof)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='COF',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_friction_type(cof):
    if cof < 0.1:
        return "Very Low Friction"
    elif cof < 0.3:
        return "Low Friction"
    elif cof < 0.5:
        return "Medium Friction"
    else:
        return "High Friction"


def get_cof_interpretation(cof):
    if cof < 0.2:
        return "Excellent for high-speed packaging"
    elif cof < 0.4:
        return "Good for general packaging"
    else:
        return "May cause handling issues in high-speed applications"


@login_required
@csrf_exempt
def calculate_dart_impact(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            weights_g = [safe_float(w) for w in data.get('weights_g', [])]
            results_pass_fail = [bool(r) for r in data.get('results_pass_fail', [])]

            if len(weights_g) != len(results_pass_fail):
                return JsonResponse({'success': False, 'error': 'Weights and results arrays must have same length'})

            calculator = ExtrusionCalculator()
            m50 = calculator.calc_dart_impact_m50(weights_g, results_pass_fail)

            result = {
                'dart_impact_m50_g': round(m50, 1),
                'test_count': len(weights_g),
                'pass_count': sum(results_pass_fail),
                'fail_count': len(results_pass_fail) - sum(results_pass_fail),
                'impact_category': get_dart_impact_category(m50)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='DART_IMPACT',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_dart_impact_category(m50_g):
    if m50_g < 50:
        return "Low Impact Resistance"
    elif m50_g < 150:
        return "Medium Impact Resistance"
    elif m50_g < 300:
        return "High Impact Resistance"
    else:
        return "Very High Impact Resistance"


@login_required
@csrf_exempt
def calculate_gauge_variation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            thickness_measurements = [safe_float(m) for m in data.get('thickness_measurements', [])]

            if not thickness_measurements:
                return JsonResponse({'success': False, 'error': 'No thickness measurements provided'})

            calculator = ExtrusionCalculator()
            cv = calculator.calc_gauge_variation_cv(thickness_measurements)

            stats = {
                'mean': round(statistics.mean(thickness_measurements), 2),
                'stdev': round(statistics.stdev(thickness_measurements), 2),
                'min': round(min(thickness_measurements), 2),
                'max': round(max(thickness_measurements), 2),
                'range': round(max(thickness_measurements) - min(thickness_measurements), 2)
            }

            result = {
                'coefficient_variation_percent': round(cv, 2),
                'statistics': stats,
                'uniformity_rating': get_uniformity_rating(cv),
                'measurement_count': len(thickness_measurements)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='GAUGE_VARIATION',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_uniformity_rating(cv_percent):
    if cv_percent < 3:
        return "Excellent Uniformity"
    elif cv_percent < 6:
        return "Good Uniformity"
    elif cv_percent < 10:
        return "Fair Uniformity"
    else:
        return "Poor Uniformity - Process Adjustment Needed"


@login_required
@csrf_exempt
def calculate_composite_density(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            layer_densities = [safe_float(d) for d in data.get('layer_densities', [])]
            layer_thicknesses = [safe_float(t) for t in data.get('layer_thicknesses', [])]

            if len(layer_densities) != len(layer_thicknesses):
                return JsonResponse({'success': False, 'error': 'Number of densities must match number of thicknesses'})

            calculator = ExtrusionCalculator()
            composite_density = calculator.calc_composite_density(layer_densities, layer_thicknesses)

            total_thickness = sum(layer_thicknesses)
            layer_data = []
            for i, (density, thickness) in enumerate(zip(layer_densities, layer_thicknesses)):
                layer_data.append({
                    'layer': i + 1,
                    'density_g_cm3': density,
                    'thickness_microns': thickness,
                    'weight_percent': round((density * thickness) / (composite_density * total_thickness) * 100, 1)
                })

            result = {
                'composite_density_g_cm3': round(composite_density, 4),
                'total_thickness_microns': round(total_thickness, 1),
                'layers': layer_data,
                'layer_count': len(layer_densities)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                ExtrusionCalculation.objects.create(
                    calculation_type='COMPOSITE_DENSITY',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_yield_basis_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)
            yield_val = calculator.calc_yield(thickness_m)
            basis_weight = calculator.calc_basis_weight(thickness_m)

            result = {
                'yield_m2_kg': round(yield_val, 2),
                'yield_m2_lb': round(calculator.convert_area(yield_val, 'm2_kg', 'm2_lb'), 2),
                'basis_weight_g_m2': round(basis_weight, 1),
                'basis_weight_lb_1000ft2': round(basis_weight * 0.2048, 1),  # Conversion factor
                'thickness_microns': round(thickness_m * 1_000_000, 1),
                'material_density': material.density
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='YIELD_BASIS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def extrusion_history(request):
    """Display extrusion calculation history for authenticated users"""
    calculations = ExtrusionCalculation.objects.filter(user=request.user).select_related('material').order_by(
        '-timestamp')
    return render(request, 'extrusion/history.html', {'calculations': calculations})


@login_required
@csrf_exempt
def calculate_weight_from_length(request):
    """Calculate weight from film length (reverse of film length calculation)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            film_length = safe_float(data.get('film_length', 0))
            film_length_unit = data.get('film_length_unit', 'm')
            film_width = safe_float(data.get('film_width', 0))
            film_width_unit = data.get('film_width_unit', 'm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            film_length_m = calculator.convert_length(film_length, film_length_unit, 'm')
            film_width_m = calculator.convert_length(film_width, film_width_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)

            weight_kg = calculator.calc_weight_from_length(film_length_m, film_width_m, thickness_m)

            result = {
                'weight_kg': round(weight_kg, 3),
                'weight_g': round(weight_kg * 1000, 1),
                'weight_lb': round(calculator.convert_mass(weight_kg, 'kg', 'lb'), 3)
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='WEIGHT_FROM_LENGTH',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_roll_radius(request):
    """Calculate roll outer radius/diameter from length"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            core_diameter = safe_float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'mm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')
            roll_length = safe_float(data.get('roll_length', 0))
            roll_length_unit = data.get('roll_length_unit', 'm')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)
            roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')

            outer_radius_m = calculator.calc_roll_radius(core_diameter_m, thickness_m, roll_length_m)
            outer_diameter_m = outer_radius_m * 2

            result = {
                'outer_radius_mm': round(outer_radius_m * 1000, 1),
                'outer_radius_cm': round(outer_radius_m * 100, 2),
                'outer_radius_inch': round(calculator.convert_length(outer_radius_m, 'm', 'inch'), 2),
                'outer_diameter_mm': round(outer_diameter_m * 1000, 1),
                'outer_diameter_cm': round(outer_diameter_m * 100, 2),
                'outer_diameter_inch': round(calculator.convert_length(outer_diameter_m, 'm', 'inch'), 2),
                'roll_length_m': roll_length_m
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='ROLL_RADIUS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
