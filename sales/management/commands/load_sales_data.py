from django.core.management.base import BaseCommand
from sales.models import LaminatedFilm
import json


class Command(BaseCommand):
    help = 'Load initial laminated film data'

    def handle(self, *args, **kwargs):
        laminated_films = [
            {
                'name': 'BOPP-PET Laminate',
                'description': 'Common packaging laminate for snacks',
                'layers': [
                    {'material': 'BOPP', 'thickness_microns': 20, 'density': 0.905},
                    {'material': 'PET', 'thickness_microns': 12, 'density': 1.365}
                ],
                'total_thickness_microns': 32,
                'composite_density': 1.035
            },
            {
                'name': 'PE-Nylon Laminate',
                'description': 'Flexible packaging for liquids',
                'layers': [
                    {'material': 'LDPE', 'thickness_microns': 40, 'density': 0.925},
                    {'material': 'NYLON', 'thickness_microns': 15, 'density': 1.145}
                ],
                'total_thickness_microns': 55,
                'composite_density': 0.985
            },
        ]

        for film_data in laminated_films:
            film, created = LaminatedFilm.objects.get_or_create(
                name=film_data['name'],
                defaults={
                    'description': film_data['description'],
                    'layers': film_data['layers'],
                    'total_thickness_microns': film_data['total_thickness_microns'],
                    'composite_density': film_data['composite_density']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {film.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {film.name}'))
