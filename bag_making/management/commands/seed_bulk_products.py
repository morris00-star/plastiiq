from django.core.management.base import BaseCommand
from bag_making.models import BulkProduct


class Command(BaseCommand):
    help = 'Seed/update BulkProduct bulk-density lookup for the Bag Capacity calculator. Safe to re-run.'

    def handle(self, *args, **kwargs):
        products = [
            dict(name='Maize/Corn', category='Grains & Cereals', density_min_kg_m3=720, density_max_kg_m3=770, density_typical_kg_m3=745),
            dict(name='Wheat', category='Grains & Cereals', density_min_kg_m3=770, density_max_kg_m3=840, density_typical_kg_m3=805),
            dict(name='Sorghum / Millet', category='Grains & Cereals', density_min_kg_m3=700, density_max_kg_m3=770, density_typical_kg_m3=735),
            dict(name='Beans / Legumes', category='Grains & Cereals', density_min_kg_m3=750, density_max_kg_m3=850, density_typical_kg_m3=800),
            dict(name='Rice', category='Grains & Cereals', density_min_kg_m3=750, density_max_kg_m3=880, density_typical_kg_m3=815,
                 notes='UNCONFIRMED - no specific range was provided, using a commonly-cited estimate for milled rice. Please verify.'),
            dict(name='Flour', category='Powders', density_min_kg_m3=450, density_max_kg_m3=650, density_typical_kg_m3=550),
            dict(name='Sugar', category='Powders', density_min_kg_m3=800, density_max_kg_m3=900, density_typical_kg_m3=850),
            dict(name='Cement', category='Powders', density_min_kg_m3=1200, density_max_kg_m3=1500, density_typical_kg_m3=1350,
                 notes='Bags run much smaller for the same weight - woven/laminated PP more common for this product'),
            dict(name='Powdered Milk', category='Powders', density_min_kg_m3=450, density_max_kg_m3=550, density_typical_kg_m3=500,
                 notes='UNCONFIRMED - no specific range was provided, using a commonly-cited estimate. Please verify.'),
            dict(name='Maize Flour (Posho)', category='Powders', density_min_kg_m3=500, density_max_kg_m3=600, density_typical_kg_m3=550,
                 notes='UNCONFIRMED - no specific range was provided, using a commonly-cited estimate. Please verify.'),
            dict(name='Granular Fertilizer', category='Fertilizers & Chemicals', density_min_kg_m3=900, density_max_kg_m3=1100, density_typical_kg_m3=1000),
            dict(name='Salt', category='Fertilizers & Chemicals', density_min_kg_m3=950, density_max_kg_m3=1150, density_typical_kg_m3=1050),
            dict(name='Charcoal / Briquettes', category='Other', density_min_kg_m3=250, density_max_kg_m3=400, density_typical_kg_m3=325,
                 notes='Loose fill - much bulkier per kg than most products'),
            dict(name='Animal Feed Pellets', category='Other', density_min_kg_m3=600, density_max_kg_m3=700, density_typical_kg_m3=650),
        ]

        for p in products:
            obj, created = BulkProduct.objects.get_or_create(name=p['name'], defaults=p)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name} ({obj.density_typical_kg_m3} kg/m3)"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists (unchanged): {obj.name}"))
