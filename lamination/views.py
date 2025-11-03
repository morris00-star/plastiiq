from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import LaminationCalculation, LaminationLayer
from .lamination_calculator import LaminationCalculator
import json


@login_required
def lamination_home(request):
    calculators = [
        {'id': 'gsm_calc', 'name': 'GSM Calculation', 'icon': 'fas fa-weight-scale'},
        {'id': 'weight_breakdown', 'name': 'Weight Breakdown', 'icon': 'fas fa-balance-scale'},
        {'id': 'adhesive_components', 'name': 'Adhesive Components', 'icon': 'fas fa-flask'},
        {'id': 'lamination_time', 'name': 'Lamination Time', 'icon': 'fas fa-clock'},
        {'id': 'production_efficiency', 'name': 'Production Efficiency', 'icon': 'fas fa-chart-line'},
        {'id': 'yield_calc', 'name': 'Material Yield', 'icon': 'fas fa-percentage'},
    ]

    materials = PlasticMaterial.objects.filter(material_type='FILM')
    adhesive_types = LaminationCalculation.ADHESIVE_TYPES

    return render(request, 'lamination/home.html', {
        'section_name': 'Lamination',
        'calculators': calculators,
        'materials': materials,
        'adhesive_types': adhesive_types
    })


@login_required
@csrf_exempt
def calculate_gsm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            thickness = float(data.get('thickness', 0))
            thickness_unit = data.get('thickness_unit', 'micron')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = LaminationCalculator()

            # Convert thickness to microns
            thickness_microns = calculator.convert_to_microns(thickness, thickness_unit)

            # Calculate GSM
            gsm = calculator.calculate_gsm_from_dimensions(thickness_microns, material.density)

            result = {
                'gsm': round(gsm, 2),
                'material_name': material.name,
                'thickness_microns': round(thickness_microns, 2),
                'density': material.density
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='GSM_CALCULATION',
                    adhesive_type='SOLVENTLESS',  # Default for GSM calc
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
def calculate_multilayer_gsm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            layers_data = data.get('layers', [])
            adhesive_gsm = float(data.get('adhesive_gsm', 0))

            if len(layers_data) < 2:
                return JsonResponse(
                    {'success': False, 'error': 'At least 2 layers required for multi-layer GSM calculation'})

            calculator = LaminationCalculator()

            # Calculate GSM for each layer
            layer_details = []
            total_film_gsm = 0

            for layer_data in layers_data:
                material_id = layer_data.get('material_id')
                thickness = float(layer_data.get('thickness', 0))
                thickness_unit = layer_data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                thickness_microns = calculator.convert_to_microns(thickness, thickness_unit)
                layer_gsm = calculator.calculate_gsm_from_dimensions(thickness_microns, material.density)

                layer_details.append({
                    'material': material.name,
                    'thickness_microns': round(thickness_microns, 2),
                    'density': material.density,
                    'gsm': round(layer_gsm, 2)
                })

                total_film_gsm += layer_gsm

            # Calculate adhesive GSM (n-1 for n layers)
            number_of_adhesive_layers = len(layers_data) - 1
            total_adhesive_gsm = adhesive_gsm * number_of_adhesive_layers

            # Total laminate GSM
            total_laminate_gsm = total_film_gsm + total_adhesive_gsm

            result = {
                'layer_details': layer_details,
                'total_film_gsm': round(total_film_gsm, 2),
                'total_adhesive_gsm': round(total_adhesive_gsm, 2),
                'total_laminate_gsm': round(total_laminate_gsm, 2),
                'number_of_layers': len(layers_data),
                'number_of_adhesive_layers': number_of_adhesive_layers,
                'adhesive_gsm_per_layer': adhesive_gsm
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='MULTILAYER_GSM',
                    adhesive_type='SOLVENTLESS',  # Default for GSM calc
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
def calculate_weight_breakdown(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_mass = float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')
            adhesive_gsm_per_layer = float(data.get('adhesive_gsm', 0))  # GSM per bonding layer
            layers_data = data.get('layers', [])

            if len(layers_data) < 2:
                return JsonResponse({'success': False, 'error': 'At least 2 layers required for lamination'})

            calculator = LaminationCalculator()
            total_mass_kg = calculator.convert_mass(total_mass, total_mass_unit, 'kg')

            # Calculate GSM for each layer and prepare layer data
            layer_details = []
            layer_data_for_calc = []

            for layer_data in layers_data:
                material_id = layer_data.get('material_id')
                thickness = float(layer_data.get('thickness', 0))
                thickness_unit = layer_data.get('thickness_unit', 'micron')

                material = PlasticMaterial.objects.get(id=material_id)
                thickness_microns = calculator.convert_to_microns(thickness, thickness_unit)
                layer_gsm = calculator.calculate_gsm_from_dimensions(thickness_microns, material.density)

                layer_details.append({
                    'material': material.name,
                    'thickness_microns': round(thickness_microns, 2),
                    'gsm': round(layer_gsm, 2)
                })

                layer_data_for_calc.append({
                    'material_name': material.name,
                    'thickness_microns': thickness_microns,
                    'gsm': layer_gsm
                })

            # Calculate weight breakdown with individual layer masses and adhesive
            breakdown = calculator.calculate_laminate_weight_breakdown(
                total_mass_kg, layer_data_for_calc, adhesive_gsm_per_layer
            )

            result = {
                'total_film_mass_kg': round(breakdown['total_film_mass_kg'], 3),
                'total_adhesive_mass_kg': round(breakdown['total_adhesive_mass_kg'], 3),
                'total_laminate_gsm': round(breakdown['total_laminate_gsm'], 2),
                'total_film_gsm': round(breakdown['total_film_gsm'], 2),
                'total_adhesive_gsm': round(breakdown['total_adhesive_gsm'], 2),
                'layer_details': layer_details,
                'layer_masses': breakdown['layer_masses'],
                'number_of_layers': breakdown['number_of_layers'],
                'adhesive_layers_count': breakdown['adhesive_layers_count'],
                'adhesive_gsm_per_layer': adhesive_gsm_per_layer,
                'film_breakdown_percent': round((breakdown['total_film_mass_kg'] / total_mass_kg) * 100, 1),
                'adhesive_breakdown_percent': round((breakdown['total_adhesive_mass_kg'] / total_mass_kg) * 100, 1)
            }

            if request.user.is_authenticated:
                calculation = LaminationCalculation.objects.create(
                    calculation_type='WEIGHT_BREAKDOWN',
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

                # Save layer details
                for i, layer_data in enumerate(layers_data):
                    LaminationLayer.objects.create(
                        calculation=calculation,
                        material_id=layer_data.get('material_id'),
                        thickness=layer_data.get('thickness'),
                        thickness_unit=layer_data.get('thickness_unit'),
                        layer_order=i
                    )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def calculate_adhesive_components(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            adhesive_type = data.get('adhesive_type', 'SOLVENTLESS')
            coat_weight_gsm = float(data.get('coat_weight_gsm', 0))
            total_mass = float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')
            total_film_gsm = float(data.get('total_film_gsm', 0))
            calculated_from_layers = data.get('calculated_from_layers', False)

            # Custom ratio parameters
            use_custom_ratio = data.get('use_custom_ratio', False)
            custom_ratio_a = data.get('custom_ratio_a')
            custom_ratio_b = data.get('custom_ratio_b')
            custom_ratio_c = data.get('custom_ratio_c')  # New solvent ratio
            custom_adhesive_solids = data.get('custom_adhesive_solids')
            custom_hardener_solids = data.get('custom_hardener_solids')
            custom_adhesive_name = data.get('custom_adhesive_name')
            custom_hardener_name = data.get('custom_hardener_name')

            if total_mass <= 0:
                return JsonResponse({'success': False, 'error': 'Total mass must be greater than zero'})
            if coat_weight_gsm <= 0:
                return JsonResponse({'success': False, 'error': 'Coat weight must be greater than zero'})
            if total_film_gsm <= 0:
                return JsonResponse({'success': False, 'error': 'Total film GSM must be greater than zero'})

            # Validate custom ratios if used
            if use_custom_ratio:
                if not custom_ratio_a or not custom_ratio_b or not custom_ratio_c:
                    return JsonResponse(
                        {'success': False, 'error': 'Please provide all custom ratio values (A, B, and C)'})
                if float(custom_ratio_a) <= 0 or float(custom_ratio_b) <= 0 or float(custom_ratio_c) < 0:
                    return JsonResponse({'success': False,
                                         'error': 'Custom ratios A and B must be greater than zero, and C must be zero or positive'})

            calculator = LaminationCalculator()
            total_mass_kg = calculator.convert_mass(total_mass, total_mass_unit, 'kg')

            # Calculate component weights with custom parameters
            components = calculator.calculate_adhesive_component_weights(
                adhesive_type, total_mass_kg, coat_weight_gsm, total_film_gsm,
                float(custom_ratio_a) if use_custom_ratio and custom_ratio_a else None,
                float(custom_ratio_b) if use_custom_ratio and custom_ratio_b else None,
                float(custom_ratio_c) if use_custom_ratio and custom_ratio_c else None,
                float(custom_adhesive_solids) if use_custom_ratio and custom_adhesive_solids else None,
                float(custom_hardener_solids) if use_custom_ratio and custom_hardener_solids else None,
                custom_adhesive_name if use_custom_ratio else None,
                custom_hardener_name if use_custom_ratio else None
            )

            result = {
                'dry_adhesive_mass_kg': components.get('Dry_Adhesive_Mass_kg', 0),
                'resin_kg': components.get('Resin_A_kg', 0),
                'hardener_kg': components.get('Hardener_B_kg', 0),
                'ethyl_acetate_kg': components.get('Ethyl_Acetate_kg', 0),
                'adhesive_system': components.get('Adhesive_System', ''),
                'hardener_system': components.get('Hardener_System', ''),
                'total_wet_mix_kg': round(
                    components.get('Resin_A_kg', 0) + components.get('Hardener_B_kg', 0) + components.get(
                        'Ethyl_Acetate_kg', 0), 3),
                'adhesive_type': adhesive_type,
                'total_area_m2': components.get('Total_Area_m2', 0),
                'calculated_from_layers': calculated_from_layers,
                'mix_ratio': components.get('Mix_Ratio', ''),
                'is_custom': components.get('Is_Custom', False),
                'solids_content': components.get('Solids_Content', {}),
                'input_parameters': {
                    'total_mass_kg': total_mass_kg,
                    'coat_weight_gsm': coat_weight_gsm,
                    'total_film_gsm': total_film_gsm,
                    'use_custom_ratio': use_custom_ratio
                }
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='ADHESIVE_COMPONENTS',
                    adhesive_type=adhesive_type,
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
def calculate_lamination_time(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            roll_length = float(data.get('roll_length', 0))
            roll_length_unit = data.get('roll_length_unit', 'm')
            machine_speed = float(data.get('machine_speed', 0))
            machine_speed_unit = data.get('machine_speed_unit', 'm_min')

            calculator = LaminationCalculator()

            # Convert to base units
            roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')
            machine_speed_m_min = calculator.convert_speed(machine_speed, machine_speed_unit, 'm_min')

            # Calculate lamination time
            lamination_time_min = calculator.calculate_lamination_time(roll_length_m, machine_speed_m_min)

            result = {
                'lamination_time_min': round(lamination_time_min, 2),
                'lamination_time_hr': round(lamination_time_min / 60, 2),
                'roll_length_m': round(roll_length_m, 2),
                'machine_speed_m_min': round(machine_speed_m_min, 2)
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='LAMINATION_TIME',
                    adhesive_type='SOLVENTLESS',  # Default
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
            lamination_time = float(data.get('lamination_time', 0))
            lamination_time_unit = data.get('lamination_time_unit', 'min')
            total_run_time = float(data.get('total_run_time', 0))
            total_run_time_unit = data.get('total_run_time_unit', 'min')

            calculator = LaminationCalculator()

            # Convert to minutes
            if lamination_time_unit == 'hr':
                lamination_time_min = lamination_time * 60
            else:
                lamination_time_min = lamination_time

            if total_run_time_unit == 'hr':
                total_run_time_min = total_run_time * 60
            else:
                total_run_time_min = total_run_time

            # Calculate efficiency
            efficiency = calculator.calculate_production_efficiency(lamination_time_min, total_run_time_min)

            result = {
                'efficiency_percent': round(efficiency, 1),
                'lamination_time_min': round(lamination_time_min, 2),
                'total_run_time_min': round(total_run_time_min, 2),
                'downtime_min': round(total_run_time_min - lamination_time_min, 2),
                'efficiency_rating': get_efficiency_rating(efficiency)
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='PRODUCTION_EFFICIENCY',
                    adhesive_type='SOLVENTLESS',
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
            input_mass = float(data.get('input_mass', 0))
            input_mass_unit = data.get('input_mass_unit', 'kg')
            output_mass = float(data.get('output_mass', 0))
            output_mass_unit = data.get('output_mass_unit', 'kg')

            calculator = LaminationCalculator()

            # Convert to kg
            input_mass_kg = calculator.convert_mass(input_mass, input_mass_unit, 'kg')
            output_mass_kg = calculator.convert_mass(output_mass, output_mass_unit, 'kg')

            # Calculate yield
            yield_percent = calculator.calculate_yield(input_mass_kg, output_mass_kg)

            result = {
                'yield_percent': round(yield_percent, 1),
                'input_mass_kg': round(input_mass_kg, 3),
                'output_mass_kg': round(output_mass_kg, 3),
                'waste_mass_kg': round(input_mass_kg - output_mass_kg, 3),
                'yield_rating': get_yield_rating(yield_percent)
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='MATERIAL_YIELD',
                    adhesive_type='SOLVENTLESS',
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Helper functions for ratings
def get_efficiency_rating(efficiency):
    if efficiency >= 90:
        return "Excellent"
    elif efficiency >= 80:
        return "Good"
    elif efficiency >= 70:
        return "Average"
    else:
        return "Needs Improvement"


def get_yield_rating(yield_percent):
    if yield_percent >= 98:
        return "Excellent"
    elif yield_percent >= 95:
        return "Good"
    elif yield_percent >= 90:
        return "Average"
    else:
        return "Needs Improvement"


def convert_speed(value, from_unit, to_unit):
    conversions = {
        'm_min': 1.0,
        'm_hr': 1 / 60.0,
        'ft_min': 0.3048,
        'ft_hr': 0.3048 / 60.0
    }
    return value * conversions[from_unit] / conversions[to_unit]


@login_required
def lamination_history(request):
    """Display lamination calculation history for authenticated users"""
    calculations = LaminationCalculation.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'lamination/history.html', {'calculations': calculations})
