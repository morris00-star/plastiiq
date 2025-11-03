from django.db import models
from django.conf import settings


class DensityCalculation(models.Model):
    material = models.ForeignKey('PlasticMaterial', on_delete=models.CASCADE)
    mass = models.FloatField(help_text="Mass in grams")
    volume = models.FloatField(help_text="Volume in cm³")
    calculated_density = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.material.name} - {self.calculated_density} g/cm³"


class PlasticMaterial(models.Model):
    MATERIAL_TYPES = [
        ('FILM', 'Plastic Film'),
        ('INK', 'Ink'),
        ('SOLVENT', 'Solvent'),
        ('ADHESIVE', 'Adhesive'),
        ('HARDENER', 'Hardener'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES)
    density = models.FloatField(help_text="Density in g/cm³")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code}) - Density: {self.density} g/cm³"
