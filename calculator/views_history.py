from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
import json
import csv
from datetime import datetime
from calculator.models import PlasticMaterial


@login_required
def calculation_history(request):
    """Main history page showing all calculations from all sections"""

    # Import all section models
    from extrusion.models import ExtrusionCalculation
    from printing.models import PrintingCalculation
    from lamination.models import LaminationCalculation
    from slitting.models import SlittingCalculation
    from bag_making.models import BagMakingCalculation
    from sales.models import SalesCalculation

    # Get calculations from all sections - handle models without material field
    all_calculations = []

    # Extrusion calculations (has material field)
    try:
        extrusion_calculations = ExtrusionCalculation.objects.filter(user=request.user).select_related(
            'material').order_by('-timestamp')
        for calc in extrusion_calculations:
            calc.section = 'extrusion'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading extrusion calculations: {e}")

    # Printing calculations (check if has material field)
    try:
        printing_calculations = PrintingCalculation.objects.filter(user=request.user).order_by('-timestamp')
        # Check if Printing model has material field
        if hasattr(PrintingCalculation, 'material'):
            printing_calculations = printing_calculations.select_related('material')
        for calc in printing_calculations:
            calc.section = 'printing'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading printing calculations: {e}")

    # Lamination calculations (check if has material field)
    try:
        lamination_calculations = LaminationCalculation.objects.filter(user=request.user).order_by('-timestamp')
        # Check if Lamination model has material field
        if hasattr(LaminationCalculation, 'material'):
            lamination_calculations = lamination_calculations.select_related('material')
        for calc in lamination_calculations:
            calc.section = 'lamination'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading lamination calculations: {e}")

    # Slitting calculations (check if has material field)
    try:
        slitting_calculations = SlittingCalculation.objects.filter(user=request.user).order_by('-timestamp')
        # Check if Slitting model has material field
        if hasattr(SlittingCalculation, 'material'):
            slitting_calculations = slitting_calculations.select_related('material')
        for calc in slitting_calculations:
            calc.section = 'slitting'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading slitting calculations: {e}")

    # Bag Making calculations (check if has material field)
    try:
        bag_making_calculations = BagMakingCalculation.objects.filter(user=request.user).order_by('-timestamp')
        # Check if BagMaking model has material field
        if hasattr(BagMakingCalculation, 'material'):
            bag_making_calculations = bag_making_calculations.select_related('material')
        for calc in bag_making_calculations:
            calc.section = 'bag_making'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading bag making calculations: {e}")

    # Sales calculations (no material field - uses input_data)
    try:
        sales_calculations = SalesCalculation.objects.filter(user=request.user).order_by('-timestamp')
        for calc in sales_calculations:
            calc.section = 'sales'
            calc.is_recent = is_recent(calc.timestamp)
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading sales calculations: {e}")

    # Sort by timestamp
    materials = PlasticMaterial.objects.all()
    all_calculations.sort(key=lambda x: x.timestamp, reverse=True)

    context = {
        'calculations': all_calculations,
        'total_calculations': len(all_calculations),
        'materials': materials,
    }

    return render(request, 'calculator/history.html', context)


def get_display_material(calculation):
    """Get material information for display in history"""
    # If calculation has a direct material foreign key and it's set
    if hasattr(calculation, 'material') and calculation.material:
        return calculation.material

    # For calculations with material stored in input_data
    if hasattr(calculation, 'input_data') and calculation.input_data:
        input_data = calculation.input_data

        # Check for material_id in input_data (single material)
        if 'material_id' in input_data and input_data['material_id']:
            try:
                material = PlasticMaterial.objects.get(id=input_data['material_id'])
                return material
            except (PlasticMaterial.DoesNotExist, ValueError):
                pass

        # Check for material_details in input_data (for laminated calculations)
        if 'material_details' in input_data and input_data['material_details']:
            materials = input_data['material_details']
            if materials and len(materials) > 0:
                # Create a special "Laminated" material object
                return create_laminated_material_object(materials)

        # Check for material_detail in input_data (for roll calculations)
        if 'material_detail' in input_data and input_data['material_detail']:
            material_detail = input_data['material_detail']
            if material_detail and 'id' in material_detail:
                try:
                    material = PlasticMaterial.objects.get(id=material_detail['id'])
                    return material
                except (PlasticMaterial.DoesNotExist, ValueError):
                    pass

        # Check for primary_material_id and secondary_material_id (laminated structure)
        if 'primary_material_id' in input_data and input_data['primary_material_id']:
            return create_laminated_material_from_structure(input_data)

    # For Sales laminated calculations, check the layers structure
    if hasattr(calculation, 'section') and calculation.section == 'sales':
        if hasattr(calculation, 'result_data') and calculation.result_data:
            result_data = calculation.result_data
            if 'layer_details' in result_data and result_data['layer_details']:
                materials = []
                for layer in result_data['layer_details']:
                    if 'name' in layer:
                        materials.append({'name': layer['name']})
                if materials:
                    return create_laminated_material_object(materials)

    return None


