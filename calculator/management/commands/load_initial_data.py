from django.core.management.base import BaseCommand
from calculator.models import PlasticMaterial

# ---------------------------------------------------------------------------
# NAMING LEGEND for two-tone/multi-layer color codes (e.g. "R/W", "Y/W/G"):
#   Format is OUTSIDE / INSIDE (or OUTSIDE / MIDDLE / INSIDE for 3 layers).
#   O=Orange, P=Purple, W=White, B=Black, R=Red, G=Green
#
#   EXCEPTION: 'LDPE B/W' (code ldpe_b_w) - here B means BLUE, not Black,
#   per plant floor convention for that specific film. Every other "B" in
#   these codes (including 'W/B Ldpe') follows the standard legend (B=Black).
#   This exception is called out explicitly in that entry's description below
#   to avoid it being misread later.
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = 'Load initial plastic material density data'

    def handle(self, *args, **kwargs):
        materials_data = [
            # --- CPP / BOPP / PET ---
            {'name': 'CPP', 'code': 'CPP', 'material_type': 'FILM', 'density': 0.910,
             'description': 'Cast Polypropylene (CPP) - clear/natural'},
            {'name': 'Metallized CPP', 'code': 'CPP_metallized', 'material_type': 'FILM', 'density': 0.910,
             'description': 'Cast Polypropylene (CPP) with a metallized (aluminum-vapor-deposited) layer'},
            {'name': 'Pearlized CPP', 'code': 'CPP_pearlized', 'material_type': 'FILM', 'density': 0.860,
             'description': 'Cast Polypropylene (CPP) with a pearlescent/opaque cavitated finish'},
            {'name': 'BOPP', 'code': 'BOPP', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Biaxially Oriented Polypropylene (BOPP) - clear/natural'},
            {'name': 'White/Colored BOPP', 'code': 'BOPP_white_colored', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Biaxially Oriented Polypropylene (BOPP) - white or custom-colored, opaque'},
            {'name': 'Metallized BOPP', 'code': 'BOPP_metallized', 'material_type': 'FILM', 'density': 0.905,
             'description': 'Biaxially Oriented Polypropylene (BOPP) with a metallized (aluminum-vapor-deposited) layer'},
            {'name': 'Pearlized BOPP', 'code': 'BOPP_pearlized', 'material_type': 'FILM', 'density': 0.790,
             'description': 'Biaxially Oriented Polypropylene (BOPP) with a pearlescent/opaque cavitated finish'},
            {'name': 'Matt Finish BOPP', 'code': 'BOPP_matt', 'material_type': 'FILM', 'density': 0.855,
             'description': 'Biaxially Oriented Polypropylene (BOPP) with a matt (low-gloss) surface finish'},
            {'name': 'PET', 'code': 'PET', 'material_type': 'FILM', 'density': 1.365,
             'description': 'Polyethylene Terephthalate (PET) - clear/natural'},
            {'name': 'Twist PET', 'code': 'PET_twist', 'material_type': 'FILM', 'density': 1.335,
             'description': 'Polyethylene Terephthalate (PET) - twist-grade for candy/confectionery wrap'},
            {'name': 'Metallized PET', 'code': 'PET_metallized', 'material_type': 'FILM', 'density': 1.365,
             'description': 'Polyethylene Terephthalate (PET) with a metallized (aluminum-vapor-deposited) layer'},
            {'name': 'Twist Metallized PET', 'code': 'PET_twist_metallized', 'material_type': 'FILM', 'density': 1.335,
             'description': 'Polyethylene Terephthalate (PET) - twist-grade with a metallized layer'},

            # --- LDPE (measured samples) ---
            {'name': 'W/B Ldpe', 'code': 'ldpe_w_b_ldpe', 'material_type': 'FILM', 'density': 0.9457,
             'description': 'LDPE two-layer film - White outside, Black inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'G/W LDPE', 'code': 'ldpe_g_w', 'material_type': 'FILM', 'density': 0.94,
             'description': 'LDPE two-layer film - Green outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'R/W LDPE', 'code': 'ldpe_r_w', 'material_type': 'FILM', 'density': 0.949,
             'description': 'LDPE two-layer film - Red outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Red', 'code': 'ldpe_red', 'material_type': 'FILM', 'density': 0.936,
             'description': 'LDPE - Red (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE clear', 'code': 'ldpe_base', 'material_type': 'FILM', 'density': 0.9186,
             'description': 'LDPE - clear/natural, base grade with no colorant - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Laminate', 'code': 'ldpe_laminate', 'material_type': 'FILM', 'density': 0.926,
             'description': 'LDPE - laminate sealant grade, used as the LDPE layer in laminated structures (not a color code) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE yellow', 'code': 'ldpe_yellow', 'material_type': 'FILM', 'density': 0.936,
             'description': 'LDPE - Yellow (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE tint yellow', 'code': 'ldpe_tint_yellow', 'material_type': 'FILM', 'density': 0.9226,
             'description': 'LDPE - light/translucent Yellow tint (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE coffee brown', 'code': 'ldpe_coffee_brown', 'material_type': 'FILM', 'density': 0.9277,
             'description': 'LDPE - Coffee Brown (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE black recycle', 'code': 'ldpe_black_recycle', 'material_type': 'FILM', 'density': 0.9302,
             'description': 'LDPE - Black, made from recycled material (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE shrink', 'code': 'ldpe_shrink', 'material_type': 'FILM', 'density': 0.9212,
             'description': 'LDPE - shrink film grade (not a color code) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE white', 'code': 'ldpe_white', 'material_type': 'FILM', 'density': 0.9509,
             'description': 'LDPE - White (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Pale green (Y/W/G)', 'code': 'ldpe_pale_green', 'material_type': 'FILM', 'density': 0.9331,
             'description': 'LDPE three-layer film - Yellow outside, White middle, Green inside (overall visual effect: pale green) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Pale Yellow/White (Y/W)', 'code': 'ldpe_pale_yellow_white', 'material_type': 'FILM', 'density': 0.9351,
             'description': 'LDPE two-layer film - pale Yellow outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE G/W', 'code': 'ldpe_g_w_2', 'material_type': 'FILM', 'density': 0.9392,
             'description': 'LDPE two-layer film - Green outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE B/W', 'code': 'ldpe_b_w', 'material_type': 'FILM', 'density': 0.9355,
             'description': 'LDPE two-layer film - Blue outside, White inside. NOTE: B here means Blue, not Black - this is the one exception to the standard color-letter legend used across these codes - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE P/W', 'code': 'ldpe_p_w', 'material_type': 'FILM', 'density': 0.9342,
             'description': 'LDPE two-layer film - Purple outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE R/W', 'code': 'ldpe_r_w_2', 'material_type': 'FILM', 'density': 0.9342,
             'description': 'LDPE two-layer film - Red outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE R/W (Heavy Red)', 'code': 'ldpe_r_w_3', 'material_type': 'FILM', 'density': 0.9533,
             'description': 'LDPE two-layer film - Red outside (heavier red pigment loading), White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Yellow', 'code': 'ldpe_yellow_2', 'material_type': 'FILM', 'density': 0.9272,
             'description': 'LDPE - Yellow (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE D2W', 'code': 'ldpe_d2w', 'material_type': 'FILM', 'density': 0.9207,
             'description': 'LDPE with d2w oxo-biodegradable additive - natural/clear (D2W is an additive technology, not a color code) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE O/W', 'code': 'ldpe_o_w', 'material_type': 'FILM', 'density': 0.9355,
             'description': 'LDPE two-layer film - Orange outside, White inside - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE D2W/G', 'code': 'ldpe_d2w_g', 'material_type': 'FILM', 'density': 0.9257,
             'description': 'LDPE with d2w oxo-biodegradable additive - Green (D2W is an additive technology, not a color code; G = Green) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE blue', 'code': 'ldpe_blue', 'material_type': 'FILM', 'density': 0.9304,
             'description': 'LDPE - Blue (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Tint Pink', 'code': 'ldpe_tint_pink', 'material_type': 'FILM', 'density': 0.9216,
             'description': 'LDPE - light/translucent Pink tint (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Tint yellow', 'code': 'ldpe_tint_yellow_2', 'material_type': 'FILM', 'density': 0.9183,
             'description': 'LDPE - light/translucent Yellow tint (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE black', 'code': 'ldpe_black', 'material_type': 'FILM', 'density': 0.9179,
             'description': 'LDPE - Black (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE yellow', 'code': 'ldpe_yellow_3', 'material_type': 'FILM', 'density': 0.9277,
             'description': 'LDPE - Yellow (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Tint blue', 'code': 'ldpe_tint_blue_2', 'material_type': 'FILM', 'density': 0.9214,
             'description': 'LDPE - light/translucent Blue tint (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Tint red', 'code': 'ldpe_tint_red', 'material_type': 'FILM', 'density': 0.9201,
             'description': 'LDPE - light/translucent Red tint (single layer/color) - measured extrusion density', 'is_ldpe': True},
            {'name': 'LDPE Golden yellow', 'code': 'ldpe_golden_yellow', 'material_type': 'FILM', 'density': 0.9315,
             'description': 'LDPE - Golden Yellow (single layer/color) - measured extrusion density', 'is_ldpe': True},

            # --- HDPE (measured samples) ---
            # Note: densities clustering ~1.00-1.09 g/cm3 (vs ~0.92-0.95 for unfilled HDPE)
            {'name': 'HDPE brown', 'code': 'hdpe_brown', 'material_type': 'FILM', 'density': 0.942,
             'description': 'HDPE - Brown (single layer/color) - measured extrusion density'},
            {'name': 'HDPE coffee brown', 'code': 'hdpe_coffee_brown', 'material_type': 'FILM', 'density': 0.938,
             'description': 'HDPE - Coffee Brown (single layer/color) - measured extrusion density'},
            {'name': 'HDPE gray', 'code': 'hdpe_gray', 'material_type': 'FILM', 'density': 1.088,
             'description': 'HDPE - Gray, compounded with mineral filler (density well above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE pink', 'code': 'hdpe_pink', 'material_type': 'FILM', 'density': 0.938,
             'description': 'HDPE - Pink (single layer/color) - measured extrusion density'},
            {'name': 'HDPE purple', 'code': 'hdpe_purple', 'material_type': 'FILM', 'density': 0.9375,
             'description': 'HDPE - Purple (single layer/color) - measured extrusion density'},
            {'name': 'HDPE siege brown', 'code': 'hdpe_siege_brown', 'material_type': 'FILM', 'density': 1.088,
             'description': 'HDPE - Siege Brown, density suggests mineral filler content (unconfirmed) - measured extrusion density'},
            {'name': 'HDPE lemon green', 'code': 'hdpe_lemon_green', 'material_type': 'FILM', 'density': 0.944,
             'description': 'HDPE - Lemon Green (single layer/color) - measured extrusion density'},
            {'name': 'HDPE orange', 'code': 'hdpe_orange', 'material_type': 'FILM', 'density': 0.946,
             'description': 'HDPE - Orange (single layer/color) - measured extrusion density'},
            {'name': 'HDPE purple', 'code': 'hdpe_purple_2', 'material_type': 'FILM', 'density': 0.998,
             'description': 'HDPE - Purple, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE dark gray', 'code': 'hdpe_dark_gray', 'material_type': 'FILM', 'density': 0.948,
             'description': 'HDPE - Dark Gray (single layer/color) - measured extrusion density'},
            {'name': 'HDPE tint blue', 'code': 'hdpe_tint_blue', 'material_type': 'FILM', 'density': 1.002,
             'description': 'HDPE - light/translucent Blue tint, density suggests mineral filler content (unconfirmed) - measured extrusion density'},
            {'name': 'HDPE tint red', 'code': 'hdpe_tint_red', 'material_type': 'FILM', 'density': 1.005,
             'description': 'HDPE - light/translucent Red tint, density suggests mineral filler content (unconfirmed) - measured extrusion density'},
            {'name': 'HDPE', 'code': 'hdpe_base', 'material_type': 'FILM', 'density': 0.9268,
             'description': 'HDPE - clear/natural, base grade without mineral filler - measured extrusion density'},
            {'name': 'HDPE red', 'code': 'hdpe_red', 'material_type': 'FILM', 'density': 0.9471,
             'description': 'HDPE - Red (single layer/color) - measured extrusion density'},
            {'name': 'HDPE white', 'code': 'hdpe_white', 'material_type': 'FILM', 'density': 1.0285,
             'description': 'HDPE - White, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE clear', 'code': 'hdpe_clear', 'material_type': 'FILM', 'density': 1.0014,
             'description': 'HDPE - clear/natural, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE white', 'code': 'hdpe_white_2', 'material_type': 'FILM', 'density': 0.9539,
             'description': 'HDPE - White, without mineral filler - measured extrusion density'},
            {'name': 'HDPE blue', 'code': 'hdpe_blue', 'material_type': 'FILM', 'density': 1.037,
             'description': 'HDPE - Blue, density suggests mineral filler content (unconfirmed) - measured extrusion density'},
            {'name': 'HDPE black', 'code': 'hdpe_black', 'material_type': 'FILM', 'density': 1.005,
             'description': 'HDPE - Black, density suggests mineral filler content (unconfirmed) - measured extrusion density'},
            {'name': 'HDPE dark green', 'code': 'hdpe_dark_green', 'material_type': 'FILM', 'density': 0.9825,
             'description': 'HDPE - Dark Green (single layer/color) - measured extrusion density'},
            {'name': 'HDPE golden yello', 'code': 'hdpe_golden_yello', 'material_type': 'FILM', 'density': 0.9943,
             'description': 'HDPE - Golden Yellow (single layer/color) - measured extrusion density'},
            {'name': 'HDPE Blue', 'code': 'hdpe_blue_2', 'material_type': 'FILM', 'density': 0.9791,
             'description': 'HDPE - Blue, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE GOlden yellow - white', 'code': 'hdpe_golden_yellow_white', 'material_type': 'FILM', 'density': 0.9379,
             'description': 'HDPE two-layer film - Golden Yellow outside, White inside - measured extrusion density'},
            {'name': 'HDPE Dark green', 'code': 'hdpe_dark_green_2', 'material_type': 'FILM', 'density': 0.9884,
             'description': 'HDPE - Dark Green, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Pale green', 'code': 'hdpe_pale_green', 'material_type': 'FILM', 'density': 0.9855,
             'description': 'HDPE - Pale Green, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Pale green and Dark green', 'code': 'hdpe_pale_green_and_dark_green', 'material_type': 'FILM', 'density': 0.9859,
             'description': 'HDPE - mixed/mottled blend of Pale Green and Dark Green (not a layered structure), compounded with mineral filler - measured extrusion density'},
            {'name': 'HDPE Orange', 'code': 'hdpe_orange_2', 'material_type': 'FILM', 'density': 0.9804,
             'description': 'HDPE - Orange, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE TInt blue', 'code': 'hdpe_tint_blue_2', 'material_type': 'FILM', 'density': 0.9559,
             'description': 'HDPE - light/translucent Blue tint (single layer/color) - measured extrusion density'},
            {'name': 'HDPE TInt green', 'code': 'hdpe_tint_green', 'material_type': 'FILM', 'density': 0.9308,
             'description': 'HDPE - light/translucent Green tint (single layer/color) - measured extrusion density'},
            {'name': 'HDPE bLACK', 'code': 'hdpe_black_2', 'material_type': 'FILM', 'density': 0.9367,
             'description': 'HDPE - Black (single layer/color) - measured extrusion density'},
            {'name': 'HDPE TInt red', 'code': 'hdpe_tint_red_2', 'material_type': 'FILM', 'density': 0.9506,
             'description': 'HDPE - light/translucent Red tint (single layer/color) - measured extrusion density'},
            {'name': 'HDPE SKY BLUE', 'code': 'hdpe_sky_blue', 'material_type': 'FILM', 'density': 1.0223,
             'description': 'HDPE - Sky Blue, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Brown', 'code': 'hdpe_brown_2', 'material_type': 'FILM', 'density': 1.0223,
             'description': 'HDPE - Brown, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Tint Orange', 'code': 'hdpe_tint_orange', 'material_type': 'FILM', 'density': 1.0056,
             'description': 'HDPE - light/translucent Orange tint, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Tint yellow', 'code': 'hdpe_tint_yellow', 'material_type': 'FILM', 'density': 1.0015,
             'description': 'HDPE - light/translucent Yellow tint, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},
            {'name': 'HDPE Brown', 'code': 'hdpe_brown_3', 'material_type': 'FILM', 'density': 0.9909,
             'description': 'HDPE - Brown, compounded with mineral filler (density above unfilled HDPE) - measured extrusion density'},

            # --- NYLON (measured samples) ---
            {'name': 'NYLON white', 'code': 'nylon_white', 'material_type': 'FILM', 'density': 0.9529,
             'description': 'NYLON (Polyamide) film - White - measured extrusion density'},
            {'name': 'NYLON clear', 'code': 'nylon_clear', 'material_type': 'FILM', 'density': 0.9383,
             'description': 'NYLON (Polyamide) film - clear/natural - measured extrusion density'},

            # --- EVOH (measured samples) ---
            {'name': 'UHT/EVOH W/B', 'code': 'evoh_uht_w_b', 'material_type': 'FILM', 'density': 0.9691,
             'description': 'Multilayer barrier film for UHT (Ultra High Temperature/aseptic) packaging, incorporating an EVOH oxygen-barrier layer - White outside, Black inside - measured extrusion density'},
            {'name': 'PE/EVOH/PE-AF', 'code': 'evoh_pe_pe_af', 'material_type': 'FILM', 'density': 0.9552,
             'description': 'Three-layer barrier structure: PE outside / EVOH oxygen-barrier core / PE with Anti-Fog (AF) additive inside - measured extrusion density'},

            # --- PP (measured samples) ---
            {'name': 'pp', 'code': 'pp_base', 'material_type': 'FILM', 'density': 0.9061,
             'description': 'Polypropylene (PP) - general/natural grade - measured extrusion density'},

            # --- Lamination Components ---
            {'name': 'Ink', 'code': 'ink', 'material_type': 'INK', 'density': 1.100, 'description': 'Printing Ink'},
            {'name': 'Ethyl Acetate', 'code': 'ethyl_acetate', 'material_type': 'SOLVENT', 'density': 0.902,
             'description': 'Solvent'},
            {'name': 'Adhesive', 'code': 'adhesive', 'material_type': 'ADHESIVE', 'density': 1.050,
             'description': 'Lamination Adhesive'},
            {'name': 'Hardener', 'code': 'hardener', 'material_type': 'HARDENER', 'density': 1.150,
             'description': 'Adhesive Hardener'},
        ]

        for data in materials_data:
            material, created = PlasticMaterial.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {material.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated description: {material.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(materials_data)} materials processed.'
        ))
