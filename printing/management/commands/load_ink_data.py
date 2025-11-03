from django.core.management.base import BaseCommand
from printing.models import InkType


class Command(BaseCommand):
    help = 'Load initial ink type data'

    def handle(self, *args, **kwargs):
        ink_data = [
            {'name': 'Standard Flexo Ink', 'code': 'FLEXO_STD', 'density': 1.2, 'coverage_rate': 1.5},
            {'name': 'UV Flexo Ink', 'code': 'FLEXO_UV', 'density': 1.3, 'coverage_rate': 1.4},
            {'name': 'Water-based Ink', 'code': 'WATER_BASED', 'density': 1.1, 'coverage_rate': 1.6},
            {'name': 'Solvent-based Ink', 'code': 'SOLVENT_BASED', 'density': 1.25, 'coverage_rate': 1.45},
            {'name': 'Metallic Ink', 'code': 'METALLIC', 'density': 1.8, 'coverage_rate': 1.2},
            {'name': 'White Ink', 'code': 'WHITE', 'density': 1.4, 'coverage_rate': 1.35},
        ]

        for data in ink_data:
            ink, created = InkType.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {ink.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {ink.name}'))