def create_laminated_material_object(materials):
    """Create a special material object for laminated structures"""

    class LaminatedMaterial:
        def __init__(self, materials):
            self.name = self._generate_laminated_name(materials)
            self.density = self._calculate_average_density(materials)
            self.is_laminated = True
            self.layers = materials

        def _generate_laminated_name(self, materials):
            """Generate a descriptive name for laminated material"""
            if len(materials) == 1:
                material = materials[0]
                name = material.get('name', 'Unknown')
                return f"{name} (Single Layer)"

            layer_names = []
            for material in materials:
                name = material.get('name', 'Unknown')
                # Extract base material name (remove density info if present)
                base_name = name.split('(')[0].strip()
                layer_names.append(base_name)

            # Remove duplicates while preserving order
            unique_layers = []
            for layer in layer_names:
                if layer not in unique_layers:
                    unique_layers.append(layer)

            if len(unique_layers) == 1:
                return f"{unique_layers[0]} ({len(materials)}-Layer)"
            else:
                return f"{' / '.join(unique_layers)} (Laminated)"

        def _calculate_average_density(self, materials):
            """Calculate average density for laminated material"""
            densities = []
            for material in materials:
                if 'density' in material:
                    try:
                        densities.append(float(material['density']))
                    except (ValueError, TypeError):
                        pass
                # Try to extract density from material name if available
                elif 'name' in material:
                    name = material['name']
                    # Look for density in parentheses in name
                    import re
                    match = re.search(r'\(([\d.]+)\s*g/cm³\)', name)
                    if match:
                        try:
                            densities.append(float(match.group(1)))
                        except (ValueError, TypeError):
                            pass

            if densities:
                return round(sum(densities) / len(densities), 3)
            else:
                return 0.0  # Default density if none found

    return LaminatedMaterial(materials)


def create_laminated_material_from_structure(input_data):
    """Create laminated material from structured input data"""
    materials = []

    # Check primary material
    if 'primary_material_id' in input_data and input_data['primary_material_id']:
        try:
            primary_material = PlasticMaterial.objects.get(id=input_data['primary_material_id'])
            materials.append({
                'name': primary_material.name,
                'density': primary_material.density,
                'type': 'primary'
            })
        except (PlasticMaterial.DoesNotExist, ValueError):
            pass

    # Check secondary material
    if 'secondary_material_id' in input_data and input_data['secondary_material_id']:
        try:
            secondary_material = PlasticMaterial.objects.get(id=input_data['secondary_material_id'])
            materials.append({
                'name': secondary_material.name,
                'density': secondary_material.density,
                'type': 'secondary'
            })
        except (PlasticMaterial.DoesNotExist, ValueError):
            pass

    # Check third material
    if 'third_material_id' in input_data and input_data['third_material_id']:
        try:
            third_material = PlasticMaterial.objects.get(id=input_data['third_material_id'])
            materials.append({
                'name': third_material.name,
                'density': third_material.density,
                'type': 'third'
            })
        except (PlasticMaterial.DoesNotExist, ValueError):
            pass

    # Check fourth material
    if 'fourth_material_id' in input_data and input_data['fourth_material_id']:
        try:
            fourth_material = PlasticMaterial.objects.get(id=input_data['fourth_material_id'])
            materials.append({
                'name': fourth_material.name,
                'density': fourth_material.density,
                'type': 'fourth'
            })
        except (PlasticMaterial.DoesNotExist, ValueError):
            pass

    if materials:
        return create_laminated_material_object(materials)

    return None


@login_required
def download_calculation_history(request, format_type):
    """Download calculation history in various formats"""

    # Import all section models
    from extrusion.models import ExtrusionCalculation
    from printing.models import PrintingCalculation
    from lamination.models import LaminationCalculation
    from slitting.models import SlittingCalculation
    from bag_making.models import BagMakingCalculation
    from sales.models import SalesCalculation

    all_calculations = []

    # Get calculations from each section with proper handling
    try:
        extrusion_calculations = ExtrusionCalculation.objects.filter(user=request.user)
        if hasattr(ExtrusionCalculation, 'material'):
            extrusion_calculations = extrusion_calculations.select_related('material')
        for calc in extrusion_calculations:
            calc.section = 'extrusion'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading extrusion calculations for export: {e}")

    try:
        printing_calculations = PrintingCalculation.objects.filter(user=request.user)
        if hasattr(PrintingCalculation, 'material'):
            printing_calculations = printing_calculations.select_related('material')
        for calc in printing_calculations:
            calc.section = 'printing'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading printing calculations for export: {e}")

    try:
        lamination_calculations = LaminationCalculation.objects.filter(user=request.user)
        if hasattr(LaminationCalculation, 'material'):
            lamination_calculations = lamination_calculations.select_related('material')
        for calc in lamination_calculations:
            calc.section = 'lamination'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading lamination calculations for export: {e}")

    try:
        slitting_calculations = SlittingCalculation.objects.filter(user=request.user)
        if hasattr(SlittingCalculation, 'material'):
            slitting_calculations = slitting_calculations.select_related('material')
        for calc in slitting_calculations:
            calc.section = 'slitting'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading slitting calculations for export: {e}")

    try:
        bag_making_calculations = BagMakingCalculation.objects.filter(user=request.user)
        if hasattr(BagMakingCalculation, 'material'):
            bag_making_calculations = bag_making_calculations.select_related('material')
        for calc in bag_making_calculations:
            calc.section = 'bag_making'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading bag making calculations for export: {e}")

    try:
        sales_calculations = SalesCalculation.objects.filter(user=request.user)
        for calc in sales_calculations:
            calc.section = 'sales'
            calc.display_material = get_display_material(calc)
            all_calculations.append(calc)
    except Exception as e:
        print(f"Error loading sales calculations for export: {e}")

    if format_type == 'json':
        return download_json_history(all_calculations, request.user.username)
    elif format_type == 'csv':
        return download_csv_history(all_calculations, request.user.username)
    elif format_type == 'txt':
        return download_text_history(all_calculations, request.user.username)
    else:
        return JsonResponse({'error': 'Invalid format'})


