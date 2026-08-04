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


def resolve_common_fields(data):
    """Resolve optional machine/customer/order context shared across all extrusion calculators."""
    machine_name = data.get('machine_name') or ''
    customer_name = data.get('customer_name') or ''
    order_name = data.get('order_name') or ''
    return machine_name, customer_name, order_name


def resolve_material_with_fallback(data):
    """
    Resolve material_id from the request. Falls back to the first material in the
    database if not provided, since ExtrusionCalculation.material has no null=True -
    a real value must always be saved.
    """
    material_id = data.get('material_id')
    if material_id:
        try:
            return PlasticMaterial.objects.get(id=material_id)
        except PlasticMaterial.DoesNotExist:
            pass
    return PlasticMaterial.objects.first()


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
        {'id': 'layer_distribution', 'name': 'Layer Distribution', 'icon': 'fas fa-th-large'},
        {'id': 'masterbatch_dosing', 'name': 'Masterbatch Dosing', 'icon': 'fas fa-tint'},
        {'id': 'regrind_blend', 'name': 'Regrind/Recycled Blend', 'icon': 'fas fa-recycle'},
        {'id': 'specific_output', 'name': 'Specific Output Rate', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'neck_in_draw', 'name': 'Neck-in / Draw Ratio', 'icon': 'fas fa-compress-arrows-alt'},
        {'id': 'puncture_energy', 'name': 'Puncture Resistance / Impact Energy', 'icon': 'fas fa-fist-raised'},
        {'id': 'secant_modulus', 'name': 'Secant Modulus', 'icon': 'fas fa-ruler-combined'},
        {'id': 'waste_percent', 'name': 'Scrap/Waste Percentage', 'icon': 'fas fa-trash-alt'},
        {'id': 'barrier_normalization', 'name': 'Barrier Property Normalization', 'icon': 'fas fa-shield-alt'},
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                thickness_gauge = thickness_microns * 0.254

                result = {
                    'thickness_microns': round(thickness_microns, 2),
                    'thickness_gauge': round(thickness_gauge, 2),
                    'thickness_mm': round(thickness_m * 1000, 4),
                    'thickness_mil': round(thickness_microns / 25.4, 3),
                    'method': 'cut_weigh',
                    'sheet_thickness_microns': round(thickness_microns, 2),
                    'tube_thickness_microns': round(thickness_microns * 2, 2),
                    'sheet_thickness_gauge': round(thickness_gauge, 2),
                    'tube_thickness_gauge': round(thickness_gauge * 2, 2),
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
                thickness_gauge = thickness_microns * 0.254

                result = {
                    'thickness_microns': round(thickness_microns, 2),
                    'thickness_gauge': round(thickness_gauge, 2),
                    'thickness_mm': round(thickness_m * 1000, 4),
                    'thickness_mil': round(thickness_microns / 25.4, 3),
                    'method': 'extrusion_rate',
                    'sheet_thickness_microns': round(thickness_microns, 2),
                    'tube_thickness_microns': round(thickness_microns * 2, 2),
                    'sheet_thickness_gauge': round(thickness_gauge, 2),
                    'tube_thickness_gauge': round(thickness_gauge * 2, 2),
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='TAKEUP_SPEED',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='TENSILE',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_tensile_category(strength_mpa):
    if strength_mpa < 10:
        return "Low Strength"
    elif strength_mpa < 30:
        return "Medium Strength"
    elif strength_mpa < 50:
        return "High Strength"
    else:
        return "Very High Strength"


@csrf_exempt
def calculate_elongation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='ELONGATION',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)

            # Get test configuration
            test_method = data.get('test_method', 'film_to_film')
            film_surface = data.get('film_surface', 'inner')

            # Static friction data
            static_friction_force = safe_float(data.get('static_friction_force', 0))
            static_friction_force_unit = data.get('static_friction_force_unit', 'N')
            static_normal_force = safe_float(data.get('static_normal_force', 0))
            static_normal_force_unit = data.get('static_normal_force_unit', 'N')

            # Dynamic friction data
            dynamic_friction_force = safe_float(data.get('dynamic_friction_force', 0))
            dynamic_friction_force_unit = data.get('dynamic_friction_force_unit', 'N')
            dynamic_normal_force = safe_float(data.get('dynamic_normal_force', 0))
            dynamic_normal_force_unit = data.get('dynamic_normal_force_unit', 'N')

            calculator = ExtrusionCalculator()

            # Convert to base units
            F_f_static = calculator.convert_force(static_friction_force, static_friction_force_unit, 'N')
            F_n_static = calculator.convert_force(static_normal_force, static_normal_force_unit, 'N')
            F_f_dynamic = calculator.convert_force(dynamic_friction_force, dynamic_friction_force_unit, 'N')
            F_n_dynamic = calculator.convert_force(dynamic_normal_force, dynamic_normal_force_unit, 'N')

            # Calculate coefficients
            static_cof = calculator.calc_coefficient_of_friction(F_f_static, F_n_static)
            dynamic_cof = calculator.calc_coefficient_of_friction(F_f_dynamic, F_n_dynamic)

            # Determine test configuration description
            test_method_display = "Film to Film (Poly to Poly)" if test_method == 'film_to_film' else "Film to Metal (Poly to Metal)"
            film_surface_display = "Inner Surface" if film_surface == 'inner' else "Outer Surface"

            result = {
                'static_coefficient': round(static_cof, 3),
                'dynamic_coefficient': round(dynamic_cof, 3),
                'test_configuration': {
                    'method': test_method_display,
                    'surface': film_surface_display,
                    'full_description': f"{test_method_display} - {film_surface_display}"
                },
                'static_friction_type': get_friction_type(static_cof),
                'dynamic_friction_type': get_friction_type(dynamic_cof),
                'static_interpretation': get_cof_interpretation(static_cof, 'static'),
                'dynamic_interpretation': get_cof_interpretation(dynamic_cof, 'dynamic'),
                'comparison_note': get_cof_comparison_note(static_cof, dynamic_cof),
                'application_recommendation': get_application_recommendation(static_cof, dynamic_cof, test_method)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='COF',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_friction_type(cof):
    if cof < 0.1:
        return "Very Low Friction"
    elif cof < 0.2:
        return "Low Friction"
    elif cof < 0.4:
        return "Medium Friction"
    elif cof < 0.6:
        return "High Friction"
    else:
        return "Very High Friction"


def get_cof_interpretation(cof, friction_type):
    if friction_type == 'static':
        if cof < 0.2:
            return "Excellent for bag opening and high-speed packaging"
        elif cof < 0.4:
            return "Good for general packaging applications"
        elif cof < 0.6:
            return "May cause sticking in high-speed applications"
        else:
            return "High sticking tendency - may cause handling issues"
    else:  # dynamic
        if cof < 0.15:
            return "Excellent slip properties for high-speed machinery"
        elif cof < 0.3:
            return "Good for most packaging machinery"
        elif cof < 0.5:
            return "May require machinery adjustments"
        else:
            return "High friction - may cause machinery problems"


def get_cof_comparison_note(static_cof, dynamic_cof):
    if static_cof > dynamic_cof:
        return "Typical behavior: Static COF > Dynamic COF"
    elif static_cof < dynamic_cof:
        return "Atypical: Static COF < Dynamic COF (unusual)"
    else:
        return "Static and Dynamic COF are equal"


def get_application_recommendation(static_cof, dynamic_cof, test_method):
    base_recommendation = ""

    if test_method == 'film_to_film':
        if dynamic_cof < 0.2:
            base_recommendation = "Excellent for high-speed bag making and stacking"
        elif dynamic_cof < 0.35:
            base_recommendation = "Suitable for most packaging applications"
        else:
            base_recommendation = "May cause stacking and handling issues"
    else:  # film_to_metal
        if dynamic_cof < 0.15:
            base_recommendation = "Excellent for high-speed machinery operation"
        elif dynamic_cof < 0.25:
            base_recommendation = "Good for standard packaging machinery"
        else:
            base_recommendation = "May cause machinery wear and tear"

    if static_cof > 0.5:
        base_recommendation += " - High static friction may cause bag opening issues"

    return base_recommendation


@login_required
@csrf_exempt
def calculate_dart_impact(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            weights_g = [safe_float(w) for w in data.get('weights_g', [])]
            failures = [safe_int(f) for f in data.get('failures', [])]
            total_drops = [safe_int(td) for td in data.get('total_drops', [])]
            weight_step = safe_float(data.get('weight_step', 5))
            material_id = data.get('material_id')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            # Validate inputs
            if len(weights_g) != len(failures) or len(weights_g) != len(total_drops):
                return JsonResponse({'success': False, 'error': 'Weights, failures, and total drops arrays must have same length'})

            if not material_id:
                return JsonResponse({'success': False, 'error': 'Please select a material'})

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = ExtrusionCalculator(material.density)

            # Convert thickness to microns for normalization
            thickness_microns = calculator.convert_to_meters(thickness, thickness_unit) * 1_000_000

            # Calculate M50 using ASTM D1709 formula - FIXED CALL
            m50 = calculator.calc_dart_impact_m50_astm(weights_g, failures, total_drops, weight_step)

            # Calculate normalized value (grams per micron)
            normalized_m50 = m50 / thickness_microns if thickness_microns > 0 else 0

            result = {
                'dart_impact_m50_g': round(m50, 1),
                'dart_impact_normalized': round(normalized_m50, 3),
                'thickness_microns': round(thickness_microns, 1),
                'test_count': len(weights_g),
                'total_failures': sum(failures),
                'total_drops': sum(total_drops),
                'failure_rate_percent': round((sum(failures) / sum(total_drops)) * 100, 1) if sum(total_drops) > 0 else 0,
                'weight_step': weight_step,
                'impact_category': get_dart_impact_category(m50),
                'normalized_category': get_normalized_dart_impact_category(normalized_m50),
                'material_name': material.name,
                'material_density': material.density
            }

            if request.user.is_authenticated:
                ExtrusionCalculation.objects.create(
                    calculation_type='DART_IMPACT',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except PlasticMaterial.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected material not found'})
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

def get_normalized_dart_impact_category(normalized_value):
    if normalized_value < 0.5:
        return "Low Normalized Impact"
    elif normalized_value < 1.0:
        return "Medium Normalized Impact"
    elif normalized_value < 2.0:
        return "High Normalized Impact"
    else:
        return "Very High Normalized Impact"

@login_required
@csrf_exempt
def calculate_gauge_variation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='GAUGE_VARIATION',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='COMPOSITE_DENSITY',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
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
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_layer_distribution(request):
    """
    RPM-based layer distribution for multi-layer machine architecture.
    Supports 3-layer (A,B,C) and 5-layer (A,B,C,D,E) configurations.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            config = data.get('layer_config', '3layer')  # '3layer' or '5layer'
            total_kg = safe_float(data.get('total_kg', 0))
            total_microns = safe_float(data.get('total_microns', 0))

            if config == '5layer':
                labels = ['A', 'B', 'C', 'D', 'E']
            elif config == '3layer':
                labels = ['A', 'B', 'C']
            else:
                return JsonResponse({'success': False, 'error': 'layer_config must be "3layer" or "5layer"'})

            rpm_values = [safe_float(data.get(f'rpm_{label.lower()}', 0)) for label in labels]

            if sum(rpm_values) <= 0:
                return JsonResponse({'success': False, 'error': 'Total RPM must be greater than 0'})

            calculator = ExtrusionCalculator()
            layer_results = calculator.calc_layer_distribution(rpm_values, total_kg, total_microns)

            layers = []
            for label, rpm, layer in zip(labels, rpm_values, layer_results):
                layers.append({
                    'layer': label,
                    'rpm': rpm,
                    'percent': round(layer['percent'], 2),
                    'kg': round(layer['kg'], 3),
                    'microns': round(layer['microns'], 2)
                })

            result = {
                'layer_config': config,
                'total_rpm': round(sum(rpm_values), 2),
                'total_kg': total_kg,
                'total_microns': total_microns,
                'layers': layers
            }

            if request.user.is_authenticated:
                calc_type = 'LAYER_DISTRIBUTION_5' if config == '5layer' else 'LAYER_DISTRIBUTION_3'
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type=calc_type,
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_composite_density(request):
    """
    Calculate composite density.
    method='thickness' (default): weighted by layer thickness in microns.
    method='percent': weighted by layer allocation percentages (must sum to 100).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            method = data.get('method', 'thickness')
            layer_densities = [safe_float(d) for d in data.get('layer_densities', [])]

            calculator = ExtrusionCalculator()

            if method == 'percent':
                layer_percentages = [safe_float(p) for p in data.get('layer_percentages', [])]

                if len(layer_densities) != len(layer_percentages):
                    return JsonResponse({'success': False, 'error': 'Number of densities must match number of percentages'})

                total_percent = sum(layer_percentages)
                if round(total_percent, 1) != 100.0:
                    return JsonResponse({'success': False, 'error': f'Layer percentages must sum to 100% (currently {total_percent}%)'})

                composite_density = calculator.calc_composite_density_by_percent(layer_densities, layer_percentages)

                layer_data = []
                for i, (density, percent) in enumerate(zip(layer_densities, layer_percentages)):
                    layer_data.append({
                        'layer': i + 1,
                        'density_g_cm3': density,
                        'allocation_percent': percent
                    })

                result = {
                    'composite_density_g_cm3': round(composite_density, 4),
                    'method': 'percent',
                    'layers': layer_data,
                    'layer_count': len(layer_densities)
                }

            else:
                layer_thicknesses = [safe_float(t) for t in data.get('layer_thicknesses', [])]

                if len(layer_densities) != len(layer_thicknesses):
                    return JsonResponse({'success': False, 'error': 'Number of densities must match number of thicknesses'})

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
                    'method': 'thickness',
                    'layers': layer_data,
                    'layer_count': len(layer_densities)
                }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='COMPOSITE_DENSITY',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_masterbatch_dosing(request):
    """Masterbatch/color concentrate dosing calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            target_percent = safe_float(data.get('target_percent', 0))
            total_batch = safe_float(data.get('total_batch', 0))
            total_batch_unit = data.get('total_batch_unit', 'kg')

            if target_percent <= 0 or total_batch <= 0:
                return JsonResponse({'success': False, 'error': 'Target percent and total batch must be greater than 0'})

            calculator = ExtrusionCalculator()
            total_batch_kg = calculator.convert_mass(total_batch, total_batch_unit, 'kg')

            dosing = calculator.calc_masterbatch_dosing(target_percent, total_batch_kg)

            result = {
                'mb_kg': round(dosing['mb_kg'], 4),
                'mb_g': round(dosing['mb_kg'] * 1000, 1),
                'virgin_kg': round(dosing['virgin_kg'], 3),
                'letdown_ratio': round(dosing['letdown_ratio'], 1),
                'letdown_display': f"1:{round(dosing['letdown_ratio'], 1)}",
                'target_percent': target_percent
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='MASTERBATCH_DOSING',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_regrind_blend(request):
    """Regrind/recycled content blend ratio and blended density calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            regrind_percent = safe_float(data.get('regrind_percent', 0))
            total_batch = safe_float(data.get('total_batch', 0))
            total_batch_unit = data.get('total_batch_unit', 'kg')
            virgin_density = safe_float(data.get('virgin_density', 0))
            regrind_density = safe_float(data.get('regrind_density', 0))

            if regrind_percent < 0 or regrind_percent > 100:
                return JsonResponse({'success': False, 'error': 'Regrind percent must be between 0 and 100'})
            if total_batch <= 0:
                return JsonResponse({'success': False, 'error': 'Total batch must be greater than 0'})

            calculator = ExtrusionCalculator()
            total_batch_kg = calculator.convert_mass(total_batch, total_batch_unit, 'kg')

            blend = calculator.calc_regrind_blend(regrind_percent, total_batch_kg, virgin_density, regrind_density)

            result = {
                'regrind_kg': round(blend['regrind_kg'], 3),
                'virgin_kg': round(blend['virgin_kg'], 3),
                'virgin_percent': round(blend['virgin_percent'], 1),
                'regrind_percent': round(regrind_percent, 1),
                'blended_density_g_cm3': round(blend['blended_density_g_cm3'], 4)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='REGRIND_BLEND',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_specific_output(request):
    """Specific output rate (kg/hr per screw RPM) calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            mass_flow = safe_float(data.get('mass_flow', 0))
            mass_flow_unit = data.get('mass_flow_unit', 'kg_hr')
            screw_rpm = safe_float(data.get('screw_rpm', 0))
            baseline_specific_output = safe_float(data.get('baseline_specific_output', 0))

            if mass_flow <= 0 or screw_rpm <= 0:
                return JsonResponse({'success': False, 'error': 'Mass flow and screw RPM must be greater than 0'})

            calculator = ExtrusionCalculator()
            mass_flow_kghr = mass_flow if mass_flow_unit == 'kg_hr' else calculator.convert_mass_flow(mass_flow, mass_flow_unit, 'kg_hr')

            specific_output = calculator.calc_specific_output_rate(mass_flow_kghr, screw_rpm)

            result = {
                'specific_output_kg_hr_rpm': round(specific_output, 4),
                'mass_flow_kghr': round(mass_flow_kghr, 2),
                'screw_rpm': screw_rpm
            }

            if baseline_specific_output > 0:
                deviation_percent = ((specific_output - baseline_specific_output) / baseline_specific_output) * 100
                result['baseline_specific_output'] = baseline_specific_output
                result['deviation_percent'] = round(deviation_percent, 1)
                result['deviation_note'] = get_specific_output_deviation_note(deviation_percent)

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='SPECIFIC_OUTPUT',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_specific_output_deviation_note(deviation_percent):
    if abs(deviation_percent) < 3:
        return "Within normal range"
    elif deviation_percent >= 3:
        return "Above baseline - check for possible over-feeding or screw wear"
    else:
        return "Below baseline - possible surging, slippage, or feed restriction"


@login_required
@csrf_exempt
def calculate_neck_in_draw(request):
    """Neck-in and draw ratio calculator for cast film / extrusion coating lines"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            die_width = safe_float(data.get('die_width', 0))
            die_width_unit = data.get('die_width_unit', 'm')
            final_width = safe_float(data.get('final_width', 0))
            final_width_unit = data.get('final_width_unit', 'm')
            die_gap = safe_float(data.get('die_gap', 0))
            die_gap_unit = data.get('die_gap_unit', 'mm')
            final_thickness = safe_float(data.get('final_thickness', 0))
            final_thickness_unit = data.get('final_thickness_unit', 'micron')

            calculator = ExtrusionCalculator()

            die_width_m = calculator.convert_length(die_width, die_width_unit, 'm')
            final_width_m = calculator.convert_length(final_width, final_width_unit, 'm')
            die_gap_m = calculator.convert_length(die_gap, die_gap_unit, 'm')
            final_thickness_m = calculator.convert_to_meters(final_thickness, final_thickness_unit)

            neck_in_m = calculator.calc_neck_in(die_width_m, final_width_m)
            draw_ratio = calculator.calc_cast_draw_ratio(die_gap_m, final_thickness_m)

            result = {
                'neck_in_mm': round(neck_in_m * 1000, 2),
                'neck_in_cm': round(neck_in_m * 100, 2),
                'neck_in_percent': round((neck_in_m / die_width_m) * 100, 2) if die_width_m else 0,
                'draw_ratio': round(draw_ratio, 2)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='NECK_IN_DRAW',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_puncture_energy(request):
    """Puncture resistance / impact energy calculator (trapezoidal or simplified method)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            method = data.get('method', 'simplified')  # 'simplified' or 'trapezoidal'

            calculator = ExtrusionCalculator()

            if method == 'trapezoidal':
                forces = [safe_float(f) for f in data.get('forces_N', [])]
                displacements_mm = [safe_float(d) for d in data.get('displacements_mm', [])]
                displacements_m = [d / 1000 for d in displacements_mm]

                if len(forces) != len(displacements_m) or len(forces) < 2:
                    return JsonResponse({'success': False, 'error': 'Need at least 2 matching force/displacement points'})

                energy_j = calculator.calc_puncture_energy_trapezoidal(forces, displacements_m)
                result = {
                    'method': 'trapezoidal',
                    'puncture_energy_j': round(energy_j, 3),
                    'data_points': len(forces),
                    'peak_force_n': round(max(forces), 2)
                }
            else:
                peak_force = safe_float(data.get('peak_force_n', 0))
                displacement_break_m = safe_float(data.get('displacement_at_break_mm', 0)) / 1000

                if peak_force <= 0 or displacement_break_m <= 0:
                    return JsonResponse({'success': False, 'error': 'Peak force and displacement at break must be greater than 0'})

                energy_j = calculator.calc_puncture_energy_simplified(peak_force, displacement_break_m)
                result = {
                    'method': 'simplified',
                    'puncture_energy_j': round(energy_j, 3),
                    'peak_force_n': peak_force,
                    'displacement_at_break_mm': round(displacement_break_m * 1000, 2)
                }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='PUNCTURE_ENERGY',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_secant_modulus(request):
    """Secant modulus calculator (stiffness from 2% strain stress)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            load_at_2pct = safe_float(data.get('load_at_2pct', 0))
            load_unit = data.get('load_unit', 'N')
            width = safe_float(data.get('width', 0))
            width_unit = data.get('width_unit', 'mm')
            thickness = safe_float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            if load_at_2pct <= 0 or width <= 0 or thickness <= 0:
                return JsonResponse({'success': False, 'error': 'Load, width, and thickness must be greater than 0'})

            calculator = ExtrusionCalculator()

            load_N = calculator.convert_force(load_at_2pct, load_unit, 'N')
            width_m = calculator.convert_length(width, width_unit, 'm')
            thickness_m = calculator.convert_to_meters(thickness, thickness_unit)

            stress_mpa = calculator.calc_tensile_strength(load_N, width_m, thickness_m)
            secant_modulus_mpa = calculator.calc_secant_modulus(stress_mpa)

            result = {
                'stress_at_2pct_mpa': round(stress_mpa, 3),
                'secant_modulus_mpa': round(secant_modulus_mpa, 1),
                'secant_modulus_psi': round(secant_modulus_mpa * 145.038, 1),
                'stiffness_category': get_secant_modulus_category(secant_modulus_mpa)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='SECANT_MODULUS',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_secant_modulus_category(modulus_mpa):
    if modulus_mpa < 200:
        return "Low Stiffness (Flexible film)"
    elif modulus_mpa < 800:
        return "Medium Stiffness"
    elif modulus_mpa < 2000:
        return "High Stiffness"
    else:
        return "Very High Stiffness (Rigid)"


@login_required
@csrf_exempt
def calculate_waste_percent(request):
    """Scrap/waste percentage calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            waste = safe_float(data.get('waste', 0))
            waste_unit = data.get('waste_unit', 'kg')
            total_input = safe_float(data.get('total_input', 0))
            total_input_unit = data.get('total_input_unit', 'kg')

            if total_input <= 0:
                return JsonResponse({'success': False, 'error': 'Total input must be greater than 0'})

            calculator = ExtrusionCalculator()
            waste_kg = calculator.convert_mass(waste, waste_unit, 'kg')
            total_input_kg = calculator.convert_mass(total_input, total_input_unit, 'kg')

            waste_percent = calculator.calc_waste_percent(waste_kg, total_input_kg)
            good_output_kg = total_input_kg - waste_kg

            result = {
                'waste_percent': round(waste_percent, 2),
                'waste_kg': round(waste_kg, 3),
                'good_output_kg': round(good_output_kg, 3),
                'yield_percent': round(100 - waste_percent, 2),
                'waste_rating': get_waste_rating(waste_percent)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='WASTE_PERCENT',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_waste_rating(waste_percent):
    if waste_percent < 2:
        return "Excellent - Minimal Waste"
    elif waste_percent < 5:
        return "Good - Acceptable Waste Level"
    elif waste_percent < 10:
        return "Fair - Review Process Settings"
    else:
        return "Poor - High Waste, Investigate Root Cause"


@login_required
@csrf_exempt
def calculate_barrier_normalization(request):
    """Barrier property (WVTR/OTR) normalization by thickness calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            property_type = data.get('property_type', 'WVTR')
            measured_value = safe_float(data.get('measured_value', 0))
            measured_thickness = safe_float(data.get('measured_thickness', 0))
            target_thickness = safe_float(data.get('target_thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            if measured_value <= 0 or measured_thickness <= 0 or target_thickness <= 0:
                return JsonResponse({'success': False, 'error': 'Measured value, measured thickness, and target thickness must be greater than 0'})

            calculator = ExtrusionCalculator()
            normalized_value = calculator.calc_normalized_barrier(measured_value, measured_thickness, target_thickness)

            result = {
                'property_type': property_type,
                'measured_value': measured_value,
                'measured_thickness': measured_thickness,
                'target_thickness': target_thickness,
                'thickness_unit': thickness_unit,
                'normalized_value': round(normalized_value, 4)
            }

            if request.user.is_authenticated:
                default_material = resolve_material_with_fallback(data)
                ExtrusionCalculation.objects.create(
                    calculation_type='BARRIER_NORMALIZATION',
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
