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
        ('MARGIN_MARKUP', 'Margin / Markup / Selling Price'),
        ('COST_PER_SQM', 'Cost per Square Meter'),
        ('BREAKEVEN_QTY', 'Breakeven Quantity'),
        ('VAT_CALCULATION', 'VAT Inclusive/Exclusive'),
        ('BULK_DISCOUNT', 'Bulk/Quantity-Break Discount'),
    ]

    calculation_type = models.CharField(max_length=25, choices=CALCULATION_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=150, blank=True)
    order_name = models.CharField(max_length=150, blank=True)
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


class SalesCalculationLayer(models.Model):
    """Real per-layer cost data for laminate costing - fixes the old flat single-cost bug."""
    calculation = models.ForeignKey(SalesCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    cost_per_kg = models.FloatField()
    weight_kg = models.FloatField()
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']


class LaminatedStructure(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layers = models.JSONField()  # Store layer materials and percentages
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