def download_json_history(calculations, username):
    """Download history as JSON"""
    data = {
        'user': username,
        'export_date': datetime.now().isoformat(),
        'total_calculations': len(calculations),
        'calculations': []
    }

    for calc in calculations:
        # Use the display_material we set earlier
        material_info = 'N/A'
        if hasattr(calc, 'display_material') and calc.display_material:
            material_info = calc.display_material.name

        calculation_data = {
            'section': get_section_name(calc),
            'calculation_type': get_calculation_type_display(calc),
            'material': material_info,
            'timestamp': calc.timestamp.isoformat(),
            'input_data': calc.input_data,
            'result_data': calc.result_data,
        }
        data['calculations'].append(calculation_data)

    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response[
        'Content-Disposition'] = f'attachment; filename="{username}_calculations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    return response


def download_csv_history(calculations, username):
    """Download history as CSV"""
    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = f'attachment; filename="{username}_calculations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Section', 'Calculation Type', 'Material', 'Timestamp', 'Input Data', 'Result Data'])

    for calc in calculations:
        # Use the display_material we set earlier
        material_info = 'N/A'
        if hasattr(calc, 'display_material') and calc.display_material:
            material_info = calc.display_material.name

        writer.writerow([
            get_section_name(calc),
            get_calculation_type_display(calc),
            material_info,
            calc.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            json.dumps(calc.input_data),
            json.dumps(calc.result_data)
        ])

    return response


def download_text_history(calculations, username):
    """Download history as formatted text"""
    content = f"Calculation History for {username}\n"
    content += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Total Calculations: {len(calculations)}\n"
    content += "=" * 80 + "\n\n"

    for i, calc in enumerate(calculations, 1):
        # Use the display_material we set earlier
        material_info = 'N/A'
        if hasattr(calc, 'display_material') and calc.display_material:
            material_info = calc.display_material.name

        content += f"Calculation #{i}\n"
        content += f"Section: {get_section_name(calc)}\n"
        content += f"Type: {get_calculation_type_display(calc)}\n"
        content += f"Material: {material_info}\n"
        content += f"Timestamp: {calc.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "Input Data:\n"

        # Format input data
        for key, value in calc.input_data.items():
            content += f"  {key}: {value}\n"

        content += "Results:\n"
        # Format result data
        for key, value in calc.result_data.items():
            content += f"  {key}: {value}\n"

        content += "-" * 40 + "\n\n"

    response = HttpResponse(content, content_type='text/plain')
    response[
        'Content-Disposition'] = f'attachment; filename="{username}_calculations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    return response


def get_section_name(calculation):
    """Get the section name from calculation object"""
    if hasattr(calculation, 'section'):
        section_map = {
            'extrusion': 'Extrusion',
            'printing': 'Printing',
            'lamination': 'Lamination',
            'slitting': 'Slitting',
            'bag_making': 'Bag Making',
            'sales': 'Sales'
        }
        return section_map.get(calculation.section, 'Unknown')

    model_name = calculation.__class__.__name__
    if 'Extrusion' in model_name:
        return 'Extrusion'
    elif 'Printing' in model_name:
        return 'Printing'
    elif 'Lamination' in model_name:
        return 'Lamination'
    elif 'Slitting' in model_name:
        return 'Slitting'
    elif 'BagMaking' in model_name:
        return 'Bag Making'
    elif 'Sales' in model_name:
        return 'Sales'
    else:
        return 'Unknown'


def get_calculation_type_display(calculation):
    """Get the display name for calculation type"""
    if hasattr(calculation, 'get_calculation_type_display'):
        return calculation.get_calculation_type_display()
    elif hasattr(calculation, 'calculation_type'):
        return calculation.calculation_type.replace('_', ' ').title()
    else:
        return 'Unknown'


def is_recent(timestamp):
    """Check if timestamp is within last 7 days"""
    from datetime import datetime, timedelta
    one_week_ago = datetime.now() - timedelta(days=7)
    return timestamp.replace(tzinfo=None) >= one_week_ago
