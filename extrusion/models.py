from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings

MACHINE_CHOICES = (
        [(f'RAJOO_{n:02d}', f'Rajoo {n:02d}') for n in range(1, 4)] +
        [(f'MAMATA_{n:02d}', f'Mamata {n:02d}') for n in range(1, 3)] +
        [('WINDSOR', 'Windsor')] +
        [('JINMING', 'Jinming')] +
        [(f'PP_{n:02d}', f'PP {n:02d}') for n in range(1, 3)] +
        [(f'TAIWAN_{n:02d}', f'Taiwan {n:02d}') for n in range(1, 7)] +
        [(f'HEMINGSTON_{n:02d}', f'Hemingston {n:02d}') for n in range(1, 5)] +
        [(f'GURUCHARANI_{n:02d}', f'Gurucharani {n:02d}') for n in range(1, 4)] +
        [(f'CHINA_{n:02d}', f'China {n:02d}') for n in range(1, 4)] +
        [('CONCORD', 'Concord')] +
        [('SHOWMAN', 'Showman')]
)


class ExtrusionCalculation(models.Model):
    CALCULATION_TYPES = [
        ('PIECES_WEIGHT', 'Pieces to Weight'),
        ('THICKNESS', 'Thickness Calculation'),
        ('TAKEUP_SPEED', 'Take-up Speed Adjustment'),
        ('ROLL_RADIUS', 'Roll Radius/Mass'),
        ('ROLL_RADIUS_FROM_MASS', 'Roll Radius from Mass'),
        ('FILM_LENGTH', 'Film Length from Weight'),
        ('WEIGHT_FROM_LENGTH', 'Weight from Length'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('BUR_DDR', 'Blown Film Ratios'),
        ('TENSILE', 'Tensile Strength'),
        ('ELONGATION', 'Percent Elongation'),
        ('COF', 'Coefficient of Friction'),
        ('DART_IMPACT', 'Dart Impact'),
        ('GAUGE_VARIATION', 'Gauge Variation'),
        ('COMPOSITE_DENSITY', 'Composite Density'),
        ('YIELD_BASIS', 'Yield & Basis Weight'),
        ('LAYER_DISTRIBUTION_3', '3-Layer Distribution'),
        ('LAYER_DISTRIBUTION_5', '5-Layer Distribution'),
        ('MASTERBATCH_DOSING', 'Masterbatch Dosing'),
        ('REGRIND_BLEND', 'Regrind/Recycled Blend'),
        ('SPECIFIC_OUTPUT', 'Specific Output Rate'),
        ('NECK_IN_DRAW', 'Neck-in / Draw Ratio'),
        ('PUNCTURE_ENERGY', 'Puncture Resistance / Impact Energy'),
        ('SECANT_MODULUS', 'Secant Modulus'),
        ('WASTE_PERCENT', 'Scrap/Waste Percentage'),
        ('BARRIER_NORMALIZATION', 'Barrier Property Normalization'),
    ]

    calculation_type = models.CharField(max_length=25, choices=CALCULATION_TYPES)
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

    # Added machine-related fields
    machine_name = models.CharField(max_length=20, choices=MACHINE_CHOICES, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    order_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_calculation_type_display()} - {self.material.name}"


class ThicknessMeasurement(models.Model):
    calculation = models.ForeignKey(ExtrusionCalculation, on_delete=models.CASCADE,
                                    related_name='thickness_measurements')
    position = models.CharField(max_length=50)
    thickness = models.FloatField()
    measurement_order = models.IntegerField()

    class Meta:
        ordering = ['measurement_order']
