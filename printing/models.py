from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class PrintingCalculation(models.Model):
    CALCULATION_TYPES = [
        ('FILM_MASS_LENGTH', 'Film Mass & Length'),
        ('INK_MASS', 'Ink Mass Needed'),
        ('MACHINE_SPEED', 'Machine Speed'),
        ('GSM_CALCULATION', 'GSM Calculation'),
        ('INK_MIXING', 'Ink Mixing'),
        ('PRODUCTION_TIME', 'Production Time'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
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
        return f"{self.get_calculation_type_display()} - {self.timestamp}"


class InkFormula(models.Model):
    INK_TYPES = [
        ('PRIMARY', 'Primary (CMYK)'),
        ('SECONDARY', 'Secondary'),
        ('TERTIARY', 'Tertiary'),
        ('SPOT', 'Spot Color'),
    ]

    name = models.CharField(max_length=100)
    ink_type = models.CharField(max_length=20, choices=INK_TYPES)
    base_color = models.CharField(max_length=50, blank=True)  # For secondary/tertiary mixing
    pigment_percentage = models.FloatField(default=0.0)
    binder_percentage = models.FloatField(default=0.0)
    additives_percentage = models.FloatField(default=0.0)
    solvent_percentage = models.FloatField(default=0.0)
    density_g_cm3 = models.FloatField(default=1.0)
    coverage_gsm = models.FloatField(default=1.0)  # GSM for 100% coverage
    created_at = models.DateTimeField(auto_now_add=True)

    def total_solids_percentage(self):
        return self.pigment_percentage + self.binder_percentage + self.additives_percentage

    def color_strength(self):
        total_solids = self.total_solids_percentage()
        return (self.pigment_percentage / total_solids * 100) if total_solids > 0 else 0

    def __str__(self):
        return f"{self.name} ({self.get_ink_type_display()})"
