from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class BagMakingCalculation(models.Model):
    BAG_TYPES = [
        ('FLAT_SHEET', 'Flat Sheet Bag'),
        ('TUBULAR', 'Tubular Bag'),
        ('GUSSETED', 'Gusseted Bag'),
        ('LAMINATED_FLAT', 'Laminated Flat Bag'),
        ('LAMINATED_TUBULAR', 'Laminated Tubular Bag'),
        ('LAMINATED_GUSSETED', 'Laminated Gusseted Bag'),
    ]

    CALCULATION_TYPES = [
        ('PIECES_WEIGHT', 'Pieces ↔ Weight'),
        ('PACKET_WEIGHT', 'Packet Weight'),
        ('BUNDLE_WEIGHT', 'Bundle/Bale Weight'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('YIELD_EFFICIENCY', 'Yield & Efficiency'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
    bag_type = models.CharField(max_length=20, choices=BAG_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
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
        return f"{self.get_calculation_type_display()} - {self.get_bag_type_display()}"


class BagLayer(models.Model):
    calculation = models.ForeignKey(BagMakingCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    thickness = models.FloatField()
    thickness_unit = models.CharField(max_length=10, default='micron')
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']
