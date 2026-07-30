import csv
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from slitting.models import SlittingCalculation
from .models import PlasticMaterial, DensityCalculation
from django.views.decorators.csrf import csrf_exempt
import json
from .templatetags.history_filters import get_calculation_type_display, get_section_name
from .views_history import get_display_material, download_csv_history


def home(request):
    """Main calculator page"""
    materials = PlasticMaterial.objects.all().order_by('material_type', 'name')
    return render(request, 'calculator/home.html', {
        'materials': materials,
        'material_types': PlasticMaterial.MATERIAL_TYPES
    })


def calculate_density(request):
    """Calculate density from mass and volume"""
    if request.method == 'POST':
        try:
            mass = float(request.POST.get('mass', 0))
            volume = float(request.POST.get('volume', 0))
            material_id = request.POST.get('material_id')

            if mass <= 0 or volume <= 0:
                return JsonResponse({'error': 'Mass and volume must be positive values'})

            # Calculate density
            density = mass / volume

            # Get selected material for comparison
            material = None
            expected_density = None
            density_difference = None
            percentage_diff = None

            if material_id:
                material = PlasticMaterial.objects.get(id=material_id)
                expected_density = material.density
                density_difference = density - expected_density
                percentage_diff = (density_difference / expected_density) * 100

            # Save calculation to history if user is authenticated
            if request.user.is_authenticated and material:
                DensityCalculation.objects.create(
                    material=material,
                    mass=mass,
                    volume=volume,
                    calculated_density=density
                )

            return JsonResponse({
                'density': round(density, 4),
                'material_name': material.name if material else None,
                'expected_density': round(expected_density, 4) if expected_density else None,
                'density_difference': round(density_difference, 4) if density_difference else None,
                'percentage_diff': round(percentage_diff, 2) if percentage_diff else None,
                'status': 'within_range' if percentage_diff and abs(
                    percentage_diff) <= 5 else 'out_of_range' if percentage_diff else 'no_reference'
            })

        except ValueError:
            return JsonResponse({'error': 'Please enter valid numbers'})
        except PlasticMaterial.DoesNotExist:
            return JsonResponse({'error': 'Selected material not found'})
        except Exception as e:
            return JsonResponse({'error': f'Calculation error: {str(e)}'})

    return JsonResponse({'error': 'Invalid request method'})


def material_reference(request):
    """Display material density reference table"""
    materials = PlasticMaterial.objects.all().order_by('material_type', 'name')
    return render(request, 'calculator/reference.html', {
        'materials': materials,
        'material_types': PlasticMaterial.MATERIAL_TYPES
    })


@login_required
def download_calculation_history(request):
    """Download calculation history as CSV"""
    section = request.GET.get('section', 'all')
    format_type = request.GET.get('format', 'csv')

    # Create response
    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = f'attachment; filename="qc_calculations_{section}_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Section', 'Calculation Type', 'Material', 'Timestamp',
        'Input Parameters', 'Results', 'User'
    ])

    # Get calculations based on section
    if section == 'all' or section == 'density':
        density_calcs = DensityCalculation.objects.filter(user=request.user).select_related('material')
        for calc in density_calcs:
            writer.writerow([
                'Density',
                'Density Calculation',
                calc.material.name if calc.material else 'N/A',
                calc.timestamp.strftime('%Y-%m-%d %H:%M'),
                f"Mass: {calc.mass}g, Volume: {calc.volume}cm³",
                f"Density: {calc.calculated_density}g/cm³",
                request.user.username
            ])

    if section == 'all' or section == 'extrusion':
        try:
            from extrusion.models import ExtrusionCalculation
            extrusion_calcs = ExtrusionCalculation.objects.filter(user=request.user).select_related('material')
            for calc in extrusion_calcs:
                writer.writerow([
                    'Extrusion',
                    calc.get_calculation_type_display(),
                    calc.material.name if calc.material else 'N/A',
                    calc.timestamp.strftime('%Y-%m-%d %H:%M'),
                    str(calc.input_data),
                    str(calc.result_data),
                    request.user.username
                ])
        except ImportError:
            pass

    # Add other sections as they are implemented

    return response


