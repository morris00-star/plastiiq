from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class LaminationCalculation(models.Model):
    ADHESIVE_TYPES = [
        ('SOLVENTLESS', 'Solventless'),
        ('SOLVENT_BASE', 'Solvent Base'),
    ]

    calculation_type = models.CharField(max_length=50)
    adhesive_type = models.CharField(max_length=20, choices=ADHESIVE_TYPES)
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
        return f"{self.calculation_type} - {self.adhesive_type}"


class LaminationLayer(models.Model):
    calculation = models.ForeignKey(LaminationCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    thickness = models.FloatField()
    thickness_unit = models.CharField(max_length=10, default='micron')
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']
