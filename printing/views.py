from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import PrintingCalculation, InkFormula
from .printing_calculator import PrintingCalculator
import json


def safe_float(value, default=0.0):
    """Safely convert value to float, handling empty strings and invalid inputs."""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def resolve_common_fields(data):
    """Resolve optional material/machine/customer/job context shared across all printing calculators.
    Material here is single-layer only (a plain FK), not a laminate structure."""
    material = None
    material_id = data.get('material_id')
    if material_id:
        try:
            material = PlasticMaterial.objects.get(id=material_id)
        except PlasticMaterial.DoesNotExist:
            material = None
    machine_name = data.get('machine_name') or ''
    customer_name = data.get('customer_name') or ''
    job_name = data.get('job_name') or ''
    return material, machine_name, customer_name, job_name


@login_required
def printing_home(request):
    calculators = [
        {'id': 'film_mass_length', 'name': 'Film Mass & Length', 'icon': 'fas fa-weight-hanging'},
        {'id': 'ink_mass', 'name': 'Ink Mass Needed', 'icon': 'fas fa-tint'},
        {'id': 'machine_speed', 'name': 'Machine Speed & Time', 'icon': 'fas fa-tachometer-alt'},
        {'id': 'gsm_calculation', 'name': 'GSM Calculation', 'icon': 'fas fa-balance-scale'},
        {'id': 'ink_mixing', 'name': 'Ink Mixing', 'icon': 'fas fa-flask'},
        {'id': 'production_time', 'name': 'Production Time', 'icon': 'fas fa-clock'},
        {'id': 'anilox_coverage', 'name': 'Anilox Ink Coverage', 'icon': 'fas fa-water'},
        {'id': 'dot_gain_contrast', 'name': 'Dot Gain & Print Contrast', 'icon': 'fas fa-circle-notch'},
        {'id': 'delta_e', 'name': 'Color Difference (ΔE)', 'icon': 'fas fa-eye'},
        {'id': 'registration_repeat', 'name': 'Registration & Repeat Length', 'icon': 'fas fa-crosshairs'},
        {'id': 'residual_solvent', 'name': 'Residual Solvent', 'icon': 'fas fa-smog'},
        {'id': 'ink_waste_allowance', 'name': 'Ink Waste Allowance', 'icon': 'fas fa-recycle'},
        {'id': 'max_safe_speed', 'name': 'Max Safe Speed vs Drying', 'icon': 'fas fa-fire-alt'},
        {'id': 'cylinder_coverage', 'name': 'Gravure Cylinder Coverage', 'icon': 'fas fa-circle'},
        {'id': 'cylinder_wear_life', 'name': 'Cylinder Wear & Life', 'icon': 'fas fa-history'},
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                # Color mixing from first principles - every color expressed only
                # as a percentage blend of the real ink stations: C, M, Y, K, W
                target_color = data.get('target_color', 'Red')
                total_batch_kg = safe_float(data.get('color_batch_kg', 0))

                recipe_data = calculator.get_color_recipe(target_color)

                if not recipe_data:
                    result = {
                        'mixing_type': 'color_mixing',
                        'error': f'Recipe for {target_color} not found'
                    }
                else:
                    mixing_result = calculator.calculate_color_mixing_batch(total_batch_kg, target_color)
                    result = {
                        'mixing_type': 'color_mixing',
                        'target_color': target_color,
                        'category': mixing_result['category'],
                        'components': mixing_result['components'],
                        'total_batch_kg': total_batch_kg,
                        'requires_special_ink': mixing_result['requires_special_ink'],
                        'note': 'Every color is expressed only in terms of the real ink stations: Cyan, Magenta, Yellow, Black, and White.'
                    }
                    if mixing_result['requires_special_ink']:
                        result['metallic_name'] = mixing_result['metallic_name']
                        result['metallic_additive_percent'] = mixing_result['metallic_additive_percent']
                        result['metallic_additive_mass_kg'] = mixing_result['metallic_additive_mass_kg']
                        result['metallic_note'] = (
                            f"{mixing_result['metallic_name']} cannot be produced from CMYK+White process inks "
                            "alone - the hue base shown is for proofing only."
                        )

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='INK_MIXING',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
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
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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


@login_required
@csrf_exempt
def calculate_anilox_coverage(request):
    """Anilox volume -> wet ink film weight cross-check against target coverage"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            anilox_unit = data.get('anilox_unit', 'cm3_m2')  # 'cm3_m2' or 'bcm'
            anilox_volume = float(data.get('anilox_volume', 0))
            transfer_efficiency_percent = float(data.get('transfer_efficiency_percent', 60))
            ink_density = float(data.get('ink_density', 1.4))
            target_gsm = safe_float(data.get('target_gsm', 0))

            if anilox_volume <= 0:
                return JsonResponse({'success': False, 'error': 'Anilox volume must be greater than 0'})

            # 1 BCM (billion cubic microns per in^2) ~= 1.55 cm3/m2
            anilox_volume_cm3_m2 = anilox_volume * 1.55 if anilox_unit == 'bcm' else anilox_volume

            wet_film_weight_gsm = calculator.calculate_wet_film_weight_from_anilox(
                anilox_volume_cm3_m2, transfer_efficiency_percent, ink_density
            )

            result = {
                'wet_film_weight_gsm': round(wet_film_weight_gsm, 4),
                'anilox_volume_cm3_m2': round(anilox_volume_cm3_m2, 4),
                'transfer_efficiency_percent': transfer_efficiency_percent,
                'ink_density_g_cm3': ink_density
            }

            if target_gsm > 0:
                deviation_percent = ((wet_film_weight_gsm - target_gsm) / target_gsm) * 100
                result['target_gsm'] = target_gsm
                result['deviation_percent'] = round(deviation_percent, 2)

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='ANILOX_COVERAGE',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_dot_gain_rating(dot_gain_percent):
    abs_gain = abs(dot_gain_percent)
    if abs_gain < 8:
        return "Within typical tolerance"
    elif abs_gain < 15:
        return "Elevated - monitor plate/anilox wear"
    else:
        return "High dot gain - check plate pressure, anilox, or ink viscosity"


@login_required
@csrf_exempt
def calculate_dot_gain_contrast(request):
    """Dot gain and print contrast quality checks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            measured_dot_area = float(data.get('measured_dot_area', 0))
            nominal_dot_area = float(data.get('nominal_dot_area', 0))
            solid_density = safe_float(data.get('solid_density', 0))
            shadow_density = safe_float(data.get('shadow_density', 0))

            dot_gain_percent = calculator.calculate_dot_gain(measured_dot_area, nominal_dot_area)

            result = {
                'dot_gain_percent': round(dot_gain_percent, 2),
                'measured_dot_area_percent': measured_dot_area,
                'nominal_dot_area_percent': nominal_dot_area,
                'dot_gain_rating': get_dot_gain_rating(dot_gain_percent)
            }

            if solid_density > 0:
                print_contrast_percent = calculator.calculate_print_contrast(solid_density, shadow_density)
                result['print_contrast_percent'] = round(print_contrast_percent, 2)
                result['solid_density'] = solid_density
                result['shadow_density'] = shadow_density

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='DOT_GAIN_CONTRAST',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_delta_e_rating(delta_e):
    if delta_e < 1:
        return "Not perceptible to the human eye"
    elif delta_e < 2:
        return "Perceptible only on close inspection"
    elif delta_e < 3.5:
        return "Perceptible at a glance"
    elif delta_e < 5:
        return "Clearly noticeable difference"
    else:
        return "Colors appear distinctly different"


@login_required
@csrf_exempt
def calculate_delta_e(request):
    """CIE76 Delta E color difference check against a tolerance"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            L1 = float(data.get('L1', 0))
            a1 = float(data.get('a1', 0))
            b1 = float(data.get('b1', 0))
            L2 = float(data.get('L2', 0))
            a2 = float(data.get('a2', 0))
            b2 = float(data.get('b2', 0))
            tolerance = float(data.get('tolerance', 2.0))

            delta_e = calculator.calculate_delta_e_cie76(L1, a1, b1, L2, a2, b2)

            result = {
                'delta_e': round(delta_e, 3),
                'tolerance': tolerance,
                'pass_fail': 'PASS' if delta_e <= tolerance else 'FAIL',
                'rating': get_delta_e_rating(delta_e)
            }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='DELTA_E',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
def calculate_registration_repeat(request):
    """Print registration error and cylinder repeat length deviation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            measured_position = safe_float(data.get('measured_position', 0))
            target_position = safe_float(data.get('target_position', 0))
            actual_repeat = safe_float(data.get('actual_repeat', 0))
            cylinder_circumference = safe_float(data.get('cylinder_circumference', 0))

            result = {}

            if measured_position or target_position:
                registration_error_mm = calculator.calculate_registration_error(measured_position, target_position)
                result['registration_error_mm'] = round(registration_error_mm, 3)

            if actual_repeat > 0 and cylinder_circumference > 0:
                repeat_deviation_percent = calculator.calculate_repeat_length_deviation(
                    actual_repeat, cylinder_circumference
                )
                result['repeat_length_deviation_percent'] = round(repeat_deviation_percent, 3)
                result['actual_repeat_mm'] = actual_repeat
                result['cylinder_circumference_mm'] = cylinder_circumference

            if not result:
                return JsonResponse({'success': False, 'error': 'Provide registration positions and/or repeat length data'})

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='REGISTRATION_REPEAT',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
def calculate_residual_solvent_printing(request):
    """Residual solvent (mg/m2) for solvent-based printing compliance checks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            solvent_detected_ug = float(data.get('solvent_detected_ug', 0))
            sample_area_m2 = float(data.get('sample_area_m2', 0))
            spec_limit_mg_m2 = safe_float(data.get('spec_limit_mg_m2', 0))

            if sample_area_m2 <= 0:
                return JsonResponse({'success': False, 'error': 'Sample area must be greater than 0'})

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
                PrintingCalculation.objects.create(
                    calculation_type='RESIDUAL_SOLVENT',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
def calculate_ink_waste_allowance(request):
    """Waste-adjusted mass planning for ink batches"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            net_mass = float(data.get('net_mass', 0))
            net_mass_unit = data.get('net_mass_unit', 'kg')
            waste_percent = float(data.get('waste_percent', 5.0))

            if net_mass <= 0:
                return JsonResponse({'success': False, 'error': 'Net mass must be greater than 0'})

            net_mass_kg = convert_mass(net_mass, net_mass_unit, 'kg')
            outcome = calculator.apply_waste_allowance(net_mass_kg, waste_percent)

            result = {
                'net_mass_kg': round(outcome['net_kg'], 3),
                'waste_percent': waste_percent,
                'waste_mass_kg': round(outcome['waste_kg'], 3),
                'gross_mass_kg': round(outcome['gross_kg'], 3)
            }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='WASTE_ALLOWANCE',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
def calculate_max_safe_speed(request):
    """Max safe machine speed given dryer/oven length and required dwell time"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            dryer_length = float(data.get('dryer_length', 0))
            dryer_length_unit = data.get('dryer_length_unit', 'm')
            dwell_time = float(data.get('dwell_time', 0))
            dwell_time_unit = data.get('dwell_time_unit', 'sec')
            requested_speed = safe_float(data.get('requested_speed', 0))
            requested_speed_unit = data.get('requested_speed_unit', 'm_min')

            if dryer_length <= 0 or dwell_time <= 0:
                return JsonResponse({'success': False, 'error': 'Dryer length and dwell time must be greater than 0'})

            dryer_length_m = convert_length(dryer_length, dryer_length_unit, 'm')
            dwell_time_min = convert_time(dwell_time, dwell_time_unit, 'min')

            max_safe_speed_m_min = calculator.calculate_max_safe_speed(dryer_length_m, dwell_time_min)

            result = {
                'max_safe_speed_m_min': round(max_safe_speed_m_min, 2),
                'max_safe_speed_m_hr': round(max_safe_speed_m_min * 60, 2),
                'dryer_length_m': round(dryer_length_m, 2),
                'dwell_time_min': round(dwell_time_min, 4)
            }

            if requested_speed > 0:
                requested_speed_m_min = convert_speed(requested_speed, requested_speed_unit, 'm_min')
                result['requested_speed_m_min'] = round(requested_speed_m_min, 2)
                result['within_safe_limit'] = requested_speed_m_min <= max_safe_speed_m_min
                result['note'] = (
                    'Requested speed is within safe drying/curing capacity'
                    if requested_speed_m_min <= max_safe_speed_m_min
                    else 'Requested speed exceeds safe drying/curing capacity - risk of incomplete cure'
                )

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='MAX_SAFE_SPEED',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
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
def calculate_cylinder_coverage(request):
    """Rotogravure cylinder coverage, revolutions, and ink consumption for a job"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            diameter = float(data.get('diameter', 0))
            diameter_unit = data.get('diameter_unit', 'mm')
            face_width = float(data.get('face_width', 0))
            face_width_unit = data.get('face_width_unit', 'mm')
            job_length = float(data.get('job_length', 0))
            job_length_unit = data.get('job_length_unit', 'm')
            coverage_mode = data.get('coverage_mode', 'image_area')  # 'image_area' or 'coverage_percent'
            image_area = safe_float(data.get('image_area', 0))
            image_area_unit = data.get('image_area_unit', 'm2')
            coverage_percent_input = safe_float(data.get('coverage_percent', 0))
            cell_volume = float(data.get('cell_volume', 0))
            cell_volume_unit = data.get('cell_volume_unit', 'cm3_m2')
            ink_density = float(data.get('ink_density', 1.4))

            if diameter <= 0 or face_width <= 0 or job_length <= 0:
                return JsonResponse({'success': False, 'error': 'Diameter, face width, and job length must be greater than 0'})

            diameter_mm = convert_length(diameter, diameter_unit, 'mm')
            diameter_m = diameter_mm / 1000
            face_width_m = convert_length(face_width, face_width_unit, 'm')
            job_length_m = convert_length(job_length, job_length_unit, 'm')

            circumference_mm = calculator.calculate_cylinder_circumference(diameter_mm)
            circumference_m = circumference_mm / 1000
            surface_area_m2 = calculator.calculate_cylinder_surface_area(diameter_m, face_width_m)

            if coverage_mode == 'coverage_percent':
                if coverage_percent_input <= 0:
                    return JsonResponse({'success': False, 'error': 'Provide a coverage percent greater than 0'})
                image_area_m2 = surface_area_m2 * (coverage_percent_input / 100)
                coverage_percent = coverage_percent_input
            else:
                if image_area <= 0:
                    return JsonResponse({'success': False, 'error': 'Provide an image/engraved area greater than 0'})
                image_area_m2 = convert_area(image_area, image_area_unit, 'm2')
                coverage_percent = calculator.calculate_cylinder_coverage_percent(image_area_m2, surface_area_m2)

            revolutions = calculator.calculate_cylinder_revolutions(job_length_m, circumference_m)

            # 1 BCM (billion cubic microns per in^2) ~= 1.55 cm3/m2
            cell_volume_cm3_m2 = cell_volume * 1.55 if cell_volume_unit == 'bcm' else cell_volume

            ink_volume_per_rev_cm3 = calculator.calculate_ink_volume_per_revolution(cell_volume_cm3_m2, image_area_m2)
            ink_mass_per_rev_g = calculator.calculate_ink_mass_per_revolution(ink_volume_per_rev_cm3, ink_density)
            total_ink_kg = calculator.calculate_total_ink_consumption(ink_mass_per_rev_g, revolutions)

            result = {
                'circumference_mm': round(circumference_mm, 2),
                'circumference_m': round(circumference_m, 4),
                'surface_area_m2': round(surface_area_m2, 4),
                'image_area_m2': round(image_area_m2, 4),
                'coverage_percent': round(coverage_percent, 2),
                'revolutions': round(revolutions, 1),
                'ink_volume_per_rev_cm3': round(ink_volume_per_rev_cm3, 4),
                'ink_mass_per_rev_g': round(ink_mass_per_rev_g, 4),
                'total_ink_kg': round(total_ink_kg, 4),
                'job_length_m': round(job_length_m, 2)
            }

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='CYLINDER_COVERAGE',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_cylinder_wear_rating(depletion_percent):
    if depletion_percent < 5:
        return "Good - within normal wear"
    elif depletion_percent < 10:
        return "Moderate wear - monitor closely"
    elif depletion_percent < 15:
        return "High wear - plan re-engraving/re-chroming soon"
    else:
        return "Critical wear - re-engrave/re-chrome before next job"


@login_required
@csrf_exempt
def calculate_cylinder_wear_life(request):
    """Cylinder cell-volume depletion (wear) and max job length per cylinder life"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material, machine_name, customer_name, job_name = resolve_common_fields(data)
            calculator = PrintingCalculator()

            original_cell_volume = float(data.get('original_cell_volume', 0))
            current_cell_volume = float(data.get('current_cell_volume', 0))
            rated_life_revolutions = safe_float(data.get('rated_life_revolutions', 0))
            diameter = safe_float(data.get('diameter', 0))
            diameter_unit = data.get('diameter_unit', 'mm')

            if original_cell_volume <= 0:
                return JsonResponse({'success': False, 'error': 'Original cell volume must be greater than 0'})

            depletion_percent = calculator.calculate_cell_volume_depletion(original_cell_volume, current_cell_volume)

            result = {
                'cell_volume_depletion_percent': round(depletion_percent, 2),
                'original_cell_volume': original_cell_volume,
                'current_cell_volume': current_cell_volume,
                'wear_rating': get_cylinder_wear_rating(depletion_percent)
            }

            if rated_life_revolutions > 0 and diameter > 0:
                diameter_mm = convert_length(diameter, diameter_unit, 'mm')
                circumference_m = calculator.calculate_cylinder_circumference(diameter_mm) / 1000
                max_job_length_m = calculator.calculate_max_job_length_per_cylinder_life(rated_life_revolutions, circumference_m)
                result['circumference_m'] = round(circumference_m, 4)
                result['max_job_length_m'] = round(max_job_length_m, 1)
                result['max_job_length_km'] = round(max_job_length_m / 1000, 3)

            if request.user.is_authenticated:
                PrintingCalculation.objects.create(
                    calculation_type='CYLINDER_WEAR_LIFE',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    job_name=job_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
