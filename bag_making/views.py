from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import BagMakingCalculation, AddonComponent, BagLayer, CutoutGeometry, BulkProduct
from .bag_calculator import BagMakingCalculator
import json
import logging

logger = logging.getLogger(__name__)


def resolve_common_fields(data):
    """Resolve optional machine/customer/order context shared across all bag making calculators."""
    machine_name = data.get('machine_name') or ''
    customer_name = data.get('customer_name') or ''
    order_name = data.get('order_name') or ''
    return machine_name, customer_name, order_name


def resolve_material_with_fallback(data):
    """
    Resolve material selection with fallback handling for laminated vs single layer.
    Returns material object or None.
    """
    bag_type = data.get('bag_type', 'FLAT_SHEET')

    if bag_type.startswith('LAMINATED'):
        # For laminated, try to get first layer material
        layers_data = data.get('layers', [])
        if layers_data:
            material_id = layers_data[0].get('material_id')
            if material_id:
                try:
                    return PlasticMaterial.objects.get(id=material_id)
                except PlasticMaterial.DoesNotExist:
                    pass
        return None
    else:
        material_id = data.get('material_id')
        if material_id:
            try:
                return PlasticMaterial.objects.get(id=material_id)
            except PlasticMaterial.DoesNotExist:
                pass
        return None


def apply_optional_feature(calculator, feature_type, data, single_piece_weight_g,
                             thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type):
    """
    Apply ONE optional accessory/cut-out feature to a bag's single-piece weight,
    per the Accessories & Cut-Outs spec. Returns a dict describing the outcome,
    or {'error': ...} if a business rule is violated.
    """
    defaults = BagMakingCalculator.ACCESSORY_DEFAULTS

    if feature_type in ('ZIPPER', 'SPOUT_ASSEMBLY') and not is_ldpe_bag:
        return {'error': f'{feature_type.replace("_", " ").title()} requires an LDPE bag or an LDPE sealing layer'}

    if feature_type == 'TAPE' and 'FLAP' not in bag_type:
        return {'error': 'Adhesive Tape requires a bag with a flap'}

    if feature_type == 'ZIPPER':
        zipper_key = data.get('zipper_type', 'ZIPPER_18MM')
        if zipper_key not in defaults:
            return {'error': f'Unknown zipper_type: {zipper_key}'}
        cz = float(data.get('zipper_cz_override') or defaults[zipper_key]['Cz_g_per_100mm'])
        feature_weight_g = calculator.calculate_zipper_weight(width_mm, cz)
        final_weight_g = single_piece_weight_g + feature_weight_g
        return {
            'feature_type': feature_type, 'feature_label': defaults[zipper_key]['label'],
            'coefficient_used': round(cz, 4), 'feature_weight_g': round(feature_weight_g, 4),
            'operation': 'added', 'final_weight_g': final_weight_g
        }

    if feature_type == 'TAPE':
        tape_key = data.get('tape_type', 'TAPE_PERMANENT')
        if tape_key not in defaults:
            return {'error': f'Unknown tape_type: {tape_key}'}
        ct = float(data.get('tape_ct_override') or defaults[tape_key]['Ct_g_per_100mm'])
        # Calculated from bag width automatically, same as Zipper - no manual length input needed
        feature_weight_g = calculator.calculate_tape_weight(width_mm, ct)
        final_weight_g = single_piece_weight_g + feature_weight_g
        return {
            'feature_type': feature_type, 'feature_label': defaults[tape_key]['label'],
            'coefficient_used': round(ct, 4), 'feature_weight_g': round(feature_weight_g, 4),
            'operation': 'added', 'final_weight_g': final_weight_g
        }

    if feature_type in ('SPOUT_ASSEMBLY', 'LOOP_HANDLE', 'BREATHER_VENT'):
        default_weight = defaults[feature_type]['weight_g']
        override_key = f'accessory_weight_override_{feature_type}'
        feature_weight_g = float(data.get(override_key) or default_weight)
        final_weight_g = single_piece_weight_g + feature_weight_g
        return {
            'feature_type': feature_type, 'feature_label': defaults[feature_type]['label'],
            'default_weight_g': default_weight, 'feature_weight_g': round(feature_weight_g, 4),
            'operation': 'added', 'final_weight_g': final_weight_g
        }

    if feature_type == 'CARRY_HANDLE':
        try:
            dpunch = CutoutGeometry.objects.get(name=BagMakingCalculator.CARRY_HANDLE_DPUNCH_NAME, is_active=True)
        except CutoutGeometry.DoesNotExist:
            return {'error': 'D Punch (30mm x 75mm) geometry not found - required for Carry Handle'}
        k = dpunch.calculate_k(density_g_cm3=density_g_cm3)
        dpunch_weight_g = calculator.calculate_cutout_weight(k, thickness_um)
        handle_weight_g = float(data.get('accessory_weight_override_CARRY_HANDLE') or defaults['CARRY_HANDLE']['weight_g'])
        final_weight_g = single_piece_weight_g - dpunch_weight_g + handle_weight_g
        return {
            'feature_type': feature_type, 'feature_label': defaults['CARRY_HANDLE']['label'],
            'dpunch_geometry': dpunch.name, 'dpunch_area_cm2': dpunch.area_cm2, 'dpunch_k': round(k, 6),
            'dpunch_deduction_g': round(dpunch_weight_g, 4), 'handle_weight_g': round(handle_weight_g, 4),
            'operation': 'deducted_dpunch_then_added_handle', 'final_weight_g': final_weight_g
        }

    if feature_type in ('D_PUNCH', 'VEST_BAG'):
        geometry_id = data.get(f'cutout_geometry_id_{feature_type}')
        if not geometry_id:
            return {'error': f'Select a {feature_type.replace("_", " ").title()} geometry'}
        try:
            geometry = CutoutGeometry.objects.get(id=geometry_id, is_active=True)
        except CutoutGeometry.DoesNotExist:
            return {'error': 'Selected cut-out geometry not found'}
        k = geometry.calculate_k(density_g_cm3=density_g_cm3)
        cutout_weight_g = calculator.calculate_cutout_weight(k, thickness_um)
        final_weight_g = single_piece_weight_g - cutout_weight_g
        return {
            'feature_type': feature_type, 'feature_label': geometry.name,
            'geometry_area_cm2': geometry.area_cm2, 'density_used_g_cm3': round(density_g_cm3, 4),
            'k': round(k, 6), 'feature_weight_g': round(cutout_weight_g, 4),
            'operation': 'deducted', 'final_weight_g': final_weight_g
        }

    return {'error': f'Unknown feature_type: {feature_type}'}


