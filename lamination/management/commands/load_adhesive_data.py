from django.core.management.base import BaseCommand
from lamination.models import AdhesiveSystem


class Command(BaseCommand):
    help = 'Load initial adhesive system data'

    def handle(self, *args, **kwargs):
        adhesive_data = [
            {
                'name': 'Standard 2-Part PU Adhesive',
                'code': 'PU_STD',
                'adhesive_density': 1.15,
                'hardener_density': 1.20,
                'ethyl_acetate_density': 0.902,
                'mix_ratio_adhesive': 10,
                'mix_ratio_hardener': 1,
                'solid_content': 35.0,
                'description': 'Standard polyurethane adhesive for general lamination'
            },
            {
                'name': 'High Performance PU Adhesive',
                'code': 'PU_HP',
                'adhesive_density': 1.18,
                'hardener_density': 1.22,
                'ethyl_acetate_density': 0.902,
                'mix_ratio_adhesive': 8,
                'mix_ratio_hardener': 1,
                'solid_content': 40.0,
                'description': 'High performance adhesive for demanding applications'
            },
            {
                'name': 'Water-based Adhesive',
                'code': 'WB_STD',
                'adhesive_density': 1.05,
                'hardener_density': 1.08,
                'ethyl_acetate_density': 0.902,
                'mix_ratio_adhesive': 5,
                'mix_ratio_hardener': 1,
                'solid_content': 45.0,
                'description': 'Water-based adhesive system'
            },
        ]

        for data in adhesive_data:
            system, created = AdhesiveSystem.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {system.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {system.name}'))
