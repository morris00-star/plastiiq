from django.core.management.base import BaseCommand
from calculator.models import PlasticMaterial


class Command(BaseCommand):
    help = 'Load initial plastic material density data'

    def handle(self, *args, **kwargs):
        materials_data = [
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


            # --- LDPE (measured samples) ---
            {'name': 'W/B Ldpe', 'code': 'ldpe_w_b_ldpe', 'material_type': 'FILM', 'density': 0.9457, 'description': 'W/B Ldpe - measured extrusion density', 'is_ldpe': True},
            {'name': 'G/W LDPE', 'code': 'ldpe_g_w', 'material_type': 'FILM', 'density': 0.94, 'description': 'g/w LDPE - measured extrusion density', 'is_ldpe': True},
            {'name': 'R/W LDPE', 'code': 'ldpe_r_w', 'material_type': 'FILM', 'density': 0.949, 'description': 'R/W LDPE - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Red', 'code': 'ldpe_red', 'material_type': 'FILM', 'density': 0.936, 'description': 'LDPE Red - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE clear', 'code': 'ldpe_base', 'material_type': 'FILM', 'density': 0.9186, 'description': 'LDPE - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Laminate', 'code': 'ldpe_laminate', 'material_type': 'FILM', 'density': 0.926, 'description': 'LDPE Laminate - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE yellow', 'code': 'ldpe_yellow', 'material_type': 'FILM', 'density': 0.936, 'description': 'LDPE yellow - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE tint yellow', 'code': 'ldpe_tint_yellow', 'material_type': 'FILM', 'density': 0.9226, 'description': 'LDPE tint yellow - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE coffee brown', 'code': 'ldpe_coffee_brown', 'material_type': 'FILM', 'density': 0.9277, 'description': 'LDPE coffee brown - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE black recycle', 'code': 'ldpe_black_recycle', 'material_type': 'FILM', 'density': 0.9302, 'description': 'LDPE black recycle - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE shrink', 'code': 'ldpe_shrink', 'material_type': 'FILM', 'density': 0.9212, 'description': 'LDPE shrink - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE white', 'code': 'ldpe_white', 'material_type': 'FILM', 'density': 0.9509, 'description': 'LDPE white - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Pale green (Y/W/G)', 'code': 'ldpe_pale_green', 'material_type': 'FILM', 'density': 0.9331, 'description': 'LDPE Pale green (Y/W/G) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Pale Yellow/White (Y/W)', 'code': 'ldpe_pale_yellow_white', 'material_type': 'FILM', 'density': 0.9351, 'description': 'LDPE Pale Yellow/White (Y/W) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE G/W', 'code': 'ldpe_g_w_2', 'material_type': 'FILM', 'density': 0.9392, 'description': 'LDPE G/W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE B/W', 'code': 'ldpe_b_w', 'material_type': 'FILM', 'density': 0.9355, 'description': 'LDPE B/W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE P/W', 'code': 'ldpe_p_w', 'material_type': 'FILM', 'density': 0.9342, 'description': 'LDPE P/W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE R/W', 'code': 'ldpe_r_w_2', 'material_type': 'FILM', 'density': 0.9342, 'description': 'LDPE R/W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE R/W (Heavy Red)', 'code': 'ldpe_r_w_3', 'material_type': 'FILM', 'density': 0.9533, 'description': 'LDPE R/W (Heavy Red) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Yellow', 'code': 'ldpe_yellow_2', 'material_type': 'FILM', 'density': 0.9272, 'description': 'LDPE Yellow - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE D2W', 'code': 'ldpe_d2w', 'material_type': 'FILM', 'density': 0.9207, 'description': 'LDPE D2W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE O/W', 'code': 'ldpe_o_w', 'material_type': 'FILM', 'density': 0.9355, 'description': 'LDPE O/W - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE D2W/G', 'code': 'ldpe_d2w_g', 'material_type': 'FILM', 'density': 0.9257, 'description': 'LDPE D2W/G - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE TInt blue', 'code': 'ldpe_tint_blue', 'material_type': 'FILM', 'density': 0.9169, 'description': 'LDPE TInt blue - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE blue', 'code': 'ldpe_blue', 'material_type': 'FILM', 'density': 0.9304, 'description': 'LDPE blue - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Tint Pink', 'code': 'ldpe_tint_pink', 'material_type': 'FILM', 'density': 0.9216, 'description': 'LDPE Tint Pink - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE TInt yellow', 'code': 'ldpe_tint_yellow_2', 'material_type': 'FILM', 'density': 0.9183, 'description': 'LDPE TInt yellow - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE black', 'code': 'ldpe_black', 'material_type': 'FILM', 'density': 0.9179, 'description': 'LDPE black - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE yellow', 'code': 'ldpe_yellow_3', 'material_type': 'FILM', 'density': 0.9277, 'description': 'LDPE yellow - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE TInt blue', 'code': 'ldpe_tint_blue_2', 'material_type': 'FILM', 'density': 0.9214, 'description': 'LDPE TInt blue - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE TInt red', 'code': 'ldpe_tint_red', 'material_type': 'FILM', 'density': 0.9201, 'description': 'LDPE TInt red - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Golden yellow', 'code': 'ldpe_golden_yellow', 'material_type': 'FILM', 'density': 0.9315, 'description': 'LDPE Golden yellow - measured extrusion density', 'is_ldpe': True},

            # --- HDPE (measured samples) ---
            {'name': 'HDPE brown', 'code': 'hdpe_brown', 'material_type': 'FILM', 'density': 0.942, 'description': 'HDPE brown - measured extrusion density'},
            {'name': 'HDPE coffee brown', 'code': 'hdpe_coffee_brown', 'material_type': 'FILM', 'density': 0.938, 'description': 'HDPE coffee brown - measured extrusion density'},
            {'name': 'HDPE gray', 'code': 'hdpe_gray', 'material_type': 'FILM', 'density': 1.088, 'description': 'HDPE gray - measured extrusion density (with filler)'},
            {'name': 'HDPE pink', 'code': 'hdpe_pink', 'material_type': 'FILM', 'density': 0.938, 'description': 'HDPE pink - measured extrusion density'},
            {'name': 'HDPE purple', 'code': 'hdpe_purple', 'material_type': 'FILM', 'density': 0.9375, 'description': 'HDPE purple - measured extrusion density'},
            {'name': 'HDPE siege brown', 'code': 'hdpe_siege_brown', 'material_type': 'FILM', 'density': 1.088, 'description': 'HDPE siege brown - measured extrusion density (with filler - suspected)'},
            {'name': 'HDPE lemon green', 'code': 'hdpe_lemon_green', 'material_type': 'FILM', 'density': 0.944, 'description': 'HDPE lemon green - measured extrusion density'},
            {'name': 'HDPE orange', 'code': 'hdpe_orange', 'material_type': 'FILM', 'density': 0.946, 'description': 'HDPE orange - measured extrusion density'},
            {'name': 'HDPE purple', 'code': 'hdpe_purple_2', 'material_type': 'FILM', 'density': 0.998, 'description': 'HDPE purple - measured extrusion density (with filler)'},
            {'name': 'HDPE dark gray', 'code': 'hdpe_dark_gray', 'material_type': 'FILM', 'density': 0.948, 'description': 'HDPE dark gray - measured extrusion density'},
            {'name': 'HDPE tint blue', 'code': 'hdpe_tint_blue', 'material_type': 'FILM', 'density': 1.002, 'description': 'HDPE tint blue - measured extrusion density (with filler - suspected)'},
            {'name': 'HDPE tint red', 'code': 'hdpe_tint_red', 'material_type': 'FILM', 'density': 1.005, 'description': 'HDPE tint red - measured extrusion density (with filler - suspected)'},
            {'name': 'HDPE', 'code': 'hdpe_base', 'material_type': 'FILM', 'density': 0.9268, 'description': 'HDPE - measured extrusion density (without filler)'},
            {'name': 'HDPE red', 'code': 'hdpe_red', 'material_type': 'FILM', 'density': 0.9471, 'description': 'HDPE red - measured extrusion density'},
            {'name': 'HDPE white', 'code': 'hdpe_white', 'material_type': 'FILM', 'density': 1.0285, 'description': 'HDPE white - measured extrusion density (with filler)'},
            {'name': 'HDPE clear', 'code': 'hdpe_clear', 'material_type': 'FILM', 'density': 1.0014, 'description': 'HDPE clear - measured extrusion density (with filler)'},
            {'name': 'HDPE white', 'code': 'hdpe_white_2', 'material_type': 'FILM', 'density': 0.9539, 'description': 'HDPE white - measured extrusion density (without filler)'},
            {'name': 'HDPE blue', 'code': 'hdpe_blue', 'material_type': 'FILM', 'density': 1.037, 'description': 'HDPE blue - measured extrusion density (with filler - suspected)'},
            {'name': 'HDPE black', 'code': 'hdpe_black', 'material_type': 'FILM', 'density': 1.005, 'description': 'HDPE black - measured extrusion density (with filler - suspected)'},
            {'name': 'HDPE dark green', 'code': 'hdpe_dark_green', 'material_type': 'FILM', 'density': 0.9825, 'description': 'HDPE dark green - measured extrusion density'},
            {'name': 'HDPE golden yello', 'code': 'hdpe_golden_yello', 'material_type': 'FILM', 'density': 0.9943, 'description': 'HDPE golden yello - measured extrusion density'},
            {'name': 'HDPE Blue', 'code': 'hdpe_blue_2', 'material_type': 'FILM', 'density': 0.9791, 'description': 'HDPE Blue - measured extrusion density (with filler)'},
            {'name': 'HDPE GOlden yellow - white', 'code': 'hdpe_golden_yellow_white', 'material_type': 'FILM', 'density': 0.9379, 'description': 'HDPE GOlden yellow - white - measured extrusion density'},
            {'name': 'HDPE Dark green', 'code': 'hdpe_dark_green_2', 'material_type': 'FILM', 'density': 0.9884, 'description': 'HDPE Dark green - measured extrusion density (with filler)'},
            {'name': 'HDPE Pale green', 'code': 'hdpe_pale_green', 'material_type': 'FILM', 'density': 0.9855, 'description': 'HDPE Pale green - measured extrusion density (with filler)'},
            {'name': 'HDPE Pale green and Dark green', 'code': 'hdpe_pale_green_and_dark_green', 'material_type': 'FILM', 'density': 0.9859, 'description': 'HDPE Pale green and Dark green - measured extrusion density (with filler)'},
            {'name': 'HDPE Orange', 'code': 'hdpe_orange_2', 'material_type': 'FILM', 'density': 0.9804, 'description': 'HDPE Orange - measured extrusion density (with filler)'},
            {'name': 'HDPE TInt blue', 'code': 'hdpe_tint_blue_2', 'material_type': 'FILM', 'density': 0.9559, 'description': 'HDPE TInt blue - measured extrusion density'},
            {'name': 'HDPE TInt green', 'code': 'hdpe_tint_green', 'material_type': 'FILM', 'density': 0.9308, 'description': 'HDPE TInt green - measured extrusion density'},
            {'name': 'HDPE bLACK', 'code': 'hdpe_black_2', 'material_type': 'FILM', 'density': 0.9367, 'description': 'HDPE bLACK - measured extrusion density'},
            {'name': 'HDPE TInt red', 'code': 'hdpe_tint_red_2', 'material_type': 'FILM', 'density': 0.9506, 'description': 'HDPE TInt red - measured extrusion density'},
            {'name': 'HDPE SKY BLUE', 'code': 'hdpe_sky_blue', 'material_type': 'FILM', 'density': 1.0223, 'description': 'HDPE SKY BLUE - measured extrusion density (with filler)'},
            {'name': 'HDPE Brown', 'code': 'hdpe_brown_2', 'material_type': 'FILM', 'density': 1.0223, 'description': 'HDPE Brown - measured extrusion density (with filler)'},
            {'name': 'HDPE Tint Orange', 'code': 'hdpe_tint_orange', 'material_type': 'FILM', 'density': 1.0056, 'description': 'HDPE Tint Orange - measured extrusion density (with filler)'},
            {'name': 'HDPE Tint yellow', 'code': 'hdpe_tint_yellow', 'material_type': 'FILM', 'density': 1.0015, 'description': 'HDPE Tint yellow - measured extrusion density (with filler)'},
            {'name': 'HDPE Brown', 'code': 'hdpe_brown_3', 'material_type': 'FILM', 'density': 0.9909, 'description': 'HDPE Brown - measured extrusion density (with filler)'},

            # --- NYLON (measured samples) ---
            {'name': 'NYLON white', 'code': 'nylon_white', 'material_type': 'FILM', 'density': 0.9529, 'description': 'NYLON white - measured extrusion density'},
            {'name': 'NYLON clear', 'code': 'nylon_clear', 'material_type': 'FILM', 'density': 0.9383, 'description': 'NYLON clear - measured extrusion density'},

            # --- EVOH (measured samples) ---
            {'name': 'UHT/EVOH W/B', 'code': 'evoh_uht_w_b', 'material_type': 'FILM', 'density': 0.9691, 'description': 'UHT/EVOH W/B - measured extrusion density'},
            {'name': 'PE/EVOH/PE-AF', 'code': 'evoh_pe_pe_af', 'material_type': 'FILM', 'density': 0.9552, 'description': 'PE/EVOH/PE-AF - measured extrusion density'},

            # --- PP (measured samples) ---
            {'name': 'pp', 'code': 'pp_base', 'material_type': 'FILM', 'density': 0.9061, 'description': 'pp - measured extrusion density'},


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

