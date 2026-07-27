from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import LaminationCalculation, LaminationLayer
from .lamination_calculator import LaminationCalculator
import json


def resolve_common_fields(data):
    """Resolve optional machine/customer/job context shared across all lamination calculators."""
    machine_name = data.get('machine_name') or ''
    customer_name = data.get('customer_name') or ''
    job_name = data.get('job_name') or ''
    return machine_name, customer_name, job_name


@login_required
def lamination_home(request):
    calculators = [
        {'id': 'gsm_calc', 'name': 'GSM Calculation', 'icon': 'fas fa-weight-scale'},
        {'id': 'weight_breakdown', 'name': 'Weight Breakdown', 'icon': 'fas fa-balance-scale'},
        {'id': 'adhesive_components', 'name': 'Adhesive Components', 'icon': 'fas fa-flask'},
        {'id': 'lamination_time', 'name': 'Lamination Time', 'icon': 'fas fa-clock'},
        {'id': 'production_efficiency', 'name': 'Production Efficiency', 'icon': 'fas fa-chart-line'},
        {'id': 'yield_calc', 'name': 'Material Yield', 'icon': 'fas fa-percentage'},
        {'id': 'setting_time', 'name': 'Setting/Curing Time', 'icon': 'fas fa-hourglass-half'},
        {'id': 'peel_strength', 'name': 'Peel Strength', 'icon': 'fas fa-grip-lines'},
        {'id': 'coat_weight_verification', 'name': 'Coat Weight Verification', 'icon': 'fas fa-vial'},
        {'id': 'application_rate', 'name': 'Application Rate', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'residual_solvent', 'name': 'Residual Solvent', 'icon': 'fas fa-smog'},
        {'id': 'overall_line_efficiency', 'name': 'Overall Line Efficiency', 'icon': 'fas fa-chart-pie'},
        {'id': 'adhesive_coverage', 'name': 'Adhesive Coverage/Roll', 'icon': 'fas fa-scroll'},
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
            total_mass = float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')
            adhesive_gsm_per_layer = float(data.get('adhesive_gsm', 0))  # GSM per bonding layer
            layers_data = data.get('layers', [])
            waste_percent = float(data.get('waste_percent', 5.0))  # Default 5% waste allowance per component

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

            # Apply waste allowance to each film layer individually (net -> gross)
            layer_masses_with_waste = []
            for layer in breakdown['layer_masses']:
                waste_info = calculator.apply_waste_allowance(layer['mass_kg'], waste_percent)
                layer_masses_with_waste.append({
                    'material_name': layer['material_name'],
                    'thickness_microns': layer['thickness_microns'],
                    'gsm': layer['gsm'],
                    'net_mass_kg': round(layer['mass_kg'], 3),
                    'waste_mass_kg': round(waste_info['waste_kg'], 3),
                    'gross_mass_kg': round(waste_info['gross_kg'], 3),
                    'mass_percent': layer['mass_percent']
                })

            # Apply waste allowance to adhesive
            adhesive_waste_info = calculator.apply_waste_allowance(breakdown['total_adhesive_mass_kg'], waste_percent)

            total_net_mass_kg = breakdown['total_film_mass_kg'] + breakdown['total_adhesive_mass_kg']
            total_gross_mass_kg = sum(l['gross_mass_kg'] for l in layer_masses_with_waste) + adhesive_waste_info['gross_kg']
            total_waste_mass_kg = total_gross_mass_kg - total_net_mass_kg

            result = {
                'total_film_mass_kg': round(breakdown['total_film_mass_kg'], 3),
                'total_adhesive_mass_kg': round(breakdown['total_adhesive_mass_kg'], 3),
                'total_laminate_gsm': round(breakdown['total_laminate_gsm'], 2),
                'total_film_gsm': round(breakdown['total_film_gsm'], 2),
                'total_adhesive_gsm': round(breakdown['total_adhesive_gsm'], 2),
                'layer_details': layer_details,
                'layer_masses': layer_masses_with_waste,
                'number_of_layers': breakdown['number_of_layers'],
                'adhesive_layers_count': breakdown['adhesive_layers_count'],
                'adhesive_gsm_per_layer': adhesive_gsm_per_layer,
                'film_breakdown_percent': round((breakdown['total_film_mass_kg'] / total_mass_kg) * 100, 1),
                'adhesive_breakdown_percent': round((breakdown['total_adhesive_mass_kg'] / total_mass_kg) * 100, 1),
                'waste_percent': waste_percent,
                'adhesive_net_mass_kg': round(breakdown['total_adhesive_mass_kg'], 3),
                'adhesive_waste_mass_kg': round(adhesive_waste_info['waste_kg'], 3),
                'adhesive_gross_mass_kg': round(adhesive_waste_info['gross_kg'], 3),
                'total_net_mass_kg': round(total_net_mass_kg, 3),
                'total_waste_mass_kg': round(total_waste_mass_kg, 3),
                'total_gross_mass_kg': round(total_gross_mass_kg, 3)
            }

            if request.user.is_authenticated:
                calculation = LaminationCalculation.objects.create(
                    calculation_type='WEIGHT_BREAKDOWN',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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


@login_required
@csrf_exempt
def calculate_adhesive_components(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            adhesive_type = data.get('adhesive_type', 'SOLVENTLESS')
            coat_weight_gsm = float(data.get('coat_weight_gsm', 0))
            total_mass = float(data.get('total_mass', 0))
            total_mass_unit = data.get('total_mass_unit', 'kg')
            total_film_gsm = float(data.get('total_film_gsm', 0))
            calculated_from_layers = data.get('calculated_from_layers', False)
            waste_percent = float(data.get('waste_percent', 5.0))  # Default 5% waste allowance per component

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

            resin_net_kg = components.get('Resin_A_kg', 0)
            hardener_net_kg = components.get('Hardener_B_kg', 0)
            solvent_net_kg = components.get('Ethyl_Acetate_kg', 0)

            resin_waste = calculator.apply_waste_allowance(resin_net_kg, waste_percent)
            hardener_waste = calculator.apply_waste_allowance(hardener_net_kg, waste_percent)
            solvent_waste = calculator.apply_waste_allowance(solvent_net_kg, waste_percent)

            result = {
                'dry_adhesive_mass_kg': components.get('Dry_Adhesive_Mass_kg', 0),
                'resin_kg': resin_net_kg,
                'hardener_kg': hardener_net_kg,
                'ethyl_acetate_kg': solvent_net_kg,
                'adhesive_system': components.get('Adhesive_System', ''),
                'hardener_system': components.get('Hardener_System', ''),
                'total_wet_mix_kg': round(resin_net_kg + hardener_net_kg + solvent_net_kg, 3),
                'adhesive_type': adhesive_type,
                'total_area_m2': components.get('Total_Area_m2', 0),
                'calculated_from_layers': calculated_from_layers,
                'mix_ratio': components.get('Mix_Ratio', ''),
                'is_custom': components.get('Is_Custom', False),
                'solids_content': components.get('Solids_Content', {}),
                'waste_percent': waste_percent,
                'resin_waste_kg': round(resin_waste['waste_kg'], 3),
                'resin_gross_kg': round(resin_waste['gross_kg'], 3),
                'hardener_waste_kg': round(hardener_waste['waste_kg'], 3),
                'hardener_gross_kg': round(hardener_waste['gross_kg'], 3),
                'solvent_waste_kg': round(solvent_waste['waste_kg'], 3),
                'solvent_gross_kg': round(solvent_waste['gross_kg'], 3),
                'total_wet_mix_gross_kg': round(
                    resin_waste['gross_kg'] + hardener_waste['gross_kg'] + solvent_waste['gross_kg'], 3
                ),
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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


@login_required
@csrf_exempt
def calculate_setting_time(request):
    """Total turnaround time = lamination time + adhesive setting/curing time"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            roll_length = float(data.get('roll_length', 0))
            roll_length_unit = data.get('roll_length_unit', 'm')
            machine_speed = float(data.get('machine_speed', 0))
            machine_speed_unit = data.get('machine_speed_unit', 'm_min')
            setting_time_hr = float(data.get('setting_time_hr', 24))
            adhesive_type = data.get('adhesive_type', 'SOLVENTLESS')

            if machine_speed <= 0:
                return JsonResponse({'success': False, 'error': 'Machine speed must be greater than 0'})

            calculator = LaminationCalculator()
            roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')
            machine_speed_m_min = calculator.convert_speed(machine_speed, machine_speed_unit, 'm_min')

            lamination_time_min = calculator.calculate_lamination_time(roll_length_m, machine_speed_m_min)
            lamination_time_hr = lamination_time_min / 60

            total_turnaround_hr = calculator.calculate_total_turnaround_time(lamination_time_hr, setting_time_hr)

            result = {
                'lamination_time_min': round(lamination_time_min, 2),
                'lamination_time_hr': round(lamination_time_hr, 3),
                'setting_time_hr': setting_time_hr,
                'adhesive_type': adhesive_type,
                'total_turnaround_hr': round(total_turnaround_hr, 2),
                'total_turnaround_days': round(total_turnaround_hr / 24, 2),
                'note': 'Setting/curing time is chemistry-dependent - confirm against your adhesive TDS. This is a duration estimate, not a scheduled clock time.'
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='SETTING_TIME',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=adhesive_type,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_peel_strength_rating(peel_strength_n_per_15mm):
    if peel_strength_n_per_15mm < 1.0:
        return "Weak Bond - Below typical acceptance threshold"
    elif peel_strength_n_per_15mm < 3.0:
        return "Moderate Bond"
    elif peel_strength_n_per_15mm < 6.0:
        return "Good Bond"
    else:
        return "Excellent Bond"


@login_required
@csrf_exempt
def calculate_peel_strength(request):
    """Peel/bond strength normalized to a standard sample width (default 15mm)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            peel_force = float(data.get('peel_force', 0))
            peel_force_unit = data.get('peel_force_unit', 'N')
            sample_width_mm = float(data.get('sample_width_mm', 15))
            standard_width_mm = float(data.get('standard_width_mm', 15))
            test_type = data.get('test_type', 'film_to_film')

            if peel_force <= 0 or sample_width_mm <= 0:
                return JsonResponse({'success': False, 'error': 'Peel force and sample width must be greater than 0'})

            calculator = LaminationCalculator()
            force_conversions = {'N': 1.0, 'kN': 1000.0, 'lbf': 4.44822}
            peel_force_N = peel_force * force_conversions.get(peel_force_unit, 1.0)

            peel_strength = calculator.calculate_peel_strength(peel_force_N, sample_width_mm, standard_width_mm)

            result = {
                'peel_strength_n_per_15mm': round(peel_strength, 3),
                'peel_force_n': round(peel_force_N, 3),
                'sample_width_mm': sample_width_mm,
                'test_type': test_type,
                'bond_rating': get_peel_strength_rating(peel_strength)
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='PEEL_STRENGTH',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_coat_weight_deviation_note(deviation_percent):
    if abs(deviation_percent) < 5:
        return "Within normal application tolerance"
    elif deviation_percent >= 5:
        return "Over-applied - check coating station settings, possible excess adhesive cost"
    else:
        return "Under-applied - check coating station settings, possible bond strength risk"


@login_required
@csrf_exempt
def calculate_coat_weight_verification(request):
    """Verify actual applied coat weight against target from before/after roll weights"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            roll_weight_before = float(data.get('roll_weight_before', 0))
            roll_weight_after = float(data.get('roll_weight_after', 0))
            weight_unit = data.get('weight_unit', 'kg')
            area_laminated_m2 = float(data.get('area_laminated_m2', 0))
            target_gsm = float(data.get('target_gsm', 0))

            if area_laminated_m2 <= 0:
                return JsonResponse({'success': False, 'error': 'Area laminated must be greater than 0'})
            if roll_weight_before == roll_weight_after:
                return JsonResponse({'success': False, 'error': 'Weight before and after must differ - no material consumption/gain detected'})

            calculator = LaminationCalculator()
            unit_to_g = {'kg': 1000.0, 'g': 1.0, 'lb': 453.592}
            before_g = roll_weight_before * unit_to_g.get(weight_unit, 1000.0)
            after_g = roll_weight_after * unit_to_g.get(weight_unit, 1000.0)

            # Direction-agnostic: works whether weighing the adhesive SUPPLY roll
            # (gets lighter as adhesive is consumed) or the FILM/SUBSTRATE roll
            # (gets heavier once adhesive is applied to it).
            consumed_g = abs(before_g - after_g)
            actual_gsm = calculator.calculate_actual_coat_weight(
                max(before_g, after_g), min(before_g, after_g), area_laminated_m2
            )

            result = {
                'actual_coat_weight_gsm': round(actual_gsm, 3),
                'consumed_g': round(consumed_g, 2),
                'area_laminated_m2': area_laminated_m2,
                'weighing_method': 'supply_roll_depleted' if after_g < before_g else 'substrate_roll_gained'
            }

            if target_gsm > 0:
                deviation_percent = calculator.calculate_coat_weight_deviation(actual_gsm, target_gsm)
                result['target_gsm'] = target_gsm
                result['deviation_percent'] = round(deviation_percent, 2)
                result['deviation_note'] = get_coat_weight_deviation_note(deviation_percent)

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='COAT_WEIGHT_VERIFICATION',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
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
def calculate_application_rate(request):
    """Cross-check adhesive consumption against theoretical coat weight target"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            adhesive_consumed = float(data.get('adhesive_consumed', 0))
            adhesive_consumed_unit = data.get('adhesive_consumed_unit', 'kg')
            total_area_m2 = float(data.get('total_area_m2', 0))
            target_gsm = float(data.get('target_gsm', 0))

            if total_area_m2 <= 0:
                return JsonResponse({'success': False, 'error': 'Total area must be greater than 0'})

            calculator = LaminationCalculator()
            adhesive_consumed_kg = calculator.convert_mass(adhesive_consumed, adhesive_consumed_unit, 'kg')

            applied_rate_gsm = calculator.calculate_application_rate(adhesive_consumed_kg, total_area_m2)

            result = {
                'applied_rate_gsm': round(applied_rate_gsm, 3),
                'adhesive_consumed_kg': round(adhesive_consumed_kg, 3),
                'total_area_m2': total_area_m2
            }

            if target_gsm > 0:
                deviation_percent = calculator.calculate_coat_weight_deviation(applied_rate_gsm, target_gsm)
                result['target_gsm'] = target_gsm
                result['deviation_percent'] = round(deviation_percent, 2)
                result['deviation_note'] = get_coat_weight_deviation_note(deviation_percent)

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='APPLICATION_RATE',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
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
def calculate_residual_solvent(request):
    """Residual solvent (mg/m2) for solvent-based lamination compliance checks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            solvent_detected_ug = float(data.get('solvent_detected_ug', 0))
            sample_area_m2 = float(data.get('sample_area_m2', 0))
            spec_limit_mg_m2 = float(data.get('spec_limit_mg_m2', 0))

            if sample_area_m2 <= 0:
                return JsonResponse({'success': False, 'error': 'Sample area must be greater than 0'})

            calculator = LaminationCalculator()
            residual_mg_m2 = calculator.calculate_residual_solvent(solvent_detected_ug, sample_area_m2)

            result = {
                'residual_solvent_mg_m2': round(residual_mg_m2, 4),
                'solvent_detected_ug': solvent_detected_ug,
                'sample_area_m2': sample_area_m2
            }

            if spec_limit_mg_m2 > 0:
                result['spec_limit_mg_m2'] = spec_limit_mg_m2
                result['pass_fail'] = 'PASS' if residual_mg_m2 <= spec_limit_mg_m2 else 'FAIL'
                result['margin_mg_m2'] = round(spec_limit_mg_m2 - residual_mg_m2, 4)

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='RESIDUAL_SOLVENT',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENT_BASE'),
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_oee_rating(overall_efficiency_percent):
    if overall_efficiency_percent >= 85:
        return "World Class"
    elif overall_efficiency_percent >= 70:
        return "Good"
    elif overall_efficiency_percent >= 50:
        return "Fair - Improvement Needed"
    else:
        return "Poor - Investigate Root Causes"


@login_required
@csrf_exempt
def calculate_overall_line_efficiency(request):
    """Composite OEE-style KPI combining availability, production efficiency, and yield"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            total_run_time_min = float(data.get('total_run_time_min', 0))
            downtime_min = float(data.get('downtime_min', 0))
            lamination_time_min = float(data.get('lamination_time_min', 0))
            input_mass_kg = float(data.get('input_mass_kg', 0))
            output_mass_kg = float(data.get('output_mass_kg', 0))

            if total_run_time_min <= 0:
                return JsonResponse({'success': False, 'error': 'Total run time must be greater than 0'})
            if input_mass_kg <= 0:
                return JsonResponse({'success': False, 'error': 'Input mass must be greater than 0'})

            calculator = LaminationCalculator()

            availability_percent = calculator.calculate_availability_percent(total_run_time_min, downtime_min)
            production_efficiency_percent = calculator.calculate_production_efficiency(lamination_time_min, total_run_time_min)
            yield_percent = calculator.calculate_yield(input_mass_kg, output_mass_kg)

            overall_efficiency = calculator.calculate_overall_line_efficiency(
                availability_percent, production_efficiency_percent, yield_percent
            )

            result = {
                'availability_percent': round(availability_percent, 2),
                'production_efficiency_percent': round(production_efficiency_percent, 2),
                'yield_percent': round(yield_percent, 2),
                'overall_line_efficiency_percent': round(overall_efficiency, 2),
                'rating': get_oee_rating(overall_efficiency)
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='OVERALL_LINE_EFFICIENCY',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
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
def calculate_adhesive_coverage_per_roll(request):
    """Quick planning check: adhesive required for a given roll area at a target coat weight"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, job_name = resolve_common_fields(data)
            coat_weight_gsm = float(data.get('coat_weight_gsm', 0))
            roll_width = float(data.get('roll_width', 0))
            roll_width_unit = data.get('roll_width_unit', 'm')
            roll_length = float(data.get('roll_length', 0))
            roll_length_unit = data.get('roll_length_unit', 'm')

            if coat_weight_gsm <= 0 or roll_width <= 0 or roll_length <= 0:
                return JsonResponse({'success': False, 'error': 'Coat weight, roll width, and roll length must be greater than 0'})

            calculator = LaminationCalculator()
            roll_width_m = calculator.convert_length(roll_width, roll_width_unit, 'm')
            roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')
            roll_area_m2 = roll_width_m * roll_length_m

            adhesive_required_kg = calculator.calculate_adhesive_coverage_per_roll(coat_weight_gsm, roll_area_m2)

            result = {
                'roll_area_m2': round(roll_area_m2, 2),
                'adhesive_required_kg': round(adhesive_required_kg, 3),
                'coat_weight_gsm': coat_weight_gsm
            }

            if request.user.is_authenticated:
                LaminationCalculation.objects.create(
                    calculation_type='ADHESIVE_COVERAGE_PER_ROLL',
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    adhesive_type=data.get('adhesive_type', 'SOLVENTLESS'),
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
