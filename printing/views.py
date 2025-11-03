from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import PrintingCalculation, InkFormula
from .printing_calculator import PrintingCalculator
import json


@login_required
def printing_home(request):
    calculators = [
        {'id': 'film_mass_length', 'name': 'Film Mass & Length', 'icon': 'fas fa-weight-hanging'},
        {'id': 'ink_mass', 'name': 'Ink Mass Needed', 'icon': 'fas fa-tint'},
        {'id': 'machine_speed', 'name': 'Machine Speed & Time', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'gsm_calculation', 'name': 'GSM Calculation', 'icon': 'fas fa-balance-scale'},
        {'id': 'ink_mixing', 'name': 'Ink Mixing', 'icon': 'fas fa-flask'},
        {'id': 'production_time', 'name': 'Production Time', 'icon': 'fas fa-clock'},
    ]

    materials = PlasticMaterial.objects.filter(material_type='FILM')
    ink_formulas = InkFormula.objects.all()

    return render(request, 'printing/home.html', {
        'section_name': 'Printing',
        'calculators': calculators,
        'materials': materials,
        'ink_formulas': ink_formulas
    })


@login_required
@csrf_exempt
def calculate_film_mass_length(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'mass')  # 'mass' or 'length'
            material_id = data.get('material_id')

            material = PlasticMaterial.objects.get(id=material_id)
            calculator = PrintingCalculator()

            if calculation_type == 'mass':
                # Calculate mass from length
                width = float(data.get('width', 0))
                width_unit = data.get('width_unit', 'm')
                length = float(data.get('length', 0))
                length_unit = data.get('length_unit', 'm')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                # Convert to base units
                width_m = convert_length(width, width_unit, 'm')
                length_m = convert_length(length, length_unit, 'm')
                thickness_um = convert_thickness(thickness, thickness_unit, 'micron')

                film_mass_kg = calculator.calculate_film_mass(width_m, length_m, thickness_um, material.density)

                result = {
                    'film_mass_kg': round(film_mass_kg, 3),
                    'film_mass_g': round(film_mass_kg * 1000, 1),
                    'film_mass_lb': round(film_mass_kg * 2.20462, 3),
                    'calculation_type': 'mass'
                }

            else:
                # Calculate length from mass
                width = float(data.get('width', 0))
                width_unit = data.get('width_unit', 'm')
                mass = float(data.get('mass', 0))
                mass_unit = data.get('mass_unit', 'kg')
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                # Convert to base units
                width_m = convert_length(width, width_unit, 'm')
                mass_kg = convert_mass(mass, mass_unit, 'kg')
                thickness_um = convert_thickness(thickness, thickness_unit, 'micron')

                film_length_m = calculator.calculate_film_length(mass_kg, width_m, thickness_um, material.density)

                result = {
                    'film_length_m': round(film_length_m, 2),
                    'film_length_ft': round(film_length_m * 3.28084, 2),
                    'film_length_yd': round(film_length_m * 1.09361, 2),
                    'calculation_type': 'length'
                }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='FILM_MASS_LENGTH',
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
def calculate_ink_mass_needed(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            film_width = float(data.get('film_width', 0))
            film_width_unit = data.get('film_width_unit', 'm')
            film_length = float(data.get('film_length', 0))
            film_length_unit = data.get('film_length_unit', 'm')
            coverage_percent = float(data.get('coverage_percent', 0))
            ink_coverage_gsm = float(data.get('ink_coverage_gsm', 1.0))
            ink_density = float(data.get('ink_density', 1.4))

            calculator = PrintingCalculator()

            # Convert to base units
            film_width_m = convert_length(film_width, film_width_unit, 'm')
            film_length_m = convert_length(film_length, film_length_unit, 'm')

            # Calculate ink mass
            ink_mass_kg = calculator.calculate_ink_mass_needed(
                film_width_m, film_length_m, coverage_percent, ink_coverage_gsm
            )

            # Calculate ink volume
            ink_volume_L = calculator.calculate_ink_volume(ink_mass_kg, ink_density)

            result = {
                'ink_mass_kg': round(ink_mass_kg, 3),
                'ink_mass_g': round(ink_mass_kg * 1000, 1),
                'ink_volume_L': round(ink_volume_L, 3),
                'coverage_percent': coverage_percent,
                'total_area_m2': round(film_width_m * film_length_m, 2),
                'printed_area_m2': round(film_width_m * film_length_m * (coverage_percent / 100), 2)
            }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='INK_MASS',
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
def calculate_machine_speed_time(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'speed')  # 'speed' or 'time'
            calculator = PrintingCalculator()

            if calculation_type == 'speed':
                # Calculate speed from length and time
                length = float(data.get('length', 0))
                length_unit = data.get('length_unit', 'm')
                run_time = float(data.get('run_time', 0))
                run_time_unit = data.get('run_time_unit', 'min')

                length_m = convert_length(length, length_unit, 'm')
                run_time_min = convert_time(run_time, run_time_unit, 'min')

                speed_m_min = calculator.calculate_machine_speed(length_m, run_time_min)

                result = {
                    'speed_m_min': round(speed_m_min, 2),
                    'speed_m_hr': round(speed_m_min * 60, 2),
                    'speed_ft_min': round(speed_m_min * 3.28084, 2),
                    'calculation_type': 'speed'
                }

            else:
                # Calculate time from length and speed
                total_length = float(data.get('total_length', 0))
                total_length_unit = data.get('total_length_unit', 'm')
                machine_speed = float(data.get('machine_speed', 0))
                machine_speed_unit = data.get('machine_speed_unit', 'm_min')

                total_length_m = convert_length(total_length, total_length_unit, 'm')
                machine_speed_m_min = convert_speed(machine_speed, machine_speed_unit, 'm_min')

                production_time = calculator.calculate_production_time(total_length_m, machine_speed_m_min)

                result = {
                    'time_minutes': round(production_time['minutes'], 2),
                    'time_hours': round(production_time['hours'], 2),
                    'time_days': round(production_time['days'], 2),
                    'calculation_type': 'time'
                }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='MACHINE_SPEED',
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
def calculate_gsm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            method = data.get('method', 'calculation')  # 'calculation' or 'cut_method'
            calculator = PrintingCalculator()

            if method == 'calculation':
                # Calculate GSM from thickness and density - CORRECT FORMULA
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')
                density = float(data.get('density', 0))

                thickness_um = convert_thickness(thickness, thickness_unit, 'micron')

                # CORRECT CALCULATION: GSM = Thickness (µm) × Density (g/cm³)
                gsm = calculator.calculate_gsm_from_dimensions(thickness_um, density)

                # Calculate expected values for common thicknesses for reference
                common_thicknesses = [10, 12, 15, 20, 25, 30, 40, 50]
                reference_values = []
                for thick in common_thicknesses:
                    ref_gsm = calculator.calculate_gsm_from_dimensions(thick, density)
                    reference_values.append({
                        'thickness': thick,
                        'gsm': round(ref_gsm, 2)
                    })

                result = {
                    'gsm': round(gsm, 4),
                    'method': 'calculation',
                    'thickness_um': thickness_um,
                    'density': density,
                    'calculation_used': f'{thickness_um} µm × {density} g/cm³ = {gsm:.4f} g/m²',
                    'reference_values': reference_values
                }

            else:
                # Calculate GSM from cut method
                sample_mass = float(data.get('sample_mass', 0))
                sample_mass_unit = data.get('sample_mass_unit', 'g')
                sample_area = float(data.get('sample_area', 0))
                sample_area_unit = data.get('sample_area_unit', 'cm2')

                sample_mass_g = convert_mass(sample_mass, sample_mass_unit, 'g')
                sample_area_cm2 = convert_area(sample_area, sample_area_unit, 'cm2')

                gsm = calculator.calculate_gsm_cut_method(sample_mass_g, sample_area_cm2)

                result = {
                    'gsm': round(gsm, 4),
                    'method': 'cut_method',
                    'sample_mass_g': sample_mass_g,
                    'sample_area_cm2': sample_area_cm2,
                    'calculation_used': f'{sample_mass_g} g ÷ {sample_area_cm2 / 10000:.6f} m² = {gsm:.4f} g/m²'
                }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='GSM_CALCULATION',
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
def calculate_ink_mixing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mixing_type = data.get('mixing_type', 'batch')  # 'batch', 'viscosity', 'secondary'
            calculator = PrintingCalculator()

            if mixing_type == 'batch':
                # Calculate ink mixing batch
                total_batch_kg = float(data.get('total_batch_kg', 0))
                pigment_pct = float(data.get('pigment_pct', 0))
                binder_pct = float(data.get('binder_pct', 0))
                additives_pct = float(data.get('additives_pct', 0))
                solvent_pct = float(data.get('solvent_pct', 0))

                formula = {
                    'pigment_pct': pigment_pct,
                    'binder_pct': binder_pct,
                    'additives_pct': additives_pct,
                    'solvent_pct': solvent_pct
                }

                batch_components = calculator.calculate_ink_mixing_batch(total_batch_kg, formula)

                result = {
                    'mixing_type': 'batch',
                    'components': batch_components,
                    'formula': formula
                }

            elif mixing_type == 'viscosity':
                # Viscosity adjustment
                current_viscosity = float(data.get('current_viscosity', 0))
                target_viscosity = float(data.get('target_viscosity', 0))
                current_mass = float(data.get('current_mass', 0))
                current_mass_unit = data.get('current_mass_unit', 'kg')

                current_mass_kg = convert_mass(current_mass, current_mass_unit, 'kg')
                solvent_needed_kg = calculator.calculate_viscosity_adjustment(
                    current_viscosity, target_viscosity, current_mass_kg
                )

                result = {
                    'mixing_type': 'viscosity',
                    'solvent_needed_kg': round(solvent_needed_kg, 3),
                    'solvent_needed_L': round(solvent_needed_kg, 3),  # Assuming solvent density ~1 kg/L
                    'new_total_mass_kg': round(current_mass_kg + solvent_needed_kg, 3),
                    'dilution_ratio': round(solvent_needed_kg / current_mass_kg, 3) if current_mass_kg > 0 else 0
                }

            else:
                # Secondary color mixing from CMYK
                secondary_recipes = calculator.mix_secondary_color(['Cyan', 'Magenta', 'Yellow', 'Black'])
                target_color = data.get('target_color', 'Red')

                if target_color in secondary_recipes:
                    recipe = secondary_recipes[target_color]
                    result = {
                        'mixing_type': 'secondary',
                        'target_color': target_color,
                        'recipe': recipe,
                        'note': 'Percentages are relative to total color composition'
                    }
                else:
                    result = {
                        'mixing_type': 'secondary',
                        'error': f'Recipe for {target_color} not found'
                    }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='INK_MIXING',
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
def calculate_production_time_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            total_order_length = float(data.get('total_order_length', 0))
            total_order_length_unit = data.get('total_order_length_unit', 'm')
            machine_speed = float(data.get('machine_speed', 0))
            machine_speed_unit = data.get('machine_speed_unit', 'm_min')
            setup_time = float(data.get('setup_time', 0))
            setup_time_unit = data.get('setup_time_unit', 'min')
            efficiency_percent = float(data.get('efficiency_percent', 85))

            calculator = PrintingCalculator()

            # Convert to base units
            total_length_m = convert_length(total_order_length, total_order_length_unit, 'm')
            machine_speed_m_min = convert_speed(machine_speed, machine_speed_unit, 'm_min')
            setup_time_min = convert_time(setup_time, setup_time_unit, 'min')

            # Calculate net production time
            net_production_min = total_length_m / machine_speed_m_min

            # Adjust for efficiency
            actual_production_min = net_production_min / (efficiency_percent / 100)

            # Add setup time
            total_time_min = actual_production_min + setup_time_min

            result = {
                'net_production_min': round(net_production_min, 2),
                'actual_production_min': round(actual_production_min, 2),
                'total_time_min': round(total_time_min, 2),
                'total_time_hr': round(total_time_min / 60, 2),
                'total_time_days': round(total_time_min / 60 / 24, 2),
                'efficiency_percent': efficiency_percent,
                'setup_time_min': setup_time_min
            }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='PRODUCTION_TIME',
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Utility conversion functions
def convert_length(value, from_unit, to_unit):
    conversions = {
        'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'inch': 0.0254, 'ft': 0.3048
    }
    return value * conversions[from_unit] / conversions[to_unit]


def convert_mass(value, from_unit, to_unit):
    conversions = {
        'g': 0.001, 'kg': 1.0, 'lb': 0.453592
    }
    return value * conversions[from_unit] / conversions[to_unit]


def convert_thickness(value, from_unit, to_unit):
    conversions = {
        'micron': 1.0, 'mm': 1000.0, 'mil': 25.4
    }
    return value * conversions[from_unit] / conversions[to_unit]


def convert_time(value, from_unit, to_unit):
    conversions = {
        'sec': 1 / 60, 'min': 1.0, 'hr': 60.0
    }
    return value * conversions[from_unit] / conversions[to_unit]


def convert_speed(value, from_unit, to_unit):
    conversions = {
        'm_min': 1.0, 'm_hr': 1 / 60, 'ft_min': 0.3048
    }
    return value * conversions[from_unit] / conversions[to_unit]


def convert_area(value, from_unit, to_unit):
    conversions = {
        'cm2': 1.0, 'm2': 10000.0, 'inch2': 6.4516
    }
    return value * conversions[from_unit] / conversions[to_unit]


@login_required
def printing_history(request):
    """Display printing calculation history for authenticated users"""
    calculations = PrintingCalculation.objects.filter(user=request.user).select_related('material').order_by(
        '-timestamp')
    return render(request, 'printing/history.html', {'calculations': calculations})
