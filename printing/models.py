from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


MACHINE_CHOICES = (
    [(f'FLEXO_F{n:02d}', f'Flexo F{n:02d}') for n in range(1, 10)] +
    [(f'BFM_{n}', f'BFM {n}') for n in range(1, 4)] +
    [(f'ROTO_{n}', f'ROTO {n}') for n in range(1, 7)]
)


class PrintingCalculation(models.Model):
    CALCULATION_TYPES = [
        ('FILM_MASS_LENGTH', 'Film Mass & Length'),
        ('INK_MASS', 'Ink Mass Needed'),
        ('MACHINE_SPEED', 'Machine Speed'),
        ('GSM_CALCULATION', 'GSM Calculation'),
        ('INK_MIXING', 'Ink Mixing'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('ANILOX_COVERAGE', 'Anilox Ink Coverage'),
        ('DOT_GAIN_CONTRAST', 'Dot Gain / Print Contrast'),
        ('DELTA_E', 'Color Difference (Delta E)'),
        ('REGISTRATION_REPEAT', 'Registration / Repeat Length'),
        ('RESIDUAL_SOLVENT', 'Residual Solvent'),
        ('WASTE_ALLOWANCE', 'Waste Allowance Planning'),
        ('MAX_SAFE_SPEED', 'Max Safe Speed vs Drying'),
        ('CYLINDER_COVERAGE', 'Cylinder Coverage & Ink Consumption'),
        ('CYLINDER_WEAR_LIFE', 'Cylinder Wear & Life Planning'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE, null=True, blank=True)
    machine_name = models.CharField(max_length=20, choices=MACHINE_CHOICES, blank=True)
    customer_name = models.CharField(max_length=150, blank=True)
    job_name = models.CharField(max_length=150, blank=True)
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
