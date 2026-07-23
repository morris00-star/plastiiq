from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class BagMakingCalculation(models.Model):
    BAG_TYPES = [
        ('FLAT_SHEET', 'Flat Sheet Bag'),
        ('TUBULAR', 'Tubular Bag'),
        ('GUSSETED_SIDE', 'Side Gusseted Bag'),
        ('GUSSETED_BOTTOM', 'Bottom Gusseted Bag'),
        ('TUBULAR_WITH_FLAP', 'Tubular Bag with Flap'),
        ('LAMINATED_FLAT', 'Laminated Flat Bag'),
        ('LAMINATED_TUBULAR', 'Laminated Tubular Bag'),
        ('LAMINATED_GUSSETED_SIDE', 'Laminated Side Gusseted Bag'),
        ('LAMINATED_GUSSETED_BOTTOM', 'Laminated Bottom Gusseted Bag'),
        ('LAMINATED_TUBULAR_FLAP', 'Laminated Tubular with Flap'),
    ]

    CALCULATION_TYPES = [
        ('PIECES_WEIGHT', 'Pieces ↔ Weight'),
        ('PACKET_WEIGHT', 'Packet Weight'),
        ('BUNDLE_WEIGHT', 'Bundle/Bale Weight'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('YIELD_EFFICIENCY', 'Yield & Efficiency'),
    ]

    ADDON_TYPES = [
        ('NONE', 'No Add-ons'),
        ('ZIPPER', 'Zipper Only'),
        ('HANDLES', 'Handles Only'),
        ('BOTH', 'Zipper and Handles'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
    bag_type = models.CharField(max_length=30, choices=BAG_TYPES)
    addon_type = models.CharField(max_length=10, choices=ADDON_TYPES, default='NONE')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE, null=True, blank=True)
    input_data = models.JSONField()
    result_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        addon = f" + {self.get_addon_type_display()}" if self.addon_type != 'NONE' else ""
        return f"{self.get_calculation_type_display()} - {self.get_bag_type_display()}{addon}"


class BagLayer(models.Model):
    calculation = models.ForeignKey(BagMakingCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    thickness = models.FloatField()
    thickness_unit = models.CharField(max_length=10, default='micron')
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']


class AddonComponent(models.Model):
    ADDON_TYPES = [
        ('ZIPPER', 'Zipper'),
        ('HANDLE', 'Handle'),
    ]

    calculation = models.ForeignKey(BagMakingCalculation, on_delete=models.CASCADE, related_name='addons')
    addon_type = models.CharField(max_length=10, choices=ADDON_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    weight_per_piece = models.FloatField(help_text="Weight in grams per piece")
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_addon_type_display()} - {self.weight_per_piece}g"