def apply_optional_features(calculator, feature_types, data, single_piece_weight_g,
                             thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type):
    """
    Apply up to 3 optional accessory/cut-out features cumulatively to a bag's
    single-piece weight - e.g. Zipper + Loop Handle + Breather Vent on one bag.
    Each feature is validated and applied in turn against the RUNNING weight
    (so a cut-out deduction and an accessory addition compose correctly
    regardless of order). Returns (list_of_feature_results, final_weight_g),
    or ({'error': ...}, original_weight_g) if any feature or the combination
    itself is invalid.
    """
    feature_types = [f for f in feature_types if f and f != 'NONE']

    if not feature_types:
        return [], single_piece_weight_g

    if len(feature_types) > 3:
        return {'error': 'Select at most 3 features'}, single_piece_weight_g

    if len(feature_types) != len(set(feature_types)):
        return {'error': 'Each feature can only be selected once'}, single_piece_weight_g

    results = []
    running_weight_g = single_piece_weight_g
    for feature_type in feature_types:
        result = apply_optional_feature(
            calculator, feature_type, data, running_weight_g,
            thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type
        )
        if result.get('error'):
            return result, single_piece_weight_g
        if 'final_weight_g' not in result:
            return {'error': f'Internal error applying feature "{feature_type}"'}, single_piece_weight_g
        running_weight_g = result['final_weight_g']
        results.append(result)

    return results, running_weight_g


def save_material_selection(calculation, data):
    """
    Resolve and persist material selection (single OR laminate) for a calculation,
    run AFTER the BagMakingCalculation record already exists. Handles both the
    plain "layers" list shape (pieces-weight) and the indexed dimensions-mode
    field shape ("dimensions_layer_material_0", "dimensions_layer_material_1", ...).
    """
    bag_type = calculation.bag_type

    if bag_type.startswith('LAMINATED'):
        layers_data = data.get('layers', [])
        if layers_data:
            for layer_order, layer in enumerate(layers_data):
                material_id = layer.get('material_id') if isinstance(layer, dict) else None
                if not material_id:
                    continue
                try:
                    material_obj = PlasticMaterial.objects.get(id=material_id)
                    BagLayer.objects.create(
                        calculation=calculation,
                        material=material_obj,
                        thickness=float(layer.get('thickness_microns', 0) or 0),
                        thickness_unit=layer.get('thickness_unit', 'micron'),
                        layer_order=layer_order
                    )
                except (PlasticMaterial.DoesNotExist, ValueError):
                    pass
        else:
            layer_index = 0
            while f'dimensions_layer_material_{layer_index}' in data:
                material_id = data.get(f'dimensions_layer_material_{layer_index}')
                thickness = data.get(f'dimensions_layer_thickness_{layer_index}', 0)
                thickness_unit = data.get(f'dimensions_layer_thickness_unit_{layer_index}', 'micron')
                if material_id:
                    try:
                        material_obj = PlasticMaterial.objects.get(id=material_id)
                        BagLayer.objects.create(
                            calculation=calculation,
                            material=material_obj,
                            thickness=float(thickness) if thickness else 0.0,
                            thickness_unit=thickness_unit,
                            layer_order=layer_index
                        )
                    except (PlasticMaterial.DoesNotExist, ValueError):
                        pass
                layer_index += 1
    else:
        material_id = data.get('material_id') or data.get('dimensions_material_id')
        if material_id:
            try:
                calculation.material = PlasticMaterial.objects.get(id=material_id)
                calculation.save(update_fields=['material'])
            except PlasticMaterial.DoesNotExist:
                pass


