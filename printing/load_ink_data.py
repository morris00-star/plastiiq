from django.core.management.base import BaseCommand
from printing.models import InkType


class Command(BaseCommand):
    help = 'Load initial ink type data'

    def handle(self, *args, **kwargs):
        ink_data = [
            {'name': 'Cyan Process', 'code': 'CYAN_PROCESS', 'coverage_gsm': 1.2, 'density_g_cm3': 1.35,
             'description': 'Standard process cyan ink'},
            {'name': 'Magenta Process', 'code': 'MAGENTA_PROCESS', 'coverage_gsm': 1.1, 'density_g_cm3': 1.38,
             'description': 'Standard process magenta ink'},
            {'name': 'Yellow Process', 'code': 'YELLOW_PROCESS', 'coverage_gsm': 1.3, 'density_g_cm3': 1.32,
             'description': 'Standard process yellow ink'},
            {'name': 'Black Process', 'code': 'BLACK_PROCESS', 'coverage_gsm': 0.9, 'density_g_cm3': 1.42,
             'description': 'Standard process black ink'},
            {'name': 'White Opaque', 'code': 'WHITE_OPAQUE', 'coverage_gsm': 2.5, 'density_g_cm3': 1.45,
             'description': 'White opaque ink for underprinting'},
            {'name': 'Metallic Silver', 'code': 'METALLIC_SILVER', 'coverage_gsm': 1.8, 'density_g_cm3': 1.65,
             'description': 'Metallic silver specialty ink'},
            {'name': 'Varnish', 'code': 'VARNISH', 'coverage_gsm': 1.0, 'density_g_cm3': 1.25,
             'description': 'Protective varnish coating'},
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
