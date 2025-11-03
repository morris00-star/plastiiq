import json
import re
from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def get_section_name(calculation):
    """Get section name from calculation object"""
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

@register.filter
def get_calculation_type_display(calculation):
    """Get display name for calculation type"""
    if hasattr(calculation, 'get_calculation_type_display'):
        return calculation.get_calculation_type_display()
    elif hasattr(calculation, 'calculation_type'):
        return calculation.calculation_type.replace('_', ' ').title()
    else:
        return 'Unknown'

@register.filter
def get_section_badge(calculation):
    """Get Bootstrap badge class for section"""
    section = get_section_name(calculation)
    badge_classes = {
        'Extrusion': 'bg-success',
        'Printing': 'bg-info',
        'Lamination': 'bg-warning text-dark',
        'Slitting': 'bg-secondary',
        'Bag Making': 'bg-dark',
        'Sales':'bg-purple',
    }
    return badge_classes.get(section, 'bg-primary')

@register.filter
def get_section_icon(calculation):
    """Get Font Awesome icon for section"""
    section = get_section_name(calculation)
    icon_classes = {
        'Extrusion': 'fas fa-industry',
        'Printing': 'fas fa-print',
        'Lamination': 'fas fa-layer-group',
        'Slitting': 'fas fa-cut',
        'Bag Making': 'fas fa-shopping-bag',
        'Sales':'fas fa-money-bill-wave',
    }
    return icon_classes.get(section, 'fas fa-calculator')

@register.filter
def is_recent(calculation):
    """Check if calculation is from last 7 days"""
    one_week_ago = datetime.now() - timedelta(days=7)
    return calculation.timestamp.replace(tzinfo=None) >= one_week_ago


@register.filter
def extrusion_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'extrusion'])

@register.filter
def printing_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'printing'])

@register.filter
def lamination_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'lamination'])

@register.filter
def slitting_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'slitting'])

@register.filter
def bag_making_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'bag making'])

@register.filter
def sales_count(calculations):
    return len([c for c in calculations if hasattr(c, 'get_section_name') and c.get_section_name().lower() == 'sales'])


@register.filter
def parse_calculation_data(value):
    """Parse and clean calculation data for display"""
    if not value:
        return {}

    try:
        # If it's already a dict, return it
        if isinstance(value, dict):
            return value

        # If it's a string, try to parse it
        if isinstance(value, str):
            cleaned = value.strip()

            # Remove surrounding quotes if present
            if (cleaned.startswith('"') and cleaned.endswith('"')) or \
                    (cleaned.startswith("'") and cleaned.endswith("'")):
                cleaned = cleaned[1:-1]

            # Replace Unicode escapes
            cleaned = cleaned.replace('\\u0027', "'")
            cleaned = cleaned.replace('\\U0027', "'")
            cleaned = cleaned.replace('\\"', '"')
            cleaned = cleaned.replace('\\\\', '\\')

            # Try to parse as JSON
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key-value pairs
                return extract_key_value_pairs(cleaned)

    except Exception as e:
        print(f"Error parsing calculation data: {e}")

    return {'raw_data': value}


def extract_key_value_pairs(data_string):
    """Extract key-value pairs from a string"""
    result = {}
    try:
        # Remove braces if present
        cleaned = data_string.strip()
        if cleaned.startswith('{') and cleaned.endswith('}'):
            cleaned = cleaned[1:-1]

        # Split by commas but be careful about nested structures
        pairs = []
        current_pair = ""
        brace_count = 0

        for char in cleaned:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ',' and brace_count == 0:
                pairs.append(current_pair.strip())
                current_pair = ""
                continue
            current_pair += char

        if current_pair:
            pairs.append(current_pair.strip())

        # Process each pair
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip().strip("'\"")
                value = value.strip().strip("'\"")

                # Try to convert numeric values
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except (ValueError, TypeError):
                    pass

                result[key] = value

    except Exception as e:
        print(f"Error extracting key-value pairs: {e}")
        result = {'error': 'Could not parse data', 'raw': data_string}

    return result

