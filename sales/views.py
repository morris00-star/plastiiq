from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from calculator.models import PlasticMaterial
from .models import SalesCalculation
from .sales_calculator import SalesCalculator
import json


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

            material = PlasticMaterial.objects.get(id=material_id) if material_id else None

            result = {
                'cost_per_kg': round(cost_per_kg, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_kg'
            }

            if request.user.is_authenticated and material:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_KG',
                    material=material,
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

            material = PlasticMaterial.objects.get(id=material_id) if material_id else None

            result = {
                'cost_per_meter': round(cost_per_meter, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_meter'
            }

            if request.user.is_authenticated and material:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_METER',
                    material=material,
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

            material = PlasticMaterial.objects.get(id=material_id) if material_id else None

            result = {
                'cost_per_piece': round(cost_per_piece, 2),
                'currency': currency,
                'material_name': material.name if material else 'Custom Material',
                'calculation_type': 'material_cost_piece'
            }

            if request.user.is_authenticated and material:
                SalesCalculation.objects.create(
                    calculation_type='MATERIAL_COST_PIECE',
                    material=material,
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            calculation_type = data.get('calculation_type', 'cost_per_kg')
            total_weight_kg = float(data.get('total_weight_kg', 0))
            currency = data.get('currency', 'UGX')
            number_of_layers = int(data.get('number_of_layers', 2))

            # Extract material information for display
            material_details = []
            for i in range(1, 5):
                material_id = data.get(f'material_{i}_id')
                if material_id:
                    try:
                        material = PlasticMaterial.objects.get(id=material_id)
                        material_details.append({
                            'id': material.id,
                            'name': material.name,
                            'density': material.density,
                            'type': 'layer'
                        })
                    except PlasticMaterial.DoesNotExist:
                        pass

            calculator = SalesCalculator(currency)

            if calculation_type == 'cost_per_kg':
                total_cost = float(data.get('total_cost', 0))
                cost_per_kg = calculator.calculate_laminated_cost_per_kg([total_cost], total_weight_kg)
                total_calculated_cost = total_cost
            else:
                cost_per_kg = float(data.get('cost_per_kg', 0))
                total_calculated_cost = calculator.calculate_laminated_total_cost([cost_per_kg * total_weight_kg])
                total_cost = total_calculated_cost

            result = {
                'cost_per_kg': round(cost_per_kg, 2),
                'total_cost': round(total_calculated_cost, 2),
                'total_weight_kg': round(total_weight_kg, 3),
                'number_of_layers': number_of_layers,
                'layer_details': material_details,  # Store layer info for display
                'currency': currency,
                'calculation_type': calculation_type
            }

            if request.user.is_authenticated:
                SalesCalculation.objects.create(
                    calculation_type='LAMINATED_COST',
                    input_data=data,
                    result_data=result,
                    user=request.user
                )

            return JsonResponse({'success': True, 'result': result})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})
