from django.core.management.base import BaseCommand
from calculator.models import PlasticMaterial


class Command(BaseCommand):
    help = 'Load initial plastic material density data'

    def handle(self, *args, **kwargs):
        materials_data = [
            # --- LDPE (base + all color variants) ---
            {'name': 'LDPE', 'code': 'LDPE', 'material_type': 'FILM', 'density': 0.925,
             'description': 'Low-Density Polyethylene (natural)', 'is_ldpe': True},
            {'name': 'LDPE Black', 'code': 'ldpe_black', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Black', 'is_ldpe': True},
            {'name': 'LDPE Blue', 'code': 'ldpe_blue', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Blue', 'is_ldpe': True},
            {'name': 'LDPE Red', 'code': 'ldpe_red', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Red', 'is_ldpe': True},
            {'name': 'LDPE Gray', 'code': 'ldpe_gray', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Gray', 'is_ldpe': True},
            {'name': 'LDPE White', 'code': 'ldpe_white', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - White', 'is_ldpe': True},
            {'name': 'LDPE Brown', 'code': 'ldpe_brown', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Brown', 'is_ldpe': True},
            {'name': 'LDPE Yellow', 'code': 'ldpe_yellow', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Yellow', 'is_ldpe': True},
            {'name': 'LDPE Green', 'code': 'ldpe_green', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE - Green', 'is_ldpe': True},
            {'name': 'LDPE W/B', 'code': 'ldpe_w_b', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE W/B (Outer White / Inner Black)', 'is_ldpe': True},
            {'name': 'LDPE Y/W', 'code': 'ldpe_y_w', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE Y/W (Outer Yellow / Inner White)', 'is_ldpe': True},
            {'name': 'LDPE B/W', 'code': 'ldpe_b_w', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE B/W (Outer Blue / Inner White)', 'is_ldpe': True},
            {'name': 'LDPE R/W', 'code': 'ldpe_r_w', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE R/W (Outer Red / Inner White)', 'is_ldpe': True},
            {'name': 'LDPE G/W', 'code': 'ldpe_g_w', 'material_type': 'FILM', 'density': 0.925,
             'description': 'LDPE G/W (Outer Green / Inner White)', 'is_ldpe': True},

            # --- HDPE (base + all color variants) ---
            {'name': 'HDPE', 'code': 'HDPE', 'material_type': 'FILM', 'density': 0.955,
             'description': 'High-Density Polyethylene (natural)'},
            {'name': 'HDPE White', 'code': 'hdpe_white', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - White'},
            {'name': 'HDPE Blue', 'code': 'hdpe_blue', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Blue'},
            {'name': 'HDPE Black', 'code': 'hdpe_black', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Black'},
            {'name': 'HDPE Yellow', 'code': 'hdpe_yellow', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Yellow'},
            {'name': 'HDPE Brown', 'code': 'hdpe_brown', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Brown'},
            {'name': 'HDPE Red', 'code': 'hdpe_red', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Red'},
            {'name': 'HDPE Green', 'code': 'hdpe_green', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Green'},
            {'name': 'HDPE Gray', 'code': 'hdpe_gray', 'material_type': 'FILM', 'density': 0.960,
             'description': 'HDPE - Gray'},

            # --- CPP / BOPP / PET (unchanged) ---
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

            # --- NYLON (Clear and White only) ---
            {'name': 'NYLON Clear', 'code': 'nylon_clear', 'material_type': 'FILM', 'density': 1.145,
             'description': 'Nylon Film - Clear'},
            {'name': 'NYLON White', 'code': 'nylon_white', 'material_type': 'FILM', 'density': 1.145,
             'description': 'Nylon Film - White'},

            # --- EVOH (Clear and W/B) - NOTE: density is a placeholder, please confirm ---
            {'name': 'EVOH Clear', 'code': 'evoh_clear', 'material_type': 'FILM', 'density': 1.14,
             'description': 'EVOH Barrier Film - Clear (density unconfirmed - please verify)'},
            {'name': 'EVOH W/B', 'code': 'evoh_w_b', 'material_type': 'FILM', 'density': 1.14,
             'description': 'EVOH Barrier Film W/B (Outer White / Inner Black) (density unconfirmed - please verify)'},

            {'name': 'Polypropylene', 'code': 'PP', 'material_type': 'FILM', 'density': 0.908,
             'description': 'General Polypropylene'},

            # --- Lamination Components (unchanged) ---
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

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(materials_data)} materials processed.'
        ))
