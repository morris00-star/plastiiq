from django.core.management.base import BaseCommand
from bag_making.models import BagType


class Command(BaseCommand):
    help = 'Load initial bag type data'

    def handle(self, *args, **kwargs):
        bag_types = [
            {'name': 'Side Seal Bag', 'code': 'SIDE_SEAL', 'style': 'SIDE_SEAL', 'waste_percentage': 5.0,
             'description': 'Standard side seal plastic bag'},
            {'name': 'Bottom Seal Bag', 'code': 'BOTTOM_SEAL', 'style': 'BOTTOM_SEAL', 'waste_percentage': 6.0,
             'description': 'Bottom seal bag with reinforced base'},
            {'name': 'Pillow Bag', 'code': 'PILLOW', 'style': 'PILLOW', 'waste_percentage': 4.5,
             'description': 'Pillow style bag with side seals'},
            {'name': 'Gusset Bag', 'code': 'GUSSET', 'style': 'GUSSET', 'waste_percentage': 7.0,
             'description': 'Bag with side gussets for expansion'},
            {'name': 'Wicket Bag', 'code': 'WICKET', 'style': 'WICKET', 'waste_percentage': 8.0,
             'description': 'Bag with wicket holes for packaging machines'},
            {'name': 'Stand-up Bag', 'code': 'STANDBAG', 'style': 'STANDBAG', 'waste_percentage': 10.0,
             'description': 'Self-standing bag with bottom gusset'},
            {'name': 'Zipper Bag', 'code': 'ZIPPER', 'style': 'ZIPPER', 'waste_percentage': 12.0,
             'description': 'Reclosable bag with zipper track'},
        ]

        for bag_data in bag_types:
            bag_type, created = BagType.objects.get_or_create(
                code=bag_data['code'],
                defaults=bag_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {bag_type.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {bag_type.name}'))
