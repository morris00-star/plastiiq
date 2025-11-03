from django.core.management.base import BaseCommand
from calculator.models import PlasticMaterial


class Command(BaseCommand):
    help = 'Load initial plastic material density data'

    def handle(self, *args, **kwargs):
        materials_data = [
            # Plastic Films
            {'name': 'LDPE', 'code': 'LDPE', 'material_type': 'FILM', 'density': 0.925,
             'description': 'Low-Density Polyethylene'},
            {'name': 'Colored LDPE', 'code': 'LDPE_colored', 'material_type': 'FILM', 'density': 0.925,
             'description': 'Colored LDPE'},
            {'name': 'HDPE', 'code': 'HDPE', 'material_type': 'FILM', 'density': 0.955,
             'description': 'High-Density Polyethylene'},
            {'name': 'Colored HDPE', 'code': 'HDPE_colored', 'material_type': 'FILM', 'density': 0.960,
             'description': 'Colored HDPE'},
            {'name': 'CPP', 'code': 'CPP', 'material_type': 'FILM', 'density': 0.910,
             'description': 'Cast Polypropylene'},
            {'name': 'Metallized CPP', 'code': 'CPP_metallized', 'material_type': 'FILM', 'density': 0.910,
             'description': 'Metallized CPP'},
            {'name': 'Pearlized CPP', 'code': 'CPP_pearlized', 'material_type': 'FILM', 'density': 0.860,
             'description': 'Pearlized CPP'},
            {'name': 'BOPP', 'code': 'BOPP', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Biaxially Oriented Polypropylene'},
            {'name': 'White/Colored BOPP', 'code': 'BOPP_white_colored', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Colored BOPP'},
            {'name': 'Metallized BOPP', 'code': 'BOPP_metallized', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Metallized BOPP'},
            {'name': 'Pearlized BOPP', 'code': 'BOPP_pearlized', 'material_type': 'FILM', 'density': 0.790,
             'description': 'Pearlized BOPP'},
            {'name': 'Matt Finish BOPP', 'code': 'BOPP_matt', 'material_type': 'FILM', 'density': 0.855,
             'description': 'Matt Finish BOPP'},
            {'name': 'PET', 'code': 'PET', 'material_type': 'FILM', 'density': 1.365,
             'description': 'Polyethylene Terephthalate'},
            {'name': 'Twist PET', 'code': 'PET_twist', 'material_type': 'FILM', 'density': 1.335,
             'description': 'Twist PET'},
            {'name': 'Metallized PET', 'code': 'PET_metallized', 'material_type': 'FILM', 'density': 1.365,
             'description': 'Metallized PET'},
            {'name': 'Twist Metallized PET', 'code': 'PET_twist_metallized', 'material_type': 'FILM', 'density': 1.335,
             'description': 'Twist Metallized PET'},
            {'name': 'NYLON', 'code': 'NYLON', 'material_type': 'FILM', 'density': 1.145, 'description': 'Nylon Film'},
            {'name': 'Colored NYLON', 'code': 'NYLON_colored', 'material_type': 'FILM', 'density': 1.145,
             'description': 'Colored Nylon'},
            {'name': 'Polypropylene', 'code': 'PP', 'material_type': 'FILM', 'density': 0.908,
             'description': 'General Polypropylene'},

            # Lamination Components
            {'name': 'Ink', 'code': 'ink', 'material_type': 'INK', 'density': 1.100, 'description': 'Printing Ink'},
            {'name': 'Ethyl Acetate', 'code': 'ethyl_acetate', 'material_type': 'SOLVENT', 'density': 0.902,
             'description': 'Solvent'},
            {'name': 'Adhesive', 'code': 'adhesive', 'material_type': 'ADHESIVE', 'density': 1.050,
             'description': 'Lamination Adhesive'},
            {'name': 'Hardener', 'code': 'hardener', 'material_type': 'HARDENER', 'density': 1.150,
             'description': 'Adhesive Hardener'},
        ]

        for data in materials_data:
            material, created = PlasticMaterial.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {material.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {material.name}'))
