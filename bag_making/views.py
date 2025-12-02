from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import BagMakingCalculation
from .bag_calculator import BagMakingCalculator
import json


@login_required
def bag_making_home(request):
    calculators = [
        {'id': 'pieces_weight', 'name': 'Pieces ↔ Weight Converter', 'icon': 'fas fa-exchange-alt'},
        {'id': 'packet_weight', 'name': 'Packet Weight Calculator', 'icon': 'fas fa-box'},
        {'id': 'bundle_weight', 'name': 'Bundle/Bale Weight Calculator', 'icon': 'fas fa-pallet'},
        {'id': 'production_time', 'name': 'Production Time & Efficiency', 'icon': 'fas fa-clock'},
    ]

    bag_types = [
        ('FLAT_SHEET', 'Flat Sheet Bag'),
        ('TUBULAR', 'Tubular Bag'),
        ('GUSSETED', 'Gusseted Bag'),
        ('LAMINATED_FLAT', 'Laminated Flat Bag'),
        ('LAMINATED_TUBULAR', 'Laminated Tubular Bag'),
        ('LAMINATED_GUSSETED', 'Laminated Gusseted Bag'),
    ]

    materials = PlasticMaterial.objects.filter(material_type='FILM')

    return render(request, 'bag_making/home.html', {
        'section_name': 'Bag Making',
        'calculators': calculators,
        'bag_types': bag_types,
        'materials': materials
    })


