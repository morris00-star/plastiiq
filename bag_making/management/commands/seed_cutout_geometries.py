from django.core.management.base import BaseCommand
from bag_making.models import CutoutGeometry


class Command(BaseCommand):
    help = 'Seed/update CutoutGeometry dies (D Punch and Vest Bag). Safe to re-run.'

    def handle(self, *args, **kwargs):
        geometries = [
            dict(name='D Punch (30mm x 75mm)', geometry_type='D_PUNCH', calibration_material='PET/LDPE laminate',
                 density_g_cm3=1.05, layers=2, area_cm2=18.51, calibration_thickness_um=150, calibration_mass_g=0.583,
                 notes='Calibration: n=3, measured avg mass 0.583g'),
            dict(name='D Punch (20mm x 90mm)', geometry_type='D_PUNCH', calibration_material='LDPE',
                 density_g_cm3=0.92, layers=2, area_cm2=16.80, calibration_thickness_um=55, calibration_mass_g=0.170,
                 notes='Calibration: n=10, measured avg mass 0.170g'),
            dict(name='D Punch (23mm x 90mm)', geometry_type='D_PUNCH', calibration_material='LDPE - P/W',
                 density_g_cm3=0.93, layers=2, area_cm2=20.67, calibration_thickness_um=65, calibration_mass_g=0.250,
                 notes='Calibration: n=4, measured avg mass 0.250g'),
            dict(name='D Punch (28mm x 80mm)', geometry_type='D_PUNCH', calibration_material='LDPE - Tint Blue',
                 density_g_cm3=0.92, layers=2, area_cm2=20.85, calibration_thickness_um=73, calibration_mass_g=0.280,
                 notes='Calibration: n=5, measured avg mass 0.280g'),
            dict(name='D Punch (17mm x 65mm)', geometry_type='D_PUNCH', calibration_material='BOPP',
                 density_g_cm3=0.905, layers=2, area_cm2=16.39, calibration_thickness_um=30, calibration_mass_g=0.089,
                 notes='Calibration: weighted avg of 3 groups - 0.09g (n=5), 0.08g (n=3), 0.10g (n=2) = 0.089g weighted mean. Assumed L=2 layers (not explicitly specified).'),
            dict(name='Small Vest (145mm x 110mm)', geometry_type='VEST_BAG', calibration_material='HD-W/O',
                 density_g_cm3=1.05, layers=2, area_cm2=155.1, calibration_thickness_um=30, calibration_mass_g=0.977,
                 notes='Calibration: n=15, measured avg mass 0.977g'),
            dict(name='Medium Vest (180mm x 130mm)', geometry_type='VEST_BAG', calibration_material='HD-W/O',
                 density_g_cm3=1.05, layers=2, area_cm2=269.7, calibration_thickness_um=30, calibration_mass_g=1.699,
                 notes='Calibration: n=9, measured avg mass 1.699g'),
            dict(name='Large Vest (390mm x 140mm)', geometry_type='VEST_BAG', calibration_material='HD-B/O (Blue)',
                 density_g_cm3=1.05, layers=2, area_cm2=479.2, calibration_thickness_um=30, calibration_mass_g=3.019,
                 notes='Calibration: n=8, measured avg mass 3.019g'),
        ]

        for g in geometries:
            obj, created = CutoutGeometry.objects.get_or_create(name=g['name'], defaults=g)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name} (A={obj.area_cm2} cm2, K={obj.calculate_k():.6f} g/um)"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists (unchanged): {obj.name}"))