@login_required
def bag_making_home(request):
    """Home view for bag making calculators"""
    calculators = [
        {'id': 'pieces_weight', 'name': 'Pieces ↔ Weight Converter', 'icon': 'fas fa-exchange-alt'},
        {'id': 'packet_weight', 'name': 'Packet Weight Calculator', 'icon': 'fas fa-box'},
        {'id': 'bundle_weight', 'name': 'Bundle/Bale Weight Calculator', 'icon': 'fas fa-pallet'},
        {'id': 'production_time', 'name': 'Production Time & Efficiency', 'icon': 'fas fa-clock'},
        {'id': 'bag_capacity', 'name': 'Bag Fill Volume/Capacity', 'icon': 'fas fa-fill-drip'},
        {'id': 'roll_requirement', 'name': 'Bags per Roll / Roll Requirement', 'icon': 'fas fa-scroll'},
        {'id': 'seal_strength', 'name': 'Heat Seal Strength', 'icon': 'fas fa-thermometer-three-quarters'},
    ]

    # Updated bag types with flap option and gusset types
    bag_types = [
        ('FLAT_SHEET', 'Flat Sheet Bag'),
        ('TUBULAR', 'Tubular Bag'),
        ('TUBULAR_WITH_FLAP', 'Tubular Bag with Flap'),
        ('GUSSETED_SIDE', 'Side Gusseted Bag'),
        ('GUSSETED_BOTTOM', 'Bottom Gusseted Bag'),
        ('LAMINATED_FLAT', 'Laminated Flat Bag'),
        ('LAMINATED_TUBULAR', 'Laminated Tubular Bag'),
        ('LAMINATED_TUBULAR_FLAP', 'Laminated Tubular with Flap'),
        ('LAMINATED_GUSSETED_SIDE', 'Laminated Side Gusseted Bag'),
        ('LAMINATED_GUSSETED_BOTTOM', 'Laminated Bottom Gusseted Bag'),
    ]

    addon_types = [
        ('NONE', 'No Add-ons'),
        ('ZIPPER', 'Zipper Only'),
        ('HANDLES', 'Handles Only'),
        ('BOTH', 'Zipper and Handles'),
    ]

    materials = PlasticMaterial.objects.filter(material_type='FILM')

    return render(request, 'bag_making/home.html', {
        'section_name': 'Bag Making',
        'calculators': calculators,
        'bag_types': bag_types,
        'addon_types': addon_types,
        'materials': materials
    })


