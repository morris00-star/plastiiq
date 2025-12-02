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

            # Get core calculation parameters
            core_calculation_method = data.get('core_calculation_method', 'dimensions')  # 'dimensions' or 'provided'
            core_wall_thickness = float(data.get('core_wall_thickness', 1.5))
            core_wall_thickness_unit = data.get('core_wall_thickness_unit', 'mm')
            core_material_density = float(data.get('core_material_density', 0.75))
            provided_core_weight = float(data.get('provided_core_weight', 0))
            provided_core_weight_unit = data.get('provided_core_weight_unit', 'kg')

            # Convert core wall thickness to mm if needed
            if core_wall_thickness_unit != 'mm':
                # Convert to mm (assuming input might be in cm or inches)
                if core_wall_thickness_unit == 'cm':
                    core_wall_thickness_mm = core_wall_thickness * 10
                elif core_wall_thickness_unit == 'inch':
                    core_wall_thickness_mm = core_wall_thickness * 25.4
                else:
                    core_wall_thickness_mm = core_wall_thickness
            else:
                core_wall_thickness_mm = core_wall_thickness

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
                material_id = layers_data[0].get('material_id') if layers_data else None
            else:
                # Single layer calculation
                material_id = data.get('material_id')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                total_thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')
                effective_density = material.density

            # Calculate roll mass with core weight
            result = calculator.calculate_roll_mass_from_diameter_with_core(
                outer_diameter_m=outer_diameter_m,
                core_diameter_m=core_diameter_m,
                width_m=width_m,
                thickness_um=total_thickness_um,
                density_g_cm3=effective_density,
                core_calculation_method=core_calculation_method,
                core_wall_thickness_mm=core_wall_thickness_mm,
                core_material_density_g_cm3=core_material_density,
                provided_core_weight=provided_core_weight if core_calculation_method == 'provided' else None,
                provided_core_weight_unit=provided_core_weight_unit
            )

            # Calculate GSM
            gsm = calculator.calculate_gsm(total_thickness_um, effective_density)

            # Add additional metrics
            result['gsm'] = round(gsm, 1)
            result['effective_density_g_cm3'] = round(effective_density, 4)
            result['total_thickness_um'] = round(total_thickness_um, 1)
            result['layer_count'] = len(layers_data) if layers_data else 1

            # Add conversions
            result['gross_weight_lb'] = round(calculator.convert_mass(result['gross_weight_kg'], 'kg', 'lb'), 2)
            result['core_weight_lb'] = round(calculator.convert_mass(result['core_weight_kg'], 'kg', 'lb'), 2)
            result['net_weight_lb'] = round(calculator.convert_mass(result['net_weight_kg'], 'kg', 'lb'), 2)

            # Add weight summary
            weight_summary = calculator.get_core_weight_summary(
                result['core_weight_kg'], result['gross_weight_kg']
            )
            result['weight_summary'] = weight_summary

            # Add core validation
            core_validation = calculator.validate_core_dimensions(core_diameter_m, width_m)
            result['core_validation'] = core_validation

            # Save calculation if user is authenticated
            if request.user.is_authenticated and material_id:
                material = PlasticMaterial.objects.get(
                    id=material_id) if not layers_data else PlasticMaterial.objects.first()
                slitting_calc = SlittingCalculation.objects.create(
                    calculation_type='ROLL_MASS',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    core_weight_source=result.get('weight_source', 'calculated')
                )

                # Save core-specific data if needed
                result['calculation_id'] = slitting_calc.id

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
            gross_mass = float(data.get('gross_mass', 0))
            gross_mass_unit = data.get('gross_mass_unit', 'kg')
            core_diameter = float(data.get('core_diameter', 0))
            core_diameter_unit = data.get('core_diameter_unit', 'm')
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'm')

            # Convert to base units
            gross_mass_kg = calculator.convert_mass(gross_mass, gross_mass_unit, 'kg')
            core_diameter_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm')
            width_m = calculator.convert_length(width, width_unit, 'm')

            # Get core calculation parameters
            core_calculation_method = data.get('core_calculation_method', 'dimensions')
            core_wall_thickness = float(data.get('core_wall_thickness', 1.5))
            core_wall_thickness_unit = data.get('core_wall_thickness_unit', 'mm')
            core_material_density = float(data.get('core_material_density', 0.75))
            provided_core_weight = float(data.get('provided_core_weight', 0))
            provided_core_weight_unit = data.get('provided_core_weight_unit', 'kg')

            # Convert core wall thickness to mm if needed
            if core_wall_thickness_unit != 'mm':
                if core_wall_thickness_unit == 'cm':
                    core_wall_thickness_mm = core_wall_thickness * 10
                elif core_wall_thickness_unit == 'inch':
                    core_wall_thickness_mm = core_wall_thickness * 25.4
                else:
                    core_wall_thickness_mm = core_wall_thickness
            else:
                core_wall_thickness_mm = core_wall_thickness

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
                material_id = layers_data[0].get('material_id') if layers_data else None
            else:
                # Single layer calculation
                material_id = data.get('material_id')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                total_thickness_um = calculator.convert_thickness(thickness, thickness_unit, 'micron')
                effective_density = material.density

            # Calculate outer diameter with core weight
            result = calculator.calculate_outer_diameter_from_mass_with_core(
                gross_mass_kg=gross_mass_kg,
                core_diameter_m=core_diameter_m,
                width_m=width_m,
                thickness_um=total_thickness_um,
                density_g_cm3=effective_density,
                core_calculation_method=core_calculation_method,
                core_wall_thickness_mm=core_wall_thickness_mm,
                core_material_density_g_cm3=core_material_density,
                provided_core_weight=provided_core_weight if core_calculation_method == 'provided' else None,
                provided_core_weight_unit=provided_core_weight_unit
            )

            # Calculate GSM
            gsm = calculator.calculate_gsm(total_thickness_um, effective_density)

            # Add additional metrics
            result['gsm'] = round(gsm, 1)
            result['effective_density_g_cm3'] = round(effective_density, 4)
            result['total_thickness_um'] = round(total_thickness_um, 1)
            result['layer_count'] = len(layers_data) if layers_data else 1

            # Add diameter conversions
            result['outer_diameter_mm'] = round(result['outer_diameter_m'] * 1000, 1)
            result['outer_diameter_inch'] = round(calculator.convert_length(result['outer_diameter_m'], 'm', 'inch'), 1)
            result['outer_diameter_ft'] = round(calculator.convert_length(result['outer_diameter_m'], 'm', 'ft'), 2)

            # Add weight conversions
            result['core_weight_lb'] = round(calculator.convert_mass(result['core_weight_kg'], 'kg', 'lb'), 2)
            result['net_weight_lb'] = round(calculator.convert_mass(result['net_weight_kg'], 'kg', 'lb'), 2)
            result['material_mass_lb'] = round(calculator.convert_mass(result['material_mass_kg'], 'kg', 'lb'), 2)

            # Add weight summary
            weight_summary = calculator.get_core_weight_summary(
                result['core_weight_kg'], gross_mass_kg
            )
            result['weight_summary'] = weight_summary

            # Add core validation
            core_validation = calculator.validate_core_dimensions(core_diameter_m, width_m)
            result['core_validation'] = core_validation

            # Calculate roll length from net material mass
            roll_length_m = calculator.calculate_film_length_from_mass(
                result['net_weight_kg'], width_m, total_thickness_um, effective_density
            )
            result['roll_length_m'] = round(roll_length_m, 2)
            result['roll_length_ft'] = round(calculator.convert_length(roll_length_m, 'm', 'ft'), 2)

            # Save calculation if user is authenticated
            if request.user.is_authenticated and material_id:
                material = PlasticMaterial.objects.get(
                    id=material_id) if not layers_data else PlasticMaterial.objects.first()
                slitting_calc = SlittingCalculation.objects.create(
                    calculation_type='ROLL_DIAMETER',
                    material=material,
                    input_data=data,
                    result_data=result,
                    user=request.user,
                    core_weight_source=result.get('weight_source', 'calculated')
                )

                result['calculation_id'] = slitting_calc.id

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Add a new view for core material management (optional)
@login_required
def get_core_materials(request):
    """API endpoint to get available core materials"""
    try:
        # If using CoreMaterial model
        core_materials = CoreMaterial.objects.filter(is_active=True)
        materials_list = [
            {
                'id': cm.id,
                'name': cm.name,
                'material_type': cm.material_type,
                'density': cm.density,
                'wall_thickness_mm': cm.wall_thickness_mm,
                'color': cm.color
            }
            for cm in core_materials
        ]

        return JsonResponse({
            'success': True,
            'materials': materials_list
        })

    except:
        # Fallback to default core materials
        return JsonResponse({
            'success': True,
            'materials': [
                {'id': 'paper', 'name': 'Standard Paper Core', 'material_type': 'Paper', 'density': 0.75,
                 'wall_thickness_mm': 1.5},
                {'id': 'heavy_paper', 'name': 'Heavy Duty Paper Core', 'material_type': 'Paper', 'density': 0.85,
                 'wall_thickness_mm': 2.0},
                {'id': 'plastic', 'name': 'Plastic Core', 'material_type': 'Plastic', 'density': 0.95,
                 'wall_thickness_mm': 2.0},
                {'id': 'steel', 'name': 'Steel Core', 'material_type': 'Steel', 'density': 7.85,
                 'wall_thickness_mm': 1.0},
            ]
        })


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
