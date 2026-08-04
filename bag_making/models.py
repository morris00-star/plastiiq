from django.db import models
from calculator.models import PlasticMaterial
from qc_project import settings


MACHINE_CHOICES = (
    [(f'SIDE_SEAL_{n:02d}', f'Side Seal {n:02d}') for n in range(1, 38)] +
    [(f'BOTTOM_SEAL_{n:02d}', f'Bottom Seal {n:02d}') for n in range(1, 20)] +
    [(f'POUCH_{n:02d}', f'Pouch {n:02d}') for n in range(1, 7)] +
    [(f'FOLDER_{n:02d}', f'Folder {n:02d}') for n in range(1, 4)] +
    [(f'VEST_BAG_{n:02d}', f'Vest Bag {n:02d}') for n in range(1, 7)] +
    [(f'SPOUT_{n:02d}', f'Spout {n:02d}') for n in range(1, 3)] +
    [(f'BREATHER_VENT_{n:02d}', f'Breather/Vent {n:02d}') for n in range(1, 3)]
)

class CutoutGeometry(models.Model):
    """
    Persisted die-geometry calibration data for cut-outs (D Punch, Vest Bag, etc.).
    Area is measured once from a physical sample and stored permanently against the
    die shape - it does NOT change with material or thickness, only if the physical
    die itself changes. K is derived on the fly from area x current density x layers,
    never stored, so it always reflects whatever material/thickness a calculation uses.

    Free-text geometry_type (not a fixed choices list) so new die shapes can be added
    without a migration - just create a new row.
    """
    name = models.CharField(max_length=100, help_text='e.g. "D Punch (30mm x 75mm)"')
    geometry_type = models.CharField(
        max_length=50,
        help_text='Free-text category tag, e.g. "D_PUNCH" or "VEST_BAG" - used for grouping/filtering in the UI'
    )
    calibration_material = models.CharField(max_length=100, help_text="Material used when this geometry was calibrated")
    density_g_cm3 = models.FloatField(help_text="Density (rho) used at calibration - editable if confirmed later")
    layers = models.IntegerField(default=2, help_text="Number of film layers (L) - normally 2")
    area_cm2 = models.FloatField(help_text="Stored, reusable effective area (A) - back-calculated once, then fixed")
    calibration_thickness_um = models.FloatField(null=True, blank=True, help_text="Thickness used for the calibration sample, for reference")
    calibration_mass_g = models.FloatField(null=True, blank=True, help_text="Measured sample mass used for the back-calculation, for reference")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['geometry_type', 'name']

    def calculate_k(self, density_g_cm3=None, layers=None):
        """K = (rho x A x L) / 10000, using the stored Area but whatever density/layers are passed in."""
        rho = density_g_cm3 if density_g_cm3 is not None else self.density_g_cm3
        l = layers if layers is not None else self.layers
        return (rho * self.area_cm2 * l) / 10000

    def __str__(self):
        return f"{self.name} (A={self.area_cm2} cm2)"


class BulkProduct(models.Model):
    """
    Extensible bulk-density lookup for the Bag Fill Volume/Capacity calculator.
    Stores the full min/max range (not just a single number) so the calculator
    can show the range and let the user pick or override with a custom value.
    """
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        help_text='e.g. "Grains & Cereals", "Powders", "Fertilizers & Chemicals", "Other"'
    )
    density_min_kg_m3 = models.FloatField()
    density_max_kg_m3 = models.FloatField()
    density_typical_kg_m3 = models.FloatField(help_text="Midpoint of min/max - used as the default")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.density_typical_kg_m3} kg/m3)"


class BagMakingCalculation(models.Model):
    BAG_TYPES = [
        ('FLAT_SHEET', 'Flat Sheet Bag'),
        ('TUBULAR', 'Tubular Bag'),
        ('GUSSETED_SIDE', 'Side Gusseted Bag'),
        ('GUSSETED_BOTTOM', 'Bottom Gusseted Bag'),
        ('TUBULAR_WITH_FLAP', 'Tubular Bag with Flap'),
        ('LAMINATED_FLAT', 'Laminated Flat Bag'),
        ('LAMINATED_TUBULAR', 'Laminated Tubular Bag'),
        ('LAMINATED_GUSSETED_SIDE', 'Laminated Side Gusseted Bag'),
        ('LAMINATED_GUSSETED_BOTTOM', 'Laminated Bottom Gusseted Bag'),
        ('LAMINATED_TUBULAR_FLAP', 'Laminated Tubular with Flap'),
        ('GUSSETED_BOTTOM_FLAP', 'Bottom Gusseted Bag with Flap'),
        ('LAMINATED_GUSSETED_BOTTOM_FLAP', 'Laminated Bottom Gusseted with Flap'),
    ]

    CALCULATION_TYPES = [
        ('PIECES_WEIGHT', 'Pieces ↔ Weight'),
        ('PACKET_WEIGHT', 'Packet Weight'),
        ('BUNDLE_WEIGHT', 'Bundle/Bale Weight'),
        ('PRODUCTION_TIME', 'Production Time'),
        ('YIELD_EFFICIENCY', 'Yield & Efficiency'),
        ('BAG_CAPACITY', 'Bag Fill Volume/Capacity'),
        ('ROLL_REQUIREMENT', 'Bags per Roll / Roll Requirement'),
        ('SEAL_STRENGTH', 'Heat Seal Strength'),
    ]

    ADDON_TYPES = [
        ('NONE', 'No Add-ons'),
        ('ZIPPER', 'Zipper Only'),
        ('HANDLES', 'Handles Only'),
        ('BOTH', 'Zipper and Handles'),
    ]

    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES)
    bag_type = models.CharField(max_length=30, choices=BAG_TYPES)
    addon_type = models.CharField(max_length=10, choices=ADDON_TYPES, default='NONE')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE, null=True, blank=True)
    machine_name = models.CharField(max_length=20, choices=MACHINE_CHOICES, blank=True, null=True)
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
        addon = f" + {self.get_addon_type_display()}" if self.addon_type != 'NONE' else ""
        return f"{self.get_calculation_type_display()} - {self.get_bag_type_display()}{addon}"


class BagLayer(models.Model):
    calculation = models.ForeignKey(BagMakingCalculation, on_delete=models.CASCADE, related_name='layers')
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    thickness = models.FloatField()
    thickness_unit = models.CharField(max_length=10, default='micron')
    layer_order = models.IntegerField()

    class Meta:
        ordering = ['layer_order']


class AddonComponent(models.Model):
    ADDON_TYPES = [
        ('ZIPPER', 'Zipper'),
        ('HANDLE', 'Handle'),
    ]

    calculation = models.ForeignKey(BagMakingCalculation, on_delete=models.CASCADE, related_name='addons')
    addon_type = models.CharField(max_length=10, choices=ADDON_TYPES)
    material = models.ForeignKey(PlasticMaterial, on_delete=models.CASCADE)
    weight_per_piece = models.FloatField(help_text="Weight in grams per piece")
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_addon_type_display()} - {self.weight_per_piece}g"
