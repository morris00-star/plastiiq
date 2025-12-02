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
    core_weight_source = models.CharField(max_length=20, blank=True, null=True)
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


class CoreMaterial(models.Model):
    """Model to store different core material properties"""
    name = models.CharField(max_length=100)
    material_type = models.CharField(max_length=50)  # e.g., 'Paper', 'Plastic', 'Steel'
    density = models.FloatField(help_text="Density in g/cm³")
    wall_thickness_mm = models.FloatField(default=1.5, help_text="Typical wall thickness in mm")
    color = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.material_type}) - {self.density}g/cm³"