@login_required
@csrf_exempt
def calculate_pieces_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_direction = data.get('calculation_direction', 'pieces_to_weight')
            bag_type = data.get('bag_type', 'FLAT_SHEET')

            calculator = BagMakingCalculator()

            # Get dimensions
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'cm')
            height = float(data.get('height', 0))
            height_unit = data.get('height_unit', 'cm')
            gusset_width = float(data.get('gusset_width', 0))
            gusset_unit = data.get('gusset_unit', 'cm')

            # Calculate area
            area_m2 = calculator.calculate_single_piece_area(
                width, height, bag_type, gusset_width,
                width_unit, height_unit, gusset_unit
            )

            # Calculate GSM based on material type
            if bag_type.startswith('LAMINATED'):
                # For laminated bags, use composite GSM
                layers_data = data.get('layers', [])
                if not layers_data:
                    return JsonResponse({'success': False, 'error': 'No layers provided for laminated bag'})

                composite_gsm = calculator.calculate_composite_gsm(layers_data)
            else:
                # For single layer bags
                material_id = data.get('material_id')
                if not material_id:
                    return JsonResponse({'success': False, 'error': 'Material required for single layer bag'})

                material = PlasticMaterial.objects.get(id=material_id)
                thickness = float(data.get('thickness', 0))
                thickness_unit = data.get('thickness_unit', 'micron')

                thickness_m = calculator.convert_thickness(thickness, thickness_unit, 'm')
                thickness_um = thickness_m * 1e6

                composite_gsm = calculator.calculate_gsm_from_thickness(thickness_um, material.density)

            # Calculate single piece weight
            single_piece_weight_g = calculator.calculate_single_piece_weight(area_m2, composite_gsm)

            if calculation_direction == 'pieces_to_weight':
                num_pieces = int(data.get('num_pieces', 0))
                output_unit = data.get('output_unit', 'kg')

                total_weight = calculator.calculate_pieces_to_weight(
                    num_pieces, single_piece_weight_g, output_unit
                )

                result = {
                    'single_piece_weight_g': round(single_piece_weight_g, 4),
                    'total_weight': round(total_weight, 4),
                    'output_unit': output_unit,
                    'num_pieces': num_pieces,
                    'calculation_type': 'pieces_to_weight',
                    'area_m2': round(area_m2, 6),
                    'composite_gsm': round(composite_gsm, 2)
                }
            else:
                total_weight = float(data.get('total_weight', 0))
                weight_unit = data.get('weight_unit', 'kg')

                num_pieces = calculator.calculate_weight_to_pieces(
                    total_weight, single_piece_weight_g, weight_unit
                )

                result = {
                    'single_piece_weight_g': round(single_piece_weight_g, 4),
                    'num_pieces': num_pieces,
                    'total_weight': total_weight,
                    'weight_unit': weight_unit,
                    'calculation_type': 'weight_to_pieces',
                    'area_m2': round(area_m2, 6),
                    'composite_gsm': round(composite_gsm, 2)
                }

            # Save calculation
            if request.user.is_authenticated:
                BagMakingCalculation.objects.create(
                    calculation_type='PIECES_WEIGHT',
                    bag_type=bag_type,
                    material=material if not bag_type.startswith('LAMINATED') else PlasticMaterial.objects.first(),
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
def calculate_packet_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_direction = data.get('calculation_direction', 'forward')
            input_method = data.get('input_method', 'direct_weight')

            calculator = BagMakingCalculator()
            result = {}

            if input_method == 'dimensions':
                # Calculate from dimensions
                result = calculate_packet_weight_from_dimensions_data(data, calculator)
            else:
                # Direct weight input
                result = calculate_packet_weight_from_direct_data(data, calculator)

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                BagMakingCalculation.objects.create(
                    calculation_type='PACKET_WEIGHT',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def calculate_packet_weight_from_dimensions_data(data, calculator):
    """Calculate packet weight from bag dimensions"""
    calculation_direction = data.get('calculation_direction', 'forward')

    # Extract dimensions data
    bag_type = data.get('dimensions_bag_type', 'FLAT_SHEET')
    width = float(data.get('dimensions_width', 0))
    height = float(data.get('dimensions_height', 0))
    gusset_width = float(data.get('dimensions_gusset_width', 0))
    width_unit = data.get('dimensions_width_unit', 'cm')
    height_unit = data.get('dimensions_height_unit', 'cm')
    gusset_unit = data.get('dimensions_gusset_unit', 'cm')
    pieces_per_packet = int(data.get('dimensions_pieces_per_packet', 0))
    packet_packaging_weight = float(data.get('dimensions_packet_packaging_weight', 0))
    packaging_unit = data.get('dimensions_packaging_unit', 'g')
    output_unit = data.get('output_unit', 'kg')

    # Calculate area
    area_m2 = calculator.calculate_single_piece_area(
        width, height, bag_type, gusset_width,
        width_unit, height_unit, gusset_unit
    )

    # Calculate GSM based on material type
    if bag_type.startswith('LAMINATED'):
        layers_data = []
        layer_index = 0
        while f'dimensions_layer_material_{layer_index}' in data:
            material_id = data.get(f'dimensions_layer_material_{layer_index}')
            thickness = float(data.get(f'dimensions_layer_thickness_{layer_index}', 0))
            thickness_unit = data.get(f'dimensions_layer_thickness_unit_{layer_index}', 'micron')

            if material_id and thickness:
                try:
                    material = PlasticMaterial.objects.get(id=material_id)
                    layers_data.append({
                        'thickness_microns': thickness,
                        'density_g_cm3': material.density,
                        'thickness_unit': thickness_unit
                    })
                except PlasticMaterial.DoesNotExist:
                    pass
            layer_index += 1

        if not layers_data:
            raise ValueError('No valid layers provided for laminated bag')

        composite_gsm = calculator.calculate_composite_gsm(layers_data)
    else:
        material_id = data.get('dimensions_material_id')
        if not material_id:
            raise ValueError('Material required for single layer bag')

        material = PlasticMaterial.objects.get(id=material_id)
        thickness = float(data.get('dimensions_thickness', 0))
        thickness_unit = data.get('dimensions_thickness_unit', 'micron')

        thickness_m = calculator.convert_thickness(thickness, thickness_unit, 'm')
        thickness_um = thickness_m * 1e6

        composite_gsm = calculator.calculate_gsm_from_thickness(thickness_um, material.density)

    # Calculate single piece weight
    single_piece_weight_g = calculator.calculate_single_piece_weight(area_m2, composite_gsm)

    # Calculate packet weight
    if calculation_direction == 'forward':
        packet_result = calculator.calculate_packet_weight(
            pieces_per_packet, single_piece_weight_g,
            packet_packaging_weight, packaging_unit, output_unit
        )

        result = {
            'calculation_type': 'forward',
            'from_dimensions': True,
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'pieces_per_packet': pieces_per_packet,
            'area_m2': round(area_m2, 6),
            'composite_gsm': round(composite_gsm, 2),
            'gross_weight': packet_result['gross_weight'],
            'net_weight': packet_result['net_weight'],
            'packaging_weight': packet_result['packaging_weight'],
            'packaging_percentage': packet_result['packaging_percentage'],
            'total_piece_weight_g': packet_result['total_piece_weight_g'],
            'output_unit': output_unit,
            'packaging_unit': 'g'
        }
    else:
        # Reverse calculation
        packet_weight = float(data.get('packet_weight', 0))
        weight_unit = data.get('weight_unit', 'kg')

        reverse_result = calculator.reverse_calculate_from_packet_weight(
            packet_weight, pieces_per_packet,
            packet_packaging_weight, packaging_unit, weight_unit
        )

        result = {
            'calculation_type': 'reverse',
            'from_dimensions': True,
            'packet_weight': packet_weight,
            'weight_unit': weight_unit,
            'pieces_per_packet': pieces_per_packet,
            'area_m2': round(area_m2, 6),
            'composite_gsm': round(composite_gsm, 2),
            'single_piece_weight_g': reverse_result['single_piece_weight_g'],
            'net_bag_weight_g': reverse_result['net_bag_weight_g'],
            'gross_packet_weight_g': reverse_result['gross_packet_weight_g'],
            'packaging_weight_g': reverse_result['packaging_weight_g'],
            'packaging_percentage': reverse_result['packaging_percentage']
        }

    return result


def calculate_packet_weight_from_direct_data(data, calculator):
    """Calculate packet weight from direct weight input"""
    calculation_direction = data.get('calculation_direction', 'forward')

    if calculation_direction == 'forward':
        single_piece_weight_g = float(data.get('single_piece_weight_g', 0))
        pieces_per_packet = int(data.get('pieces_per_packet', 0))
        packet_packaging_weight = float(data.get('packet_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'g')
        output_unit = data.get('output_unit', 'kg')

        packet_result = calculator.calculate_packet_weight(
            pieces_per_packet, single_piece_weight_g,
            packet_packaging_weight, packaging_unit, output_unit
        )

        result = {
            'calculation_type': 'forward',
            'from_dimensions': False,
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'pieces_per_packet': pieces_per_packet,
            'gross_weight': packet_result['gross_weight'],
            'net_weight': packet_result['net_weight'],
            'packaging_weight': packet_result['packaging_weight'],
            'packaging_percentage': packet_result['packaging_percentage'],
            'total_piece_weight_g': packet_result['total_piece_weight_g'],
            'output_unit': output_unit,
            'packaging_unit': 'g'
        }
    else:
        # Reverse calculation
        packet_weight = float(data.get('packet_weight', 0))
        weight_unit = data.get('weight_unit', 'kg')
        pieces_per_packet = int(data.get('pieces_per_packet', 0))
        packet_packaging_weight = float(data.get('packet_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'g')

        reverse_result = calculator.reverse_calculate_from_packet_weight(
            packet_weight, pieces_per_packet,
            packet_packaging_weight, packaging_unit, weight_unit
        )

        result = {
            'calculation_type': 'reverse',
            'from_dimensions': False,
            'packet_weight': packet_weight,
            'weight_unit': weight_unit,
            'pieces_per_packet': pieces_per_packet,
            'single_piece_weight_g': reverse_result['single_piece_weight_g'],
            'net_bag_weight_g': reverse_result['net_bag_weight_g'],
            'gross_packet_weight_g': reverse_result['gross_packet_weight_g'],
            'packaging_weight_g': reverse_result['packaging_weight_g'],
            'packaging_percentage': reverse_result['packaging_percentage']
        }

    return result


@login_required
@csrf_exempt
def calculate_bundle_weight(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_direction = data.get('calculation_direction', 'forward')
            input_method = data.get('input_method', 'direct_weight')

            calculator = BagMakingCalculator()
            result = {}

            if input_method == 'dimensions':
                # Calculate from dimensions
                result = calculate_bundle_weight_from_dimensions_data(data, calculator)
            else:
                # Direct weight input
                result = calculate_bundle_weight_from_direct_data(data, calculator)

            if request.user.is_authenticated:
                default_material = PlasticMaterial.objects.first()
                BagMakingCalculation.objects.create(
                    calculation_type='BUNDLE_WEIGHT',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    material=default_material,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def calculate_bundle_weight_from_direct_data(data, calculator):
    """Calculate bundle weight from direct weight input"""
    calculation_direction = data.get('calculation_direction', 'forward')

    print("Direct data received:", data)  # Debug log

    if calculation_direction == 'forward':
        packet_weight_kg = float(data.get('packet_weight_kg', 0))
        packets_per_bundle = int(data.get('packets_per_bundle', 0))
        bundle_packaging_weight = float(data.get('bundle_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'kg')
        output_unit = data.get('output_unit', 'kg')

        print(
            f"Forward calculation inputs: packet={packet_weight_kg}kg, packets={packets_per_bundle}, packaging={bundle_packaging_weight}{packaging_unit}")  # Debug log

        # Ensure packaging weight is properly converted
        if packaging_unit == 'g':
            bundle_packaging_weight_kg = bundle_packaging_weight / 1000
            packaging_unit = 'kg'  # Convert to kg for calculator
        else:
            bundle_packaging_weight_kg = bundle_packaging_weight

        bundle_result = calculator.calculate_bundle_weight(
            packets_per_bundle, packet_weight_kg,
            bundle_packaging_weight_kg, packaging_unit, output_unit
        )

        print("Bundle result:", bundle_result)  # Debug log

        result = {
            'calculation_type': 'forward',
            'from_dimensions': False,
            'gross_weight': bundle_result['gross_weight'],
            'net_weight': bundle_result['net_weight'],
            'packaging_weight': bundle_result['packaging_weight'],
            'packaging_percentage': bundle_result['packaging_percentage'],
            'packet_weight_kg': bundle_result['packet_weight_kg'],
            'packets_per_bundle': packets_per_bundle,
            'net_packets_weight_kg': bundle_result['net_packets_weight_kg'],
            'output_unit': output_unit,
            'packaging_unit': 'kg'
        }
    else:
        # Reverse calculation
        bundle_weight = float(data.get('bundle_weight', 0))
        weight_unit = data.get('weight_unit', 'kg')
        packets_per_bundle = int(data.get('packets_per_bundle', 0))
        bundle_packaging_weight = float(data.get('bundle_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'kg')

        print(
            f"Reverse calculation inputs: bundle={bundle_weight}{weight_unit}, packets={packets_per_bundle}, packaging={bundle_packaging_weight}{packaging_unit}")  # Debug log

        reverse_result = calculator.reverse_calculate_from_bundle_weight(
            bundle_weight, packets_per_bundle,
            bundle_packaging_weight, packaging_unit, weight_unit
        )

        print("Reverse result:", reverse_result)  # Debug log

        result = {
            'calculation_type': 'reverse',
            'from_dimensions': False,
            'bundle_weight': bundle_weight,
            'weight_unit': weight_unit,
            'packets_per_bundle': packets_per_bundle,
            'packet_weight_kg': reverse_result['packet_weight_kg'],
            'net_packets_weight_kg': reverse_result['net_packets_weight_kg'],
            'gross_bundle_weight_kg': reverse_result['gross_bundle_weight_kg'],
            'packaging_weight_kg': reverse_result['packaging_weight_kg'],
            'packaging_percentage': reverse_result['packaging_percentage']
        }

    return result


def calculate_bundle_weight_from_dimensions_data(data, calculator):
    """Calculate bundle weight from bag dimensions"""
    calculation_direction = data.get('calculation_direction', 'forward')

    # Extract dimensions data
    bag_type = data.get('dimensions_bag_type', 'FLAT_SHEET')
    width = float(data.get('dimensions_width', 0))
    height = float(data.get('dimensions_height', 0))
    gusset_width = float(data.get('dimensions_gusset_width', 0))
    width_unit = data.get('dimensions_width_unit', 'cm')
    height_unit = data.get('dimensions_height_unit', 'cm')
    gusset_unit = data.get('dimensions_gusset_unit', 'cm')
    pieces_per_packet = int(data.get('dimensions_pieces_per_packet', 0))
    packets_per_bundle = int(data.get('dimensions_packets_per_bundle', 0))
    bundle_packaging_weight = float(data.get('dimensions_bundle_packaging_weight', 0))
    packaging_unit = data.get('dimensions_packaging_unit', 'kg')
    output_unit = data.get('output_unit', 'kg')

    # Calculate area
    area_m2 = calculator.calculate_single_piece_area(
        width, height, bag_type, gusset_width,
        width_unit, height_unit, gusset_unit
    )

    # Calculate GSM based on material type
    if bag_type.startswith('LAMINATED'):
        layers_data = []
        layer_index = 0
        while f'dimensions_layer_material_{layer_index}' in data:
            material_id = data.get(f'dimensions_layer_material_{layer_index}')
            thickness = float(data.get(f'dimensions_layer_thickness_{layer_index}', 0))
            thickness_unit = data.get(f'dimensions_layer_thickness_unit_{layer_index}', 'micron')

            if material_id and thickness:
                try:
                    material = PlasticMaterial.objects.get(id=material_id)
                    layers_data.append({
                        'thickness_microns': thickness,
                        'density_g_cm3': material.density,
                        'thickness_unit': thickness_unit
                    })
                except PlasticMaterial.DoesNotExist:
                    pass
            layer_index += 1

        if not layers_data:
            raise ValueError('No valid layers provided for laminated bag')

        composite_gsm = calculator.calculate_composite_gsm(layers_data)
    else:
        material_id = data.get('dimensions_material_id')
        if not material_id:
            raise ValueError('Material required for single layer bag')

        material = PlasticMaterial.objects.get(id=material_id)
        thickness = float(data.get('dimensions_thickness', 0))
        thickness_unit = data.get('dimensions_thickness_unit', 'micron')

        thickness_m = calculator.convert_thickness(thickness, thickness_unit, 'm')
        thickness_um = thickness_m * 1e6

        composite_gsm = calculator.calculate_gsm_from_thickness(thickness_um, material.density)

    # Calculate single piece weight
    single_piece_weight_g = calculator.calculate_single_piece_weight(area_m2, composite_gsm)

    # Calculate packet weight
    packet_weight_kg = (single_piece_weight_g * pieces_per_packet) / 1000

    if calculation_direction == 'forward':
        bundle_result = calculator.calculate_bundle_weight(
            packets_per_bundle, packet_weight_kg,
            bundle_packaging_weight, packaging_unit, output_unit
        )

        result = {
            'calculation_type': 'forward',
            'from_dimensions': True,
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'pieces_per_packet': pieces_per_packet,
            'area_m2': round(area_m2, 6),
            'composite_gsm': round(composite_gsm, 2),
            'gross_weight': bundle_result['gross_weight'],
            'net_weight': bundle_result['net_weight'],
            'packaging_weight': bundle_result['packaging_weight'],
            'packaging_percentage': bundle_result['packaging_percentage'],
            'packet_weight_kg': round(packet_weight_kg, 4),
            'packets_per_bundle': packets_per_bundle,
            'net_packets_weight_kg': bundle_result['net_packets_weight_kg'],
            'output_unit': output_unit,
            'packaging_unit': 'kg'
        }
    else:
        # Reverse calculation
        bundle_weight = float(data.get('bundle_weight', 0))
        weight_unit = data.get('weight_unit', 'kg')

        reverse_result = calculator.reverse_calculate_from_bundle_weight(
            bundle_weight, packets_per_bundle,
            bundle_packaging_weight, packaging_unit, weight_unit
        )

        result = {
            'calculation_type': 'reverse',
            'from_dimensions': True,
            'bundle_weight': bundle_weight,
            'weight_unit': weight_unit,
            'packets_per_bundle': packets_per_bundle,
            'packet_weight_kg': reverse_result['packet_weight_kg'],
            'net_packets_weight_kg': reverse_result['net_packets_weight_kg'],
            'gross_bundle_weight_kg': reverse_result['gross_bundle_weight_kg'],
            'packaging_weight_kg': reverse_result['packaging_weight_kg'],
            'packaging_percentage': reverse_result['packaging_percentage'],
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'area_m2': round(area_m2, 6),
            'composite_gsm': round(composite_gsm, 2),
            'pieces_per_packet': pieces_per_packet
        }

    return result


@login_required
@csrf_exempt
def calculate_production_metrics(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculator = BagMakingCalculator()

            # Production time calculation
            total_pieces = int(data.get('total_pieces', 0))
            machine_speed = float(data.get('machine_speed', 0))
            machine_speed_unit = data.get('machine_speed_unit', 'pcs_min')

            if machine_speed_unit == 'pcs_hr':
                machine_speed_pcs_min = machine_speed / 60
            else:
                machine_speed_pcs_min = machine_speed

            production_time_min = calculator.calculate_production_time(total_pieces, machine_speed_pcs_min)

            # Yield calculation
            input_film_mass = float(data.get('input_film_mass', 0))
            input_mass_unit = data.get('input_mass_unit', 'kg')
            output_bag_mass = float(data.get('output_bag_mass', 0))
            output_mass_unit = data.get('output_mass_unit', 'kg')

            input_film_mass_kg = calculator.convert_mass(input_film_mass, input_mass_unit, 'kg')
            output_bag_mass_kg = calculator.convert_mass(output_bag_mass, output_mass_unit, 'kg')

            yield_percent = calculator.calculate_yield(input_film_mass_kg, output_bag_mass_kg)

            # Efficiency calculation
            actual_run_time = float(data.get('actual_run_time', 0))
            actual_time_unit = data.get('actual_time_unit', 'min')

            if actual_time_unit == 'hr':
                actual_run_time_min = actual_run_time * 60
            else:
                actual_run_time_min = actual_run_time

            efficiency_percent = calculator.calculate_efficiency(production_time_min, actual_run_time_min)

            # Production rate
            total_pieces_produced = int(data.get('total_pieces_produced', total_pieces))
            production_rate = calculator.calculate_production_rate(total_pieces_produced, actual_run_time_min)

            result = {
                'production_time_min': round(production_time_min, 2),
                'production_time_hr': round(production_time_min / 60, 2),
                'yield_percent': round(yield_percent, 2),
                'efficiency_percent': round(efficiency_percent, 2),
                'production_rate_pcs_hr': round(production_rate, 2),
                'recommendations': get_production_recommendations(yield_percent, efficiency_percent)
            }

            if request.user.is_authenticated:
                BagMakingCalculation.objects.create(
                    calculation_type='PRODUCTION_TIME',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    material=PlasticMaterial.objects.first(),
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_production_recommendations(yield_percent, efficiency_percent):
    recommendations = []

    if yield_percent < 85:
        recommendations.append("Low yield - Check for material waste and optimize cutting patterns")
    elif yield_percent > 98:
        recommendations.append("Excellent yield - Maintain current processes")

    if efficiency_percent < 80:
        recommendations.append("Low efficiency - Consider machine maintenance or operator training")
    elif efficiency_percent > 95:
        recommendations.append("High efficiency - Excellent performance")

    return recommendations if recommendations else ["Process running within normal parameters"]


@login_required
def bag_making_history(request):
    """Display bag making calculation history"""
    calculations = BagMakingCalculation.objects.filter(user=request.user).select_related('material').order_by(
        '-timestamp')
    return render(request, 'bag_making/history.html', {'calculations': calculations})
