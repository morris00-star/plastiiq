from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import SalesCalculation
from .sales_calculator import SalesCalculator
from .models import SalesCalculationLayer
import json


def resolve_common_fields(data):
    """Resolve optional customer/order context shared across all sales calculators."""
    customer_name = data.get('customer_name') or ''
    order_name = data.get('order_name') or ''
    return customer_name, order_name


def resolve_material(data):
    """Resolve optional single material (not used for laminate mode, which uses real layers)."""
    material_id = data.get('material_id')
    if not material_id:
        return None
    try:
        return PlasticMaterial.objects.get(id=material_id)
    except PlasticMaterial.DoesNotExist:
        return None


def resolve_material_or_laminate(data):
    """
    Resolve material selection which may be a single material OR a laminate
    (multiple layer materials tagged for history - these sales formulas don't
    compute from density, so laminate mode is a labeling/history concept only).

    Returns (material, laminate_material_names):
    - single mode:   material = PlasticMaterial instance or None, laminate_material_names = []
    - laminate mode: material = None (no single FK fits), laminate_material_names = list of names
    """
    material_mode = data.get('material_mode', 'single')
    if material_mode == 'laminate':
        material_ids = data.get('layer_material_ids', [])
        names = []
        for mid in material_ids:
            if not mid:
                continue
            try:
                names.append(PlasticMaterial.objects.get(id=mid).name)
            except PlasticMaterial.DoesNotExist:
                pass
        return None, names
    return resolve_material(data), []


@login_required
def sales_home(request):
    calculators = [
        {'id': 'material_cost_kg', 'name': 'Material Cost per kg', 'icon': 'fas fa-weight-hanging'},
        {'id': 'material_cost_meter', 'name': 'Material Cost per meter', 'icon': 'fas fa-ruler'},
        {'id': 'material_cost_piece', 'name': 'Material Cost per piece', 'icon': 'fas fa-cube'},
        {'id': 'order_quantity_kg', 'name': 'Order Quantity from kg', 'icon': 'fas fa-shopping-cart'},
        {'id': 'order_quantity_meter', 'name': 'Order Quantity from meters', 'icon': 'fas fa-ruler-combined'},
        {'id': 'order_quantity_piece', 'name': 'Order Quantity from pieces', 'icon': 'fas fa-boxes'},
        {'id': 'roll_cost', 'name': 'Roll Cost Calculation', 'icon': 'fas fa-roll'},
        {'id': 'laminated_cost', 'name': 'Laminated Material Cost', 'icon': 'fas fa-layer-group'},
        {'id': 'margin_markup', 'name': 'Margin / Markup / Selling Price', 'icon': 'fas fa-percentage'},
        {'id': 'cost_per_sqm', 'name': 'Cost per Square Meter', 'icon': 'fas fa-vector-square'},
        {'id': 'breakeven', 'name': 'Breakeven Quantity', 'icon': 'fas fa-balance-scale'},
        {'id': 'vat_calc', 'name': 'VAT Inclusive/Exclusive', 'icon': 'fas fa-receipt'},
        {'id': 'bulk_discount', 'name': 'Bulk/Quantity-Break Discount', 'icon': 'fas fa-tags'},
    ]

    materials = PlasticMaterial.objects.all()

    return render(request, 'sales/home.html', {
        'section_name': 'Sales & Pricing',
        'calculators': calculators,
        'materials': materials,
        'currency': 'UGX'
    })


