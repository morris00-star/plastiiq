from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class SlittingCalculation(models.Model):
    CALCULATION_TYPES = [
        ('ROLL_MASS', 'Roll Mass from Diameter'),
        ('ROLL_DIAMETER', 'Roll Diameter from Mass'),
        ('SLITTING_TIME', 'Slitting Time'),
        ('PRODUCTION_EFFICIENCY', 'Production Efficiency'),
        ('PRODUCTION_RATE', 'Production Rate'),
        ('YIELD_CALCULATION', 'Yield Calculation'),
    ]

    calculation_type = models.CharField(max_length=30, choices=CALCULATION_TYPES)
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
        return f"{self.get_calculation_type_display()} - {self.material.name}"


class SlittingLayer(models.Model):
    calculation = models.ForeignKey(SlittingCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    thickness = models.FloatField()
    thickness_unit = models.CharField(max_length=10, default='micron')
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']