@login_required
@csrf_exempt
def delete_calculation(request, calculation_id):
    """Delete a specific calculation from any section"""
    if request.method != 'POST' and request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Import all section models
        from extrusion.models import ExtrusionCalculation
        from printing.models import PrintingCalculation
        from lamination.models import LaminationCalculation
        from slitting.models import SlittingCalculation
        from bag_making.models import BagMakingCalculation
        from sales.models import SalesCalculation

        calculation = None
        section_name = None

        # Check all sections for the calculation
        try:
            calculation = ExtrusionCalculation.objects.get(id=calculation_id, user=request.user)
            section_name = 'extrusion'
        except ExtrusionCalculation.DoesNotExist:
            try:
                calculation = PrintingCalculation.objects.get(id=calculation_id, user=request.user)
                section_name = 'printing'
            except PrintingCalculation.DoesNotExist:
                try:
                    calculation = LaminationCalculation.objects.get(id=calculation_id, user=request.user)
                    section_name = 'lamination'
                except LaminationCalculation.DoesNotExist:
                    try:
                        calculation = SlittingCalculation.objects.get(id=calculation_id, user=request.user)
                        section_name = 'slitting'
                    except SlittingCalculation.DoesNotExist:
                        try:
                            calculation = BagMakingCalculation.objects.get(id=calculation_id, user=request.user)
                            section_name = 'bag_making'
                        except BagMakingCalculation.DoesNotExist:
                            try:
                                calculation = SalesCalculation.objects.get(id=calculation_id, user=request.user)
                                section_name = 'sales'
                            except SalesCalculation.DoesNotExist:
                                pass

        if calculation:
            calculation_name = get_calculation_type_display(calculation)
            calculation.delete()
            return JsonResponse({
                'success': True,
                'message': f'{calculation_name} calculation deleted successfully',
                'section': section_name
            })
        else:
            return JsonResponse({'success': False, 'error': 'Calculation not found or access denied'}, status=404)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
def delete_calculations_bulk(request):
    """Delete multiple calculations in bulk"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        calculation_ids = data.get('calculation_ids', [])

        if not calculation_ids:
            return JsonResponse({'success': False, 'error': 'No calculations selected'})

        deleted_count = 0
        errors = []

        # Import all section models
        from extrusion.models import ExtrusionCalculation
        from printing.models import PrintingCalculation
        from lamination.models import LaminationCalculation
        from slitting.models import SlittingCalculation
        from bag_making.models import BagMakingCalculation
        from sales.models import SalesCalculation

        # List of all models to check
        models = [
            (ExtrusionCalculation, 'extrusion'),
            (PrintingCalculation, 'printing'),
            (LaminationCalculation, 'lamination'),
            (SlittingCalculation, 'slitting'),
            (BagMakingCalculation, 'bag_making'),
            (SalesCalculation, 'sales')
        ]

        for calculation_id in calculation_ids:
            calculation_found = False
            for model, section_name in models:
                try:
                    calculation = model.objects.get(id=calculation_id, user=request.user)
                    calculation.delete()
                    deleted_count += 1
                    calculation_found = True
                    break
                except model.DoesNotExist:
                    continue

            if not calculation_found:
                errors.append(f"Calculation {calculation_id} not found")

        if errors:
            return JsonResponse({
                'success': True,
                'message': f'Deleted {deleted_count} calculations, {len(errors)} errors',
                'deleted_count': deleted_count,
                'errors': errors
            })
        else:
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {deleted_count} calculations',
                'deleted_count': deleted_count
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def export_selected_calculations(request):
    """Export selected calculations"""
    calculation_ids = request.GET.get('ids', '').split(',')
    if not calculation_ids or calculation_ids == ['']:
        return JsonResponse({'error': 'No calculations selected'})

    # Filter valid IDs
    valid_ids = [id for id in calculation_ids if id.isdigit()]

    # Import all section models
    from extrusion.models import ExtrusionCalculation
    from printing.models import PrintingCalculation
    from lamination.models import LaminationCalculation
    from slitting.models import SlittingCalculation
    from bag_making.models import BagMakingCalculation
    from sales.models import SalesCalculation

    all_calculations = []

    # Get calculations from each section
    models = [
        ExtrusionCalculation,
        PrintingCalculation,
        LaminationCalculation,
        SlittingCalculation,
        BagMakingCalculation,
        SalesCalculation
    ]

    for model in models:
        try:
            calculations = model.objects.filter(
                id__in=valid_ids,
                user=request.user
            )
            for calc in calculations:
                calc.section = get_section_name(calc)
                calc.display_material = get_display_material(calc)
                all_calculations.append(calc)
        except Exception as e:
            print(f"Error loading calculations for {model}: {e}")
            continue

    return download_csv_history(all_calculations, f"{request.user.username}_selected")


@login_required
def calculation_reasons(request):
    """Display the purposes and benefits of all calculations"""
    return render(request, 'calculator/reasons.html')


@login_required
def material_properties(request):
    """Display material properties and applications guide"""
    return render(request, 'calculator/material_properties.html')


@login_required
def additives_resins(request):
    """
    View for displaying additives and resins information
    """
    context = {
        'title': 'Additives & Resins',
        'description': 'Complete guide to additives, their functions, mechanisms, and optimal usage in plastic film production'
    }
    return render(request, 'calculator/additives_resins.html', context)


@login_required
def tolerances(request):
    """
    View for displaying typical tolerances in plastic film production
    """
    context = {
        'title': 'Production Tolerances',
        'description': 'Industry-standard tolerances for quality control and process optimization in plastic film manufacturing'
    }
    return render(request, 'calculator/tolerances.html', context)


@login_required
def troubleshooting(request):
    """
    View for displaying production troubleshooting guide
    """
    context = {
        'title': 'Troubleshooting Guide',
        'description': 'Comprehensive defect analysis and solutions for plastic film manufacturing'
    }
    return render(request, 'calculator/troubleshooting.html', context)