@csrf_exempt
def calculate_material_cost_kg(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            total_material_cost = float(data.get('total_material_cost', 0))
            output_mass_kg = float(data.get('output_mass_kg', 0))
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            cost_per_kg = calculator.calculate_material_cost_per_kg(total_material_cost, output_mass_kg)

            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)
            customer_name, order_name = resolve_common_fields(data)
            customer_name, order_name = resolve_common_fields(data)

            result = {
                'cost_per_kg': round(cost_per_kg, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_kg'
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_KG',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_material_cost_meter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            total_material_cost = float(data.get('total_material_cost', 0))
            output_length_m = float(data.get('output_length_m', 0))
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            cost_per_meter = calculator.calculate_material_cost_per_meter(total_material_cost, output_length_m)

            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            result = {
                'cost_per_meter': round(cost_per_meter, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_meter'
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_METER',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_material_cost_piece(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            material_id = data.get('material_id')
            total_material_cost = float(data.get('total_material_cost', 0))
            output_pieces = int(data.get('output_pieces', 0))
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            cost_per_piece = calculator.calculate_material_cost_per_piece(total_material_cost, output_pieces)

            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            result = {
                'cost_per_piece': round(cost_per_piece, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_piece'
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_PIECE',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_order_quantity_kg(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'quantity_from_budget')
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            if calculation_type == 'quantity_from_budget':
                cost_per_kg = float(data.get('cost_per_kg', 0))
                total_budget = float(data.get('total_budget', 0))
                quantity_kg = calculator.calculate_order_quantity_from_kg(cost_per_kg, total_budget)

                result = {
                    'quantity_kg': round(quantity_kg, 2),
                    'total_budget': total_budget,
                    'cost_per_kg': cost_per_kg,
                    'currency': currency,
                    'calculation_type': 'quantity_from_budget'
                }
            else:  # cost_from_quantity
                cost_per_kg = float(data.get('cost_per_kg', 0))
                quantity_kg = float(data.get('quantity_kg', 0))
                total_cost = calculator.calculate_total_cost_from_kg(cost_per_kg, quantity_kg)

                result = {
                    'total_cost': round(total_cost, 2),
                    'quantity_kg': quantity_kg,
                    'cost_per_kg': cost_per_kg,
                    'currency': currency,
                    'calculation_type': 'cost_from_quantity'
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='ORDER_QUANTITY_KG',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_order_quantity_meter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'quantity_from_budget')
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            if calculation_type == 'quantity_from_budget':
                cost_per_meter = float(data.get('cost_per_meter', 0))
                total_budget = float(data.get('total_budget', 0))
                quantity_meters = calculator.calculate_order_quantity_from_meters(cost_per_meter, total_budget)

                result = {
                    'quantity_meters': round(quantity_meters, 2),
                    'total_budget': total_budget,
                    'cost_per_meter': cost_per_meter,
                    'currency': currency,
                    'calculation_type': 'quantity_from_budget'
                }
            else:  # cost_from_quantity
                cost_per_meter = float(data.get('cost_per_meter', 0))
                quantity_meters = float(data.get('quantity_meters', 0))
                total_cost = calculator.calculate_total_cost_from_meters(cost_per_meter, quantity_meters)

                result = {
                    'total_cost': round(total_cost, 2),
                    'quantity_meters': quantity_meters,
                    'cost_per_meter': cost_per_meter,
                    'currency': currency,
                    'calculation_type': 'cost_from_quantity'
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='ORDER_QUANTITY_METER',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_order_quantity_piece(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'quantity_from_budget')
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            if calculation_type == 'quantity_from_budget':
                cost_per_piece = float(data.get('cost_per_piece', 0))
                total_budget = float(data.get('total_budget', 0))
                quantity_pieces = calculator.calculate_order_quantity_from_pieces(cost_per_piece, total_budget)

                result = {
                    'quantity_pieces': int(quantity_pieces),
                    'total_budget': total_budget,
                    'cost_per_piece': cost_per_piece,
                    'currency': currency,
                    'calculation_type': 'quantity_from_budget'
                }
            else:  # cost_from_quantity
                cost_per_piece = float(data.get('cost_per_piece', 0))
                quantity_pieces = int(data.get('quantity_pieces', 0))
                total_cost = calculator.calculate_total_cost_from_pieces(cost_per_piece, quantity_pieces)

                result = {
                    'total_cost': round(total_cost, 2),
                    'quantity_pieces': quantity_pieces,
                    'cost_per_piece': cost_per_piece,
                    'currency': currency,
                    'calculation_type': 'cost_from_quantity'
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='ORDER_QUANTITY_PIECE',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_roll_cost(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'cost_per_kg')
            currency = data.get('currency', 'UGX')

            calculator = SalesCalculator(currency)
            material, laminate_materials = resolve_material_or_laminate(data)
            customer_name, order_name = resolve_common_fields(data)

            if calculation_type == 'cost_per_kg':
                roll_cost = float(data.get('roll_cost', 0))
                roll_weight_kg = float(data.get('roll_weight_kg', 0))
                cost_per_kg = calculator.calculate_roll_cost_per_kg(roll_cost, roll_weight_kg)

                result = {
                    'cost_per_kg': round(cost_per_kg, 2),
                    'roll_cost': roll_cost,
                    'roll_weight_kg': roll_weight_kg,
                    'currency': currency,
                    'calculation_type': 'cost_per_kg'
                }
            else:  # total_cost
                cost_per_kg = float(data.get('cost_per_kg', 0))
                roll_weight_kg = float(data.get('roll_weight_kg', 0))
                roll_cost = calculator.calculate_roll_cost_from_kg(cost_per_kg, roll_weight_kg)

                result = {
                    'roll_cost': round(roll_cost, 2),
                    'cost_per_kg': cost_per_kg,
                    'roll_weight_kg': roll_weight_kg,
                    'currency': currency,
                    'calculation_type': 'total_cost'
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='ROLL_COST',
                    material=material,
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_laminated_cost(request):
    """
    Laminated material cost, computed from REAL per-layer cost/weight entries.
    (Previously this collapsed to a single flat cost regardless of layer count -
    now each layer's own cost-per-kg x weight is summed properly.)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            currency = data.get('currency', 'UGX')
            layers_input = data.get('layers', [])

            if not layers_input:
                return JsonResponse({'success': False, 'error': 'Provide at least one layer with material, cost per kg, and weight'})

            calculator = SalesCalculator(currency)

            layer_costs = []
            layer_details = []
            total_weight_kg = 0.0

            for i, layer in enumerate(layers_input):
                material_id = layer.get('material_id')
                cost_per_kg = float(layer.get('cost_per_kg', 0) or 0)
                weight_kg = float(layer.get('weight_kg', 0) or 0)

                if cost_per_kg <= 0 or weight_kg <= 0:
                    continue

                layer_cost = calculator.calculate_layer_cost(cost_per_kg, weight_kg)
                layer_costs.append(layer_cost)
                total_weight_kg += weight_kg

                material_name = 'Custom Material'
                if material_id:
                    try:
                        material_name = PlasticMaterial.objects.get(id=material_id).name
                    except PlasticMaterial.DoesNotExist:
                        pass

                layer_details.append({
                    'layer': i + 1,
                    'material_id': material_id,
                    'material_name': material_name,
                    'cost_per_kg': round(cost_per_kg, 2),
                    'weight_kg': round(weight_kg, 3),
                    'layer_cost': round(layer_cost, 2)
                })

            if not layer_costs:
                return JsonResponse({'success': False, 'error': 'Each layer needs a cost per kg and weight greater than 0'})

            total_cost = calculator.calculate_laminated_total_cost(layer_costs)
            cost_per_kg_composite = calculator.calculate_laminated_cost_per_kg(layer_costs, total_weight_kg)

            result = {
                'total_cost': round(total_cost, 2),
                'total_weight_kg': round(total_weight_kg, 3),
                'cost_per_kg': round(cost_per_kg_composite, 2),
                'number_of_layers': len(layer_costs),
                'layer_details': layer_details,
                'currency': currency
            }

            if request.user.is_authenticated:
                calculation = SalesCalculation.objects.create(
                    calculation_type='LAMINATED_COST',
                    customer_name=customer_name,
                    order_name=order_name,
                    input_data=data,
                    result_data=result,
                    user=request.user
                )
                for i, layer in enumerate(layers_input):
                    material_id = layer.get('material_id')
                    if material_id:
                        try:
                            material_obj = PlasticMaterial.objects.get(id=material_id)
                            SalesCalculationLayer.objects.create(
                                calculation=calculation,
                                material=material_obj,
                                cost_per_kg=float(layer.get('cost_per_kg', 0) or 0),
                                weight_kg=float(layer.get('weight_kg', 0) or 0),
                                layer_order=i
                            )
                        except PlasticMaterial.DoesNotExist:
                            pass

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_margin_markup(request):
    """Bidirectional margin/markup/selling price calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            material, laminate_materials = resolve_material_or_laminate(data)
            currency = data.get('currency', 'UGX')
            mode = data.get('mode', 'from_prices')  # 'from_prices', 'price_from_markup', 'price_from_margin'

            calculator = SalesCalculator(currency)

            if mode == 'price_from_markup':
                cost_price = float(data.get('cost_price', 0))
                markup_percent = float(data.get('markup_percent', 0))
                selling_price = calculator.calculate_selling_price_from_markup(cost_price, markup_percent)
                profit = calculator.calculate_profit(cost_price, selling_price)
                margin_percent = calculator.calculate_margin_percent(cost_price, selling_price)
                result = {
                    'mode': 'price_from_markup', 'cost_price': cost_price, 'markup_percent': markup_percent,
                    'selling_price': round(selling_price, 2), 'margin_percent': round(margin_percent, 2),
                    'profit': round(profit, 2), 'currency': currency
                }
            elif mode == 'price_from_margin':
                cost_price = float(data.get('cost_price', 0))
                margin_percent = float(data.get('margin_percent', 0))
                if margin_percent >= 100:
                    return JsonResponse({'success': False, 'error': 'Margin % must be less than 100'})
                selling_price = calculator.calculate_selling_price_from_margin(cost_price, margin_percent)
                profit = calculator.calculate_profit(cost_price, selling_price)
                markup_percent = calculator.calculate_markup_percent(cost_price, selling_price)
                result = {
                    'mode': 'price_from_margin', 'cost_price': cost_price, 'margin_percent': margin_percent,
                    'selling_price': round(selling_price, 2), 'markup_percent': round(markup_percent, 2),
                    'profit': round(profit, 2), 'currency': currency
                }
            else:
                cost_price = float(data.get('cost_price', 0))
                selling_price = float(data.get('selling_price', 0))
                markup_percent = calculator.calculate_markup_percent(cost_price, selling_price)
                margin_percent = calculator.calculate_margin_percent(cost_price, selling_price)
                profit = calculator.calculate_profit(cost_price, selling_price)
                result = {
                    'mode': 'from_prices', 'cost_price': cost_price, 'selling_price': selling_price,
                    'markup_percent': round(markup_percent, 2), 'margin_percent': round(margin_percent, 2),
                    'profit': round(profit, 2), 'currency': currency
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='MARGIN_MARKUP', material=material,
                    customer_name=customer_name, order_name=order_name,
                    input_data=data, result_data=result, user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_cost_per_sqm(request):
    """Bidirectional cost/price per square meter calculator"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            material, laminate_materials = resolve_material_or_laminate(data)
            currency = data.get('currency', 'UGX')
            calculation_type = data.get('calculation_type', 'cost_per_sqm')

            calculator = SalesCalculator(currency)

            if calculation_type == 'cost_per_sqm':
                total_material_cost = float(data.get('total_material_cost', 0))
                width = float(data.get('width', 0))
                width_unit = data.get('width_unit', 'm')
                length = float(data.get('length', 0))
                length_unit = data.get('length_unit', 'm')
                width_m = calculator.convert_length_to_m(width, width_unit)
                length_m = calculator.convert_length_to_m(length, length_unit)
                area_m2 = width_m * length_m
                cost_per_sqm = calculator.calculate_cost_per_sqm(total_material_cost, area_m2)
                result = {
                    'cost_per_sqm': round(cost_per_sqm, 2), 'area_m2': round(area_m2, 3),
                    'width_m': round(width_m, 3), 'length_m': round(length_m, 3),
                    'total_material_cost': total_material_cost, 'currency': currency,
                    'calculation_type': 'cost_per_sqm'
                }
            elif calculation_type == 'quantity_from_budget':
                cost_per_sqm = float(data.get('cost_per_sqm', 0))
                total_budget = float(data.get('total_budget', 0))
                area_m2 = calculator.calculate_order_quantity_from_sqm(cost_per_sqm, total_budget)
                result = {
                    'area_m2': round(area_m2, 3), 'total_budget': total_budget,
                    'cost_per_sqm': cost_per_sqm, 'currency': currency,
                    'calculation_type': 'quantity_from_budget'
                }
            else:
                cost_per_sqm = float(data.get('cost_per_sqm', 0))
                area_m2 = float(data.get('area_m2', 0))
                total_cost = calculator.calculate_total_cost_from_sqm(cost_per_sqm, area_m2)
                result = {
                    'total_cost': round(total_cost, 2), 'area_m2': area_m2,
                    'cost_per_sqm': cost_per_sqm, 'currency': currency,
                    'calculation_type': 'cost_from_quantity'
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='COST_PER_SQM', material=material,
                    customer_name=customer_name, order_name=order_name,
                    input_data=data, result_data=result, user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_breakeven(request):
    """Breakeven quantity from fixed costs, selling price, and variable cost per unit"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            material, laminate_materials = resolve_material_or_laminate(data)
            currency = data.get('currency', 'UGX')

            fixed_costs = float(data.get('fixed_costs', 0))
            selling_price_per_unit = float(data.get('selling_price_per_unit', 0))
            variable_cost_per_unit = float(data.get('variable_cost_per_unit', 0))

            calculator = SalesCalculator(currency)
            contribution_margin = selling_price_per_unit - variable_cost_per_unit

            if contribution_margin <= 0:
                return JsonResponse({'success': False, 'error': 'Selling price must be greater than variable cost per unit'})

            breakeven_units = calculator.calculate_breakeven_units(fixed_costs, selling_price_per_unit, variable_cost_per_unit)
            breakeven_revenue = breakeven_units * selling_price_per_unit

            result = {
                'breakeven_units': round(breakeven_units, 1),
                'contribution_margin_per_unit': round(contribution_margin, 2),
                'breakeven_revenue': round(breakeven_revenue, 2),
                'fixed_costs': fixed_costs,
                'currency': currency
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='BREAKEVEN_QTY', material=material,
                    customer_name=customer_name, order_name=order_name,
                    input_data=data, result_data=result, user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_vat(request):
    """VAT inclusive/exclusive price calculator (default 18% Uganda VAT, editable)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            material, laminate_materials = resolve_material_or_laminate(data)
            currency = data.get('currency', 'UGX')
            mode = data.get('mode', 'add_vat')  # 'add_vat' or 'remove_vat'
            vat_percent = float(data.get('vat_percent', 18))

            calculator = SalesCalculator(currency)

            if mode == 'remove_vat':
                price_incl_vat = float(data.get('price_incl_vat', 0))
                price_excl_vat = calculator.calculate_price_excl_vat(price_incl_vat, vat_percent)
                vat_amount = price_incl_vat - price_excl_vat
                result = {
                    'mode': 'remove_vat', 'price_incl_vat': price_incl_vat,
                    'price_excl_vat': round(price_excl_vat, 2), 'vat_amount': round(vat_amount, 2),
                    'vat_percent': vat_percent, 'currency': currency
                }
            else:
                price_excl_vat = float(data.get('price_excl_vat', 0))
                price_incl_vat = calculator.calculate_price_incl_vat(price_excl_vat, vat_percent)
                vat_amount = price_incl_vat - price_excl_vat
                result = {
                    'mode': 'add_vat', 'price_excl_vat': price_excl_vat,
                    'price_incl_vat': round(price_incl_vat, 2), 'vat_amount': round(vat_amount, 2),
                    'vat_percent': vat_percent, 'currency': currency
                }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='VAT_CALCULATION', material=material,
                    customer_name=customer_name, order_name=order_name,
                    input_data=data, result_data=result, user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def calculate_bulk_discount(request):
    """Bulk/quantity-break discount calculator (single flat discount or tiered by quantity)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_name, order_name = resolve_common_fields(data)
            material, laminate_materials = resolve_material_or_laminate(data)
            currency = data.get('currency', 'UGX')

            base_price = float(data.get('base_price', 0))
            quantity = float(data.get('quantity', 0))
            tiers_input = data.get('tiers', [])

            calculator = SalesCalculator(currency)

            tiers = []
            for tier in tiers_input:
                min_qty = float(tier.get('min_qty', 0) or 0)
                discount_percent = float(tier.get('discount_percent', 0) or 0)
                if min_qty > 0 or discount_percent > 0:
                    tiers.append({'min_qty': min_qty, 'discount_percent': discount_percent})

            if tiers:
                applicable_discount = calculator.calculate_bulk_tier_discount(quantity, tiers)
            else:
                applicable_discount = float(data.get('discount_percent', 0) or 0)

            discounted_price = calculator.calculate_discounted_price(base_price, applicable_discount)
            total_order_value = discounted_price * quantity
            total_savings = (base_price - discounted_price) * quantity

            result = {
                'base_price': base_price,
                'quantity': quantity,
                'applicable_discount_percent': round(applicable_discount, 2),
                'discounted_price_per_unit': round(discounted_price, 2),
                'total_order_value': round(total_order_value, 2),
                'total_savings': round(total_savings, 2),
                'currency': currency
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='BULK_DISCOUNT', material=material,
                    customer_name=customer_name, order_name=order_name,
                    input_data=data, result_data=result, user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
