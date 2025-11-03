from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import SlittingCalculation
from .slitting_calculator import SlittingCalculator
import json


@login_required
def slitting_home(request):
    calculators = [
        {'id': 'roll_mass', 'name': 'Roll Mass from Diameter', 'icon': 'fas fa-weight-hanging'},
        {'id': 'roll_diameter', 'name': 'Roll Diameter from Mass', 'icon': 'fas fa-circle'},
        {'id': 'slitting_time', 'name': 'Slitting Time', 'icon': 'fas fa-clock'},
        {'id': 'production_efficiency', 'name': 'Production Efficiency', 'icon': 'fas fa-chart-line'},
        {'id': 'production_rate', 'name': 'Production Rate', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'yield_calculation', 'name': 'Yield Calculation', 'icon': 'fas fa-percentage'},
        {'id': 'film_length', 'name': 'Film Length from Mass', 'icon': 'fas fa-ruler'},
    ]

    materials = PlasticMaterial.objects.all().order_by('material_type', 'name')

    return render(request, 'slitting/home.html', {
        'section_name': 'Slitting',
        'calculators': calculators,
        'materials': materials
    })


@login_required
@csrf_exempt
def calculate_roll_mass(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            # Get roll dimensions
            outer_diameter = float(data.get('outer_diameter', 0))
            outer_diameter_unit = data.get('outer_diameter_unit', 'm')
            core_diameter = float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'm')
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'm')

            # Convert to base units
            outer_diameter_m = calculator.convert_length(outer_diameter, outer_diameter_unit, 'm')
            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            width_m = calculator.convert_length(width, width_unit, 'm')

            # Handle layers
            layers_data = data.get('layers', [])
            if layers_data:
                # Multi-layer calculation
                layer_thicknesses_um = []
                layer_densities_g_cm3 = []

                for layer in layers_data:
                    material_id = layer.get('material_id')
                    thickness = float(layer.get('thickness', 0))
                    thickness_unit = layer.get('thickness_unit', 'micron')

                    material = PlasticMaterial.objects.get(id=material_id)
                    thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')

                    layer_thicknesses_um.append(thickness_um)
                    layer_densities_g_cm3.append(material.density)

                total_thickness_um = calculator.calculate_material_thickness_total(layer_thicknesses_um)
                effective_density = calculator.calculate_material_density_effective(layer_thicknesses_um,
                                                                                    layer_densities_g_cm3)

            else:
                # Single layer calculation
                material_id = data.get('material_id')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                total_thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')
                effective_density = material.density

            # Calculate roll mass
            roll_mass_kg = calculator.calculate_roll_mass_from_diameter(
                outer_diameter_m, core_diameter_m, width_m, total_thickness_um, effective_density
            )

            # Calculate GSM
            gsm = calculator.calculate_gsm(total_thickness_um, effective_density)

            result = {
                'roll_mass_kg': round(roll_mass_kg, 2),
                'roll_mass_lb': round(calculator.convert_mass(roll_mass_kg, 'kg', 'lb'), 2),
                'effective_density_g_cm3': round(effective_density, 4),
                'total_thickness_um': round(total_thickness_um, 1),
                'gsm': round(gsm, 1),
                'layer_count': len(layers_data) if layers_data else 1
            }

            # Save calculation if user is authenticated
            if request.user.is_authenticated:
                material = PlasticMaterial.objects.get(
                    id=material_id) if not layers_data else PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='ROLL_MASS',
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
def calculate_roll_diameter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            # Get roll mass and dimensions
            roll_mass = float(data.get('roll_mass', 0))
            roll_mass_unit = data.get('roll_mass_unit', 'kg')
            core_diameter = float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'm')
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'm')

            # Convert to base units
            roll_mass_kg = calculator.convert_mass(roll_mass, roll_mass_unit, 'kg')
            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            width_m = calculator.convert_length(width, width_unit, 'm')

            # Handle layers
            layers_data = data.get('layers', [])
            if layers_data:
                # Multi-layer calculation
                layer_thicknesses_um = []
                layer_densities_g_cm3 = []

                for layer in layers_data:
                    material_id = layer.get('material_id')
                    thickness = float(layer.get('thickness', 0))
                    thickness_unit = layer.get('thickness_unit', 'micron')

                    material = PlasticMaterial.objects.get(id=material_id)
                    thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')

                    layer_thicknesses_um.append(thickness_um)
                    layer_densities_g_cm3.append(material.density)

                total_thickness_um = calculator.calculate_material_thickness_total(layer_thicknesses_um)
                effective_density = calculator.calculate_material_density_effective(layer_thicknesses_um,
                                                                                    layer_densities_g_cm3)

            else:
                # Single layer calculation
                material_id = data.get('material_id')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                total_thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')
                effective_density = material.density

            # Calculate outer diameter
            outer_diameter_m = calculator.calculate_outer_diameter_from_mass(
                roll_mass_kg, core_diameter_m, width_m, total_thickness_um, effective_density
            )

            # Calculate GSM
            gsm = calculator.calculate_gsm(total_thickness_um, effective_density)

            result = {
                'outer_diameter_m': round(outer_diameter_m, 3),
                'outer_diameter_mm': round(outer_diameter_m * 1000, 1),
                'outer_diameter_inch': round(calculator.convert_length(outer_diameter_m, 'm', 'inch'), 1),
                'effective_density_g_cm3': round(effective_density, 4),
                'total_thickness_um': round(total_thickness_um, 1),
                'gsm': round(gsm, 1),
                'layer_count': len(layers_data) if layers_data else 1
            }

            # Save calculation if user is authenticated
            if request.user.is_authenticated:
                material = PlasticMaterial.objects.get(
                    id=material_id) if not layers_data else PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='ROLL_DIAMETER',
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
def calculate_slitting_time(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            roll_length = float(data.get('roll_length', 0))
            roll_length_unit = data.get('roll_length_unit', 'm')
            slitting_speed = float(data.get('slitting_speed', 0))
            slitting_speed_unit = data.get('slitting_speed_unit', 'm_min')

            # Convert to base units
            roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')
            slitting_speed_m_min = calculator.convert_speed(slitting_speed, slitting_speed_unit, 'm_min')

            slitting_time_min = calculator.calculate_slitting_time(roll_length_m, slitting_speed_m_min)

            result = {
                'slitting_time_min': round(slitting_time_min, 1),
                'slitting_time_hr': round(slitting_time_min / 60, 2),
                'slitting_time_sec': round(slitting_time_min * 60, 0),
                'efficiency_note': 'Normal operation' if slitting_time_min <= 480 else 'Extended run'
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='SLITTING_TIME',
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
def calculate_production_efficiency(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            slitting_time = float(data.get('slitting_time', 0))
            slitting_time_unit = data.get('slitting_time_unit', 'min')
            total_run_time = float(data.get('total_run_time', 0))
            total_run_time_unit = data.get('total_run_time_unit', 'min')

            # Convert to minutes
            if slitting_time_unit == 'hr':
                slitting_time_min = slitting_time * 60
            else:
                slitting_time_min = slitting_time

            if total_run_time_unit == 'hr':
                total_run_time_min = total_run_time * 60
            else:
                total_run_time_min = total_run_time

            efficiency_percent = calculator.calculate_production_efficiency(slitting_time_min, total_run_time_min)

            result = {
                'efficiency_percent': round(efficiency_percent, 1),
                'efficiency_rating': get_efficiency_rating(efficiency_percent),
                'downtime_min': round(total_run_time_min - slitting_time_min, 1),
                'recommendation': get_efficiency_recommendation(efficiency_percent)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='PRODUCTION_EFFICIENCY',
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
def calculate_production_rate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            roll_mass = float(data.get('roll_mass', 0))
            roll_mass_unit = data.get('roll_mass_unit', 'kg')
            total_run_time = float(data.get('total_run_time', 0))
            total_run_time_unit = data.get('total_run_time_unit', 'min')

            # Convert to base units
            roll_mass_kg = calculator.convert_mass(roll_mass, roll_mass_unit, 'kg')

            if total_run_time_unit == 'hr':
                total_run_time_min = total_run_time * 60
            else:
                total_run_time_min = total_run_time

            production_rate_kg_hr = calculator.calculate_slitting_production_rate_kg_hr(roll_mass_kg,
                                                                                        total_run_time_min)

            result = {
                'production_rate_kg_hr': round(production_rate_kg_hr, 1),
                'production_rate_lb_hr': round(calculator.convert_mass(production_rate_kg_hr, 'kg', 'lb'), 1),
                'production_rate_kg_min': round(production_rate_kg_hr / 60, 2),
                'performance_rating': get_production_rating(production_rate_kg_hr)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='PRODUCTION_RATE',
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
def calculate_yield(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            total_input = float(data.get('total_input', 0))
            total_input_unit = data.get('total_input_unit', 'kg')
            good_output = float(data.get('good_output', 0))
            good_output_unit = data.get('good_output_unit', 'kg')

            # Convert to base units
            total_input_kg = calculator.convert_mass(total_input, total_input_unit, 'kg')
            good_output_kg = calculator.convert_mass(good_output, good_output_unit, 'kg')

            yield_percent, scrap_percent = calculator.calculate_yield_scrap(total_input_kg, good_output_kg)
            scrap_mass_kg = total_input_kg - good_output_kg

            result = {
                'yield_percent': round(yield_percent, 1),
                'scrap_percent': round(scrap_percent, 1),
                'scrap_mass_kg': round(scrap_mass_kg, 2),
                'scrap_mass_lb': round(calculator.convert_mass(scrap_mass_kg, 'kg', 'lb'), 2),
                'yield_rating': get_yield_rating(yield_percent)
            }

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
                    calculation_type='YIELD_CALCULATION',
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
def calculate_film_length(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = SlittingCalculator()

            mass = float(data.get('mass', 0))
            mass_unit = data.get('mass_unit', 'kg')
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'm')

            # Handle layers
            layers_data = data.get('layers', [])
            if layers_data:
                # Multi-layer calculation
                layer_thicknesses_um = []
                layer_densities_g_cm3 = []

                for layer in layers_data:
                    material_id = layer.get('material_id')
                    thickness = float(layer.get('thickness', 0))
                    thickness_unit = layer.get('thickness_unit', 'micron')

                    material = PlasticMaterial.objects.get(id=material_id)
                    thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')

                    layer_thicknesses_um.append(thickness_um)
                    layer_densities_g_cm3.append(material.density)

                total_thickness_um = calculator.calculate_material_thickness_total(layer_thicknesses_um)
                effective_density = calculator.calculate_material_density_effective(layer_thicknesses_um,
                                                                                    layer_densities_g_cm3)

            else:
                # Single layer calculation
                material_id = data.get('material_id')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                total_thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')
                effective_density = material.density

            # Convert to base units
            mass_kg = calculator.convert_mass(mass, mass_unit, 'kg')
            width_m = calculator.convert_length(width, width_unit, 'm')

            film_length_m = calculator.calculate_film_length_from_mass(mass_kg, width_m, total_thickness_um,
                                                                       effective_density)

            result = {
                'film_length_m': round(film_length_m, 2),
                'film_length_ft': round(calculator.convert_length(film_length_m, 'm', 'ft'), 2),
                'film_length_yd': round(film_length_m / 0.9144, 2),
                'effective_density_g_cm3': round(effective_density, 4),
                'total_thickness_um': round(total_thickness_um, 1),
                'layer_count': len(layers_data) if layers_data else 1
            }

            if request.user.is_authenticated:
                material = PlasticMaterial.objects.get(
                    id=material_id) if not layers_data else PlasticMaterial.objects.first()
                SlittingCalculation.objects.create(
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


# Helper functions for ratings and recommendations
def get_efficiency_rating(efficiency):
    if efficiency >= 90:
        return "Excellent"
    elif efficiency >= 80:
        return "Good"
    elif efficiency >= 70:
        return "Average"
    else:
        return "Needs Improvement"


def get_efficiency_recommendation(efficiency):
    if efficiency >= 90:
        return "Maintain current processes"
    elif efficiency >= 80:
        return "Minor optimizations possible"
    elif efficiency >= 70:
        return "Review setup and changeover procedures"
    else:
        return "Significant process improvements needed"


def get_production_rating(rate_kg_hr):
    if rate_kg_hr >= 1000:
        return "High Performance"
    elif rate_kg_hr >= 500:
        return "Good Performance"
    elif rate_kg_hr >= 200:
        return "Average Performance"
    else:
        return "Low Performance"


def get_yield_rating(yield_percent):
    if yield_percent >= 98:
        return "Excellent"
    elif yield_percent >= 95:
        return "Good"
    elif yield_percent >= 90:
        return "Acceptable"
    else:
        return "Needs Improvement"


@login_required
def slitting_history(request):
    """Display slitting calculation history for authenticated users"""
    calculations = SlittingCalculation.objects.filter(user=request.user).select_related('material').order_by(
        '-timestamp')
    return render(request, 'slitting/history.html', {'calculations': calculations})