@login_required
@csrf_exempt
def calculate_pieces_weight(request):
    """Calculate pieces to weight or weight to pieces"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
            flap_length = float(data.get('flap_length', 0))
            flap_unit = data.get('flap_unit', 'cm')

            # Calculate area with flap support
            area_m2 = calculator.calculate_single_piece_area(
                width=width, height=height, bag_type=bag_type, gusset_width=gusset_width,
                flap_length=flap_length, width_unit=width_unit, height_unit=height_unit,
                gusset_unit=gusset_unit, flap_unit=flap_unit
            )

            # Calculate GSM based on material type
            material = None
            if bag_type.startswith('LAMINATED'):
                # For laminated bags, use composite GSM
                layers_data = data.get('layers', [])
                if not layers_data:
                    return JsonResponse({'success': False, 'error': 'No layers provided for laminated bag'})
                composite_gsm = calculator.calculate_composite_gsm(layers_data)

                # Total thickness across all layers (mirrors calculate_composite_gsm's own
                # unit-conversion logic) - needed for the optional cut-out/accessory step below.
                thickness_um = 0.0
                is_ldpe_bag = False
                for layer in layers_data:
                    layer_thickness_um = layer['thickness_microns']
                    if layer.get('thickness_unit') and layer['thickness_unit'] != 'micron':
                        layer_thickness_m = calculator.convert_thickness(
                            layer['thickness_microns'], layer['thickness_unit'], 'm'
                        )
                        layer_thickness_um = layer_thickness_m * 1e6
                    thickness_um += layer_thickness_um

                    layer_material_id = layer.get('material_id')
                    if layer_material_id:
                        try:
                            if PlasticMaterial.objects.get(id=layer_material_id).is_ldpe:
                                is_ldpe_bag = True
                        except PlasticMaterial.DoesNotExist:
                            pass

                # Effective/composite density that reproduces the same total GSM at this thickness
                density_g_cm3 = (composite_gsm / thickness_um) if thickness_um > 0 else 0.0
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
                density_g_cm3 = material.density
                is_ldpe_bag = material.is_ldpe

            # Calculate add-on weight
            addon_data = data.get('addons', {})
            addon_weight_g = calculator.calculate_addon_weight(
                zipper_data=addon_data.get('zipper'),
                handle_data=addon_data.get('handles')
            )

            # Calculate single piece weight including add-ons
            single_piece_weight_g = calculator.calculate_single_piece_weight(
                area_m2, composite_gsm, addon_weight_g
            )

            # --- Optional accessory / cut-out features (up to 3, applied after base weight) ---
            feature_types = data.get('feature_types', [])
            if isinstance(feature_types, str):
                feature_types = [feature_types] if feature_types else []
            feature_types = [f for f in feature_types if f and f != 'NONE']

            feature_results = []
            if feature_types:
                length_conversions = {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'inch': 25.4}
                width_mm = width * length_conversions.get(width_unit, 10.0)
                outcome, single_piece_weight_g = apply_optional_features(
                    calculator, feature_types, data, single_piece_weight_g,
                    thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type
                )
                if isinstance(outcome, dict) and outcome.get('error'):
                    return JsonResponse({'success': False, 'error': outcome['error']})
                feature_results = outcome

            result = {}

            if calculation_direction == 'pieces_to_weight':
                num_pieces = int(data.get('num_pieces', 0))
                output_unit = data.get('output_unit', 'kg')

                total_weight = calculator.calculate_pieces_to_weight(
                    num_pieces, single_piece_weight_g, output_unit
                )

                result = {
                    'single_piece_weight_g': round(single_piece_weight_g, 4),
                    'bag_weight_only_g': round(single_piece_weight_g - addon_weight_g, 4),
                    'addon_weight_g': round(addon_weight_g, 4),
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
                    'bag_weight_only_g': round(single_piece_weight_g - addon_weight_g, 4),
                    'addon_weight_g': round(addon_weight_g, 4),
                    'num_pieces': num_pieces,
                    'total_weight': total_weight,
                    'weight_unit': weight_unit,
                    'calculation_type': 'weight_to_pieces',
                    'area_m2': round(area_m2, 6),
                    'composite_gsm': round(composite_gsm, 2)
                }

            # Save calculation
            if request.user.is_authenticated:
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='PIECES_WEIGHT',
                    bag_type=bag_type,
                    addon_type=data.get('addon_type', 'NONE'),
                    material=material if not bag_type.startswith('LAMINATED') else None,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

                # Save laminate layer structure
                save_material_selection(calculation, data)

                # Save addon components if any
                if addon_weight_g > 0:
                    _save_addon_components(calculation, addon_data)

            if feature_results:
                result['features'] = feature_results

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in pieces_weight calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def reverse_calculate_zipper(request):
    """Reverse calculate zipper weight per cm from total add-on weight"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculator = BagMakingCalculator()

            total_addon_weight_g = float(data.get('total_addon_weight_g', 0))
            zipper_length = float(data.get('zipper_length', 0))
            length_unit = data.get('length_unit', 'cm')
            num_handles = int(data.get('num_handles', 0))
            handle_weight_g = float(data.get('handle_weight_g', 0))

            result = calculator.reverse_calculate_zipper_weight(
                total_addon_weight_g,
                zipper_length,
                length_unit,
                num_handles,
                handle_weight_g
            )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def _save_addon_components(calculation, addon_data):
    """Helper function to save addon components"""
    if addon_data.get('zipper', {}).get('enabled'):
        AddonComponent.objects.create(
            calculation=calculation,
            addon_type='ZIPPER',
            material=PlasticMaterial.objects.get(id=addon_data['zipper']['material_id']),
            weight_per_piece=addon_data['zipper'].get('total_weight', 0),
            description=f"Zipper length: {addon_data['zipper'].get('length', 0)} {addon_data['zipper'].get('length_unit', 'cm')}"
        )

    if addon_data.get('handles', {}).get('enabled'):
        AddonComponent.objects.create(
            calculation=calculation,
            addon_type='HANDLE',
            material=PlasticMaterial.objects.get(id=addon_data['handles']['material_id']),
            weight_per_piece=addon_data['handles'].get('total_weight', 0),
            description=f"Quantity: {addon_data['handles'].get('quantity', 2)}"
        )


