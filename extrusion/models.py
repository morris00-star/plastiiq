from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class ExtrusionCalculation(models.Model):
    CALCULATION_TYPES = [
        ('PIECES_WEIGHT', 'Pieces to Weight'),
        ('THICKNESS', 'Thickness Calculation'),
        ('TAKEUP_SPEED', 'Take-up Speed Adjustment'),
        ('ROLL_RADIUS', 'Roll Radius/Mass'),
        ('FILM_LENGTH', 'Film Length from Weight'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('BUR_DDR', 'Blown Film Ratios'),
        ('TENSILE', 'Tensile Strength'),
        ('ELONGATION', 'Percent Elongation'),
        ('COF', 'Coefficient of Friction'),
        ('DART_IMPACT', 'Dart Impact'),
        ('GAUGE_VARIATION', 'Gauge Variation'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    input_data = models.JSONField()  # Store all input parameters
    result_data = models.JSONField()  # Store all results
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.get_calculation_type_display()} - {self.material.name}"


class ThicknessMeasurement(models.Model):
    calculation = models.ForeignKey(ExtrusionCalculation, on_delete=models.CASCADE,
                                    related_name='thickness_measurements')
    position = models.CharField(max_length=50)
    thickness_microns = models.FloatField()
    measurement_order = models.IntegerField()

    class Meta:
        ordering = ['measurement_order']

