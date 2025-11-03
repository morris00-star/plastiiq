from django.db import models


class UnitConversion(models.Model):
    UNIT_TYPES = [
        ('LENGTH', 'Length'),
        ('MASS', 'Mass'),
        ('THICKNESS', 'Thickness'),
        ('TIME', 'Time'),
    ]

    name = models.CharField(max_length=100)
    from_unit = models.CharField(max_length=50)
    to_unit = models.CharField(max_length=50)
    conversion_factor = models.FloatField()
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES)

    def __str__(self):
        return f"{self.from_unit} to {self.to_unit}"


class MaterialRoll(models.Model):
    material = models.ForeignKey('calculator.PlasticMaterial', on_delete=models.CASCADE)
    core_diameter = models.FloatField(help_text="Core diameter in mm")
    outer_diameter = models.FloatField(help_text="Outer diameter in mm")
    width = models.FloatField(help_text="Width in mm")
    thickness = models.FloatField(help_text="Thickness in microns")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.material.name} - {self.outer_diameter}mm"
    