@login_required
@csrf_exempt
def calculate_packet_weight(request):
    """Calculate packet weight calculations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculation_direction = data.get('calculation_direction', 'forward')
            input_method = data.get('input_method', 'direct_weight')

            calculator = BagMakingCalculator()
            result = {}

            if input_method == 'dimensions':
                result = calculate_packet_weight_from_dimensions_data(data, calculator)
            else:
                result = calculate_packet_weight_from_direct_data(data, calculator)

            if request.user.is_authenticated:
                # Get material for non-laminated
                material = resolve_material_with_fallback(data)
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='PACKET_WEIGHT',
                    bag_type=data.get('dimensions_bag_type') or data.get('bag_type', 'FLAT_SHEET'),
                    addon_type=data.get('addon_type', 'NONE'),
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in packet_weight calculation: {str(e)}", exc_info=True)
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
    flap_length = float(data.get('dimensions_flap_length', 0))
    width_unit = data.get('dimensions_width_unit', 'cm')
    height_unit = data.get('dimensions_height_unit', 'cm')
    gusset_unit = data.get('dimensions_gusset_unit', 'cm')
    flap_unit = data.get('dimensions_flap_unit', 'cm')
    pieces_per_packet = int(data.get('dimensions_pieces_per_packet', 0))
    packet_packaging_weight = float(data.get('dimensions_packet_packaging_weight', 0))
    packaging_unit = data.get('dimensions_packaging_unit', 'g')
    output_unit = data.get('output_unit', 'kg')

    # Calculate area
    area_m2 = calculator.calculate_single_piece_area(
        width=width, height=height, bag_type=bag_type, gusset_width=gusset_width,
        flap_length=flap_length, width_unit=width_unit, height_unit=height_unit,
        gusset_unit=gusset_unit, flap_unit=flap_unit
    )

    # Calculate GSM based on material type
    if bag_type.startswith('LAMINATED'):
        layers_data = []
        layer_index = 0
        is_ldpe_bag = False
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
                    if material.is_ldpe:
                        is_ldpe_bag = True
                except PlasticMaterial.DoesNotExist:
                    pass
            layer_index += 1

        if not layers_data:
            raise ValueError('No valid layers provided for laminated bag')

        composite_gsm = calculator.calculate_composite_gsm(layers_data)

        # Total thickness across all layers - needed for the optional cut-out/accessory step below
        thickness_um = 0.0
        for layer in layers_data:
            layer_thickness_um = layer['thickness_microns']
            if layer.get('thickness_unit') and layer['thickness_unit'] != 'micron':
                layer_thickness_m = calculator.convert_thickness(
                    layer['thickness_microns'], layer['thickness_unit'], 'm'
                )
                layer_thickness_um = layer_thickness_m * 1e6
            thickness_um += layer_thickness_um

        density_g_cm3 = (composite_gsm / thickness_um) if thickness_um > 0 else 0.0
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
        density_g_cm3 = material.density
        is_ldpe_bag = material.is_ldpe

    # Calculate add-on weight
    addon_data = data.get('dimensions_addons', {})
    addon_weight_g = calculator.calculate_addon_weight(
        zipper_data=addon_data.get('zipper'),
        handle_data=addon_data.get('handles')
    )

    # Calculate single piece weight including add-ons
    single_piece_weight_g = calculator.calculate_single_piece_weight(area_m2, composite_gsm, addon_weight_g)

    # --- Optional accessory / cut-out features (up to 3, applied after base weight) ---
    feature_types = data.get('feature_types', [])
    if isinstance(feature_types, str):
        feature_types = [feature_types] if feature_types else []
    feature_types = [f for f in feature_types if f and f != 'NONE']

    feature_results = []
    if feature_types:
        length_conversions = {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'inch': 25.4}
        width_mm = width * length_conversions.get(width_unit, 10.0)
        outcome, single_piece_weight_g = apply_optional_features(
            calculator, feature_types, data, single_piece_weight_g,
            thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type
        )
        if isinstance(outcome, dict) and outcome.get('error'):
            raise ValueError(outcome['error'])
        feature_results = outcome

    if calculation_direction == 'forward':
        packet_result = calculator.calculate_packet_weight(
            pieces_per_packet, single_piece_weight_g,
            packet_packaging_weight, packaging_unit, output_unit
        )

        result = {
            'calculation_type': 'forward',
            'from_dimensions': True,
            'single_piece_weight_g': round(single_piece_weight_g, 4),
            'bag_weight_only_g': round(single_piece_weight_g - addon_weight_g, 4),
            'addon_weight_g': round(addon_weight_g, 4),
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

    if feature_results:
        result['features'] = feature_results

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
    """Calculate bundle weight calculations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculation_direction = data.get('calculation_direction', 'forward')
            input_method = data.get('input_method', 'direct_weight')

            calculator = BagMakingCalculator()
            result = {}

            if input_method == 'dimensions':
                result = calculate_bundle_weight_from_dimensions_data(data, calculator)
            else:
                result = calculate_bundle_weight_from_direct_data(data, calculator)

            if request.user.is_authenticated:
                material = resolve_material_with_fallback(data)
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='BUNDLE_WEIGHT',
                    bag_type=data.get('dimensions_bag_type') or data.get('bag_type', 'FLAT_SHEET'),
                    addon_type=data.get('addon_type', 'NONE'),
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in bundle_weight calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def calculate_bundle_weight_from_direct_data(data, calculator):
    """Calculate bundle weight from direct weight input"""
    calculation_direction = data.get('calculation_direction', 'forward')

    if calculation_direction == 'forward':
        packet_weight_kg = float(data.get('packet_weight_kg', 0))
        packets_per_bundle = int(data.get('packets_per_bundle', 0))
        bundle_packaging_weight = float(data.get('bundle_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'kg')
        output_unit = data.get('output_unit', 'kg')

        bundle_result = calculator.calculate_bundle_weight(
            packets_per_bundle, packet_weight_kg,
            bundle_packaging_weight, packaging_unit, output_unit
        )

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
        bundle_weight = float(data.get('bundle_weight', 0))
        weight_unit = data.get('weight_unit', 'kg')
        packets_per_bundle = int(data.get('packets_per_bundle', 0))
        bundle_packaging_weight = float(data.get('bundle_packaging_weight', 0))
        packaging_unit = data.get('packaging_unit', 'kg')

        reverse_result = calculator.reverse_calculate_from_bundle_weight(
            bundle_weight, packets_per_bundle,
            bundle_packaging_weight, packaging_unit, weight_unit
        )

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
    flap_length = float(data.get('dimensions_flap_length', 0))
    width_unit = data.get('dimensions_width_unit', 'cm')
    height_unit = data.get('dimensions_height_unit', 'cm')
    gusset_unit = data.get('dimensions_gusset_unit', 'cm')
    flap_unit = data.get('dimensions_flap_unit', 'cm')
    pieces_per_packet = int(data.get('dimensions_pieces_per_packet', 0))
    packets_per_bundle = int(data.get('dimensions_packets_per_bundle', 0))
    bundle_packaging_weight = float(data.get('dimensions_bundle_packaging_weight', 0))
    packaging_unit = data.get('dimensions_packaging_unit', 'kg')
    output_unit = data.get('output_unit', 'kg')

    # Calculate area
    area_m2 = calculator.calculate_single_piece_area(
        width=width, height=height, bag_type=bag_type, gusset_width=gusset_width,
        flap_length=flap_length, width_unit=width_unit, height_unit=height_unit,
        gusset_unit=gusset_unit, flap_unit=flap_unit
    )

    # Calculate GSM based on material type
    if bag_type.startswith('LAMINATED'):
        layers_data = []
        layer_index = 0
        is_ldpe_bag = False
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
                    if material.is_ldpe:
                        is_ldpe_bag = True
                except PlasticMaterial.DoesNotExist:
                    pass
            layer_index += 1

        if not layers_data:
            raise ValueError('No valid layers provided for laminated bag')

        composite_gsm = calculator.calculate_composite_gsm(layers_data)

        # Total thickness across all layers - needed for the optional cut-out/accessory step below
        thickness_um = 0.0
        for layer in layers_data:
            layer_thickness_um = layer['thickness_microns']
            if layer.get('thickness_unit') and layer['thickness_unit'] != 'micron':
                layer_thickness_m = calculator.convert_thickness(
                    layer['thickness_microns'], layer['thickness_unit'], 'm'
                )
                layer_thickness_um = layer_thickness_m * 1e6
            thickness_um += layer_thickness_um

        density_g_cm3 = (composite_gsm / thickness_um) if thickness_um > 0 else 0.0
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
        density_g_cm3 = material.density
        is_ldpe_bag = material.is_ldpe

    # Calculate add-on weight
    addon_data = data.get('dimensions_addons', {})
    addon_weight_g = calculator.calculate_addon_weight(
        zipper_data=addon_data.get('zipper'),
        handle_data=addon_data.get('handles')
    )

    # Calculate single piece weight including add-ons
    single_piece_weight_g = calculator.calculate_single_piece_weight(area_m2, composite_gsm, addon_weight_g)

    # --- Optional accessory / cut-out features (up to 3, applied after base weight) ---
    feature_types = data.get('feature_types', [])
    if isinstance(feature_types, str):
        feature_types = [feature_types] if feature_types else []
    feature_types = [f for f in feature_types if f and f != 'NONE']

    feature_results = []
    if feature_types:
        length_conversions = {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'inch': 25.4}
        width_mm = width * length_conversions.get(width_unit, 10.0)
        outcome, single_piece_weight_g = apply_optional_features(
            calculator, feature_types, data, single_piece_weight_g,
            thickness_um, density_g_cm3, width_mm, is_ldpe_bag, bag_type
        )
        if isinstance(outcome, dict) and outcome.get('error'):
            raise ValueError(outcome['error'])
        feature_results = outcome

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
            'bag_weight_only_g': round(single_piece_weight_g - addon_weight_g, 4),
            'addon_weight_g': round(addon_weight_g, 4),
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

    if feature_results:
        result['features'] = feature_results

    return result


@login_required
@csrf_exempt
def calculate_production_metrics(request):
    """Calculate production time and efficiency metrics"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
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
                material = resolve_material_with_fallback(data)
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='PRODUCTION_TIME',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    addon_type='NONE',
                    material=material,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in production_metrics calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_production_recommendations(yield_percent, efficiency_percent):
    """Generate production recommendations based on metrics"""
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


def list_cutout_geometries(request):
    """Return active cut-out geometries, grouped by geometry_type, for the feature selector."""
    geometries = CutoutGeometry.objects.filter(is_active=True).order_by('geometry_type', 'name')
    data = {}
    for g in geometries:
        data.setdefault(g.geometry_type, []).append({
            'id': g.id,
            'name': g.name,
            'area_cm2': g.area_cm2,
            'calibration_material': g.calibration_material,
        })
    return JsonResponse({'success': True, 'geometries': data})


def list_bulk_products(request):
    """Return active bulk products, grouped by category, for the Bag Capacity calculator."""
    products = BulkProduct.objects.filter(is_active=True).order_by('category', 'name')
    data = {}
    for p in products:
        data.setdefault(p.category, []).append({
            'id': p.id,
            'name': p.name,
            'density_min_kg_m3': p.density_min_kg_m3,
            'density_max_kg_m3': p.density_max_kg_m3,
            'density_typical_kg_m3': p.density_typical_kg_m3,
            'notes': p.notes,
        })
    return JsonResponse({'success': True, 'products': data})


@csrf_exempt
def calculate_bag_capacity(request):
    """Bag fill volume/capacity calculator - bidirectional (volume<->fill weight)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculator = BagMakingCalculator()

            bag_shape = data.get('bag_shape', 'GUSSETED')  # 'GUSSETED' or 'FLAT'
            width = float(data.get('width', 0))
            width_unit = data.get('width_unit', 'cm')
            height = float(data.get('height', 0))
            height_unit = data.get('height_unit', 'cm')
            gusset = float(data.get('gusset', 0))
            gusset_unit = data.get('gusset_unit', 'cm')

            if width <= 0 or height <= 0:
                return JsonResponse({'success': False, 'error': 'Width and height must be greater than 0'})
            if bag_shape == 'GUSSETED' and gusset <= 0:
                return JsonResponse({'success': False, 'error': 'Gusset depth must be greater than 0 for gusseted bags'})

            width_cm = calculator.convert_length(width, width_unit, 'cm')
            height_cm = calculator.convert_length(height, height_unit, 'cm')
            gusset_cm = calculator.convert_length(gusset, gusset_unit, 'cm') if gusset else 0

            if bag_shape == 'GUSSETED':
                volume_cm3 = calculator.calculate_gusseted_bag_volume_cm3(width_cm, gusset_cm, height_cm)
            else:
                volume_cm3 = calculator.calculate_flat_bag_volume_cm3(width_cm, height_cm)

            volume_liters = volume_cm3 / 1000

            # Density source: BulkProduct lookup, or a custom override
            product_id = data.get('product_id')
            custom_density = data.get('custom_density_kg_m3')
            density_kg_m3 = None
            product_name = None

            if custom_density:
                density_kg_m3 = float(custom_density)
                product_name = 'Custom'
            elif product_id:
                try:
                    product = BulkProduct.objects.get(id=product_id, is_active=True)
                    density_kg_m3 = product.density_typical_kg_m3
                    product_name = product.name
                except BulkProduct.DoesNotExist:
                    pass

            result = {
                'bag_shape': bag_shape,
                'volume_cm3': round(volume_cm3, 2),
                'volume_liters': round(volume_liters, 3),
                'width_cm': round(width_cm, 2),
                'height_cm': round(height_cm, 2),
                'gusset_cm': round(gusset_cm, 2) if gusset_cm else 0,
            }

            if density_kg_m3:
                fill_weight_kg = calculator.calculate_fill_weight_from_volume(volume_liters, density_kg_m3)
                result['product_name'] = product_name
                result['density_kg_m3'] = density_kg_m3
                result['estimated_fill_weight_kg'] = round(fill_weight_kg, 3)

            # Reverse direction: given a target fill weight, what volume/dimensions are needed
            target_weight_kg = data.get('target_weight_kg')
            if target_weight_kg and density_kg_m3:
                target_weight_kg = float(target_weight_kg)
                required_volume_liters = calculator.calculate_volume_needed_for_weight(target_weight_kg, density_kg_m3)
                result['target_weight_kg'] = target_weight_kg
                result['required_volume_liters'] = round(required_volume_liters, 3)
                result['required_volume_cm3'] = round(required_volume_liters * 1000, 2)

            if request.user.is_authenticated:
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='BAG_CAPACITY',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    addon_type='NONE',
                    material=None,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in bag_capacity calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_roll_requirement(request):
    """Bags per roll / roll requirement calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculator = BagMakingCalculator()

            height = float(data.get('height', 0))
            height_unit = data.get('height_unit', 'cm')
            seal_allowance = float(data.get('seal_allowance', 3))
            seal_allowance_unit = data.get('seal_allowance_unit', 'mm')

            if height <= 0:
                return JsonResponse({'success': False, 'error': 'Height must be greater than 0'})

            height_m = calculator.convert_length(height, height_unit, 'm')
            seal_allowance_m = calculator.convert_length(seal_allowance, seal_allowance_unit, 'm')

            bag_repeat_length_m = calculator.calculate_bag_repeat_length(height_m, seal_allowance_m)

            # Roll length: either entered directly, or derived from outer/core diameter + thickness
            roll_length_source = data.get('roll_length_source', 'direct')  # 'direct' or 'derived'

            if roll_length_source == 'derived':
                outer_diameter = float(data.get('outer_diameter', 0))
                outer_diameter_unit = data.get('outer_diameter_unit', 'mm')
                core_diameter = float(data.get('core_diameter', 0))
                core_diameter_unit = data.get('core_diameter_unit', 'mm')
                thickness = float(data.get('roll_thickness', 0))
                thickness_unit = data.get('roll_thickness_unit', 'micron')

                if outer_diameter <= 0 or core_diameter <= 0 or thickness <= 0:
                    return JsonResponse({'success': False, 'error': 'Outer diameter, core diameter, and thickness must all be greater than 0'})

                outer_radius_m = calculator.convert_length(outer_diameter, outer_diameter_unit, 'm') / 2
                core_radius_m = calculator.convert_length(core_diameter, core_diameter_unit, 'm') / 2
                thickness_m = calculator.convert_thickness(thickness, thickness_unit, 'm')

                roll_length_m = calculator.calculate_roll_length_from_diameter(outer_radius_m, core_radius_m, thickness_m)
            else:
                roll_length = float(data.get('roll_length', 0))
                roll_length_unit = data.get('roll_length_unit', 'm')
                if roll_length <= 0:
                    return JsonResponse({'success': False, 'error': 'Roll length must be greater than 0'})
                roll_length_m = calculator.convert_length(roll_length, roll_length_unit, 'm')

            bags_per_roll = calculator.calculate_bags_per_roll(roll_length_m, bag_repeat_length_m)

            result = {
                'bag_repeat_length_m': round(bag_repeat_length_m, 4),
                'roll_length_m': round(roll_length_m, 2),
                'bags_per_roll': bags_per_roll,
                'roll_length_source': roll_length_source,
            }

            total_bags_needed = data.get('total_bags_needed')
            if total_bags_needed:
                total_bags_needed = int(total_bags_needed)
                if bags_per_roll <= 0:
                    return JsonResponse({'success': False, 'error': 'Bags per roll is 0 - check roll length and bag repeat length'})
                rolls_required = calculator.calculate_rolls_required(total_bags_needed, bags_per_roll)
                total_film_length_required_m = calculator.calculate_total_film_length_required(total_bags_needed, bag_repeat_length_m)
                result['total_bags_needed'] = total_bags_needed
                result['rolls_required'] = rolls_required
                result['total_film_length_required_m'] = round(total_film_length_required_m, 2)

            if request.user.is_authenticated:
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='ROLL_REQUIREMENT',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    addon_type='NONE',
                    material=None,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in roll_requirement calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def get_seal_strength_rating(seal_strength_n_per_15mm, min_threshold):
    if min_threshold and seal_strength_n_per_15mm < min_threshold:
        return "FAIL - below minimum threshold"
    if seal_strength_n_per_15mm < 10:
        return "Weak Seal"
    elif seal_strength_n_per_15mm < 25:
        return "Moderate Seal"
    elif seal_strength_n_per_15mm < 40:
        return "Good Seal"
    else:
        return "Excellent Seal"


@csrf_exempt
def calculate_seal_strength(request):
    """Heat seal strength calculator (ASTM F88-style, same convention as Lamination's Peel Strength)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            machine_name, customer_name, order_name = resolve_common_fields(data)
            calculator = BagMakingCalculator()

            seal_force = float(data.get('seal_force', 0))
            seal_force_unit = data.get('seal_force_unit', 'N')
            sample_width = float(data.get('sample_width', 15))
            sample_width_unit = data.get('sample_width_unit', 'mm')
            seal_location = data.get('seal_location', 'TOP')  # TOP / BOTTOM / SIDE / ZIPPER
            min_threshold = data.get('min_threshold')

            if seal_force <= 0 or sample_width <= 0:
                return JsonResponse({'success': False, 'error': 'Seal force and sample width must be greater than 0'})

            force_conversions = {'N': 1.0, 'kN': 1000.0, 'lbf': 4.44822}
            seal_force_n = seal_force * force_conversions.get(seal_force_unit, 1.0)
            sample_width_mm = calculator.convert_length(sample_width, sample_width_unit, 'mm')

            seal_strength = calculator.calculate_seal_strength(seal_force_n, sample_width_mm)

            result = {
                'seal_strength_n_per_15mm': round(seal_strength, 3),
                'seal_force_n': round(seal_force_n, 3),
                'sample_width_mm': round(sample_width_mm, 2),
                'seal_location': seal_location,
            }

            if min_threshold:
                min_threshold = float(min_threshold)
                result['min_threshold'] = min_threshold
                result['pass_fail'] = 'PASS' if seal_strength >= min_threshold else 'FAIL'

            result['rating'] = get_seal_strength_rating(seal_strength, float(min_threshold) if min_threshold else None)

            if request.user.is_authenticated:
                calculation = BagMakingCalculation.objects.create(
                    calculation_type='SEAL_STRENGTH',
                    bag_type=data.get('bag_type', 'FLAT_SHEET'),
                    addon_type='NONE',
                    material=None,
                    machine_name=machine_name,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                save_material_selection(calculation, data)

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            logger.error(f"Error in seal_strength calculation: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
