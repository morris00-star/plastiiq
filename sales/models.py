from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


class SalesCalculation(models.Model):
    CALCULATION_TYPES = [
        ('MATERIAL_COST_KG', 'Material Cost per kg'),
        ('MATERIAL_COST_METER', 'Material Cost per meter'),
        ('MATERIAL_COST_PIECE', 'Material Cost per piece'),
        ('ORDER_QUANTITY_KG', 'Order Quantity from kg'),
        ('ORDER_QUANTITY_METER', 'Order Quantity from meters'),
        ('ORDER_QUANTITY_PIECE', 'Order Quantity from pieces'),
        ('ROLL_COST', 'Roll Cost Calculation'),
        ('LAMINATED_COST', 'Laminated Material Cost'),
    ]

    calculation_type = models.CharField(max_length=25, choices=CALCULATION_TYPES)
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


class LaminatedStructure(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layers = models.JSONField()  # Store layer materials and percentages
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
