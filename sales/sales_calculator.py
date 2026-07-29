class SalesCalculator:
    """
    Sales pricing and quantity calculations for plastic products.
    Default currency: UGX (Ugandan Shillings)
    """

    def __init__(self, currency='UGX'):
        self.currency = currency

    # --- MATERIAL COST PER UNIT ---

    def calculate_material_cost_per_kg(self, total_material_cost, output_mass_kg):
        """
        Calculates the raw material cost component for a product sold by mass (kilograms).
        Formula: Cost_per_kg = Total_Material_Cost / Output_Mass_kg
        """
        if output_mass_kg <= 0:
            return 0.0

        cost_per_kg = total_material_cost / output_mass_kg
        return cost_per_kg

    def calculate_material_cost_per_meter(self, total_material_cost, output_length_m):
        """
        Calculates the raw material cost component for a product sold by length (meters).
        Formula: Cost_per_meter = Total_Material_Cost / Output_Length_m
        """
        if output_length_m <= 0:
            return 0.0

        cost_per_meter = total_material_cost / output_length_m
        return cost_per_meter

    def calculate_material_cost_per_piece(self, total_material_cost, output_pieces):
        """
        Calculates the raw material cost component for a product sold by count (pieces, bags, or pouches).
        Formula: Cost_per_Piece = Total_Material_Cost / Output_Pieces
        """
        if output_pieces <= 0:
            return 0.0

        cost_per_piece = total_material_cost / output_pieces
        return cost_per_piece

    # --- BIDIRECTIONAL ORDER QUANTITY CALCULATIONS ---

    def calculate_order_quantity_from_kg(self, cost_per_kg, total_budget):
        """
        Calculate how many kg can be purchased with a given budget.
        Formula: Quantity_kg = Total_Budget / Cost_per_kg
        """
        if cost_per_kg <= 0:
            return 0.0

        quantity_kg = total_budget / cost_per_kg
        return quantity_kg

    def calculate_total_cost_from_kg(self, cost_per_kg, quantity_kg):
        """
        Calculate total cost for a given quantity in kg.
        Formula: Total_Cost = Cost_per_kg × Quantity_kg
        """
        total_cost = cost_per_kg * quantity_kg
        return total_cost

    def calculate_order_quantity_from_meters(self, cost_per_meter, total_budget):
        """
        Calculate how many meters can be purchased with a given budget.
        Formula: Quantity_meters = Total_Budget / Cost_per_meter
        """
        if cost_per_meter <= 0:
            return 0.0

        quantity_meters = total_budget / cost_per_meter
        return quantity_meters

    def calculate_total_cost_from_meters(self, cost_per_meter, quantity_meters):
        """
        Calculate total cost for a given quantity in meters.
        Formula: Total_Cost = Cost_per_meter × Quantity_meters
        """
        total_cost = cost_per_meter * quantity_meters
        return total_cost

    def calculate_order_quantity_from_pieces(self, cost_per_piece, total_budget):
        """
        Calculate how many pieces can be purchased with a given budget.
        Formula: Quantity_pieces = Total_Budget / Cost_per_piece
        """
        if cost_per_piece <= 0:
            return 0.0

        quantity_pieces = total_budget / cost_per_piece
        return quantity_pieces

    def calculate_total_cost_from_pieces(self, cost_per_piece, quantity_pieces):
        """
        Calculate total cost for a given quantity in pieces.
        Formula: Total_Cost = Cost_per_piece × Quantity_pieces
        """
        total_cost = cost_per_piece * quantity_pieces
        return total_cost

    # --- ROLL COST CALCULATIONS ---

    def calculate_roll_cost_per_kg(self, roll_cost, roll_weight_kg):
        """
        Calculate cost per kg for a roll.
        Formula: Cost_per_kg = Roll_Cost / Roll_Weight_kg
        """
        if roll_weight_kg <= 0:
            return 0.0

        cost_per_kg = roll_cost / roll_weight_kg
        return cost_per_kg

    def calculate_roll_cost_from_kg(self, cost_per_kg, roll_weight_kg):
        """
        Calculate total roll cost from cost per kg.
        Formula: Roll_Cost = Cost_per_kg × Roll_Weight_kg
        """
        roll_cost = cost_per_kg * roll_weight_kg
        return roll_cost

    # --- LAMINATED MATERIAL COST ---

    def calculate_laminated_cost_per_kg(self, layer_costs, total_weight_kg):
        """
        Calculate cost per kg for laminated material.
        Formula: Cost_per_kg = Total_Layer_Costs / Total_Weight_kg
        """
        if total_weight_kg <= 0:
            return 0.0

        total_layer_costs = sum(layer_costs)
        cost_per_kg = total_layer_costs / total_weight_kg
        return cost_per_kg

    def calculate_laminated_total_cost(self, layer_costs):
        """
        Calculate total cost for laminated material.
        Formula: Total_Cost = Sum of all layer costs
        """
        return sum(layer_costs)

    # --- LAMINATE PER-LAYER COST (fixes the flat single-cost bug) ---

    def calculate_layer_cost(self, cost_per_kg, weight_kg):
        """Layer Cost = Cost per kg x Weight kg (per individual laminate layer)"""
        return cost_per_kg * weight_kg

    # --- MARGIN / MARKUP / SELLING PRICE ---

    @staticmethod
    def calculate_markup_percent(cost_price, selling_price):
        """Markup% = ((Selling Price - Cost Price) / Cost Price) * 100"""
        if cost_price <= 0:
            return 0.0
        return ((selling_price - cost_price) / cost_price) * 100

    @staticmethod
    def calculate_margin_percent(cost_price, selling_price):
        """Margin% = ((Selling Price - Cost Price) / Selling Price) * 100"""
        if selling_price <= 0:
            return 0.0
        return ((selling_price - cost_price) / selling_price) * 100

    @staticmethod
    def calculate_selling_price_from_markup(cost_price, markup_percent):
        """Selling Price = Cost Price x (1 + Markup% / 100)"""
        return cost_price * (1 + markup_percent / 100)

    @staticmethod
    def calculate_selling_price_from_margin(cost_price, margin_percent):
        """Selling Price = Cost Price / (1 - Margin% / 100)"""
        if margin_percent >= 100:
            return 0.0
        return cost_price / (1 - margin_percent / 100)

    @staticmethod
    def calculate_profit(cost_price, selling_price):
        """Profit = Selling Price - Cost Price"""
        return selling_price - cost_price

    # --- COST / PRICE PER SQUARE METER ---

    @staticmethod
    def calculate_cost_per_sqm(total_material_cost, area_m2):
        """Cost per m2 = Total Material Cost / Area (Width_m x Length_m)"""
        if area_m2 <= 0:
            return 0.0
        return total_material_cost / area_m2

    @staticmethod
    def calculate_order_quantity_from_sqm(cost_per_sqm, total_budget):
        """Area (m2) = Total Budget / Cost per m2"""
        if cost_per_sqm <= 0:
            return 0.0
        return total_budget / cost_per_sqm

    @staticmethod
    def calculate_total_cost_from_sqm(cost_per_sqm, area_m2):
        """Total Cost = Cost per m2 x Area (m2)"""
        return cost_per_sqm * area_m2

    # --- BREAKEVEN QUANTITY ---

    @staticmethod
    def calculate_breakeven_units(fixed_costs, selling_price_per_unit, variable_cost_per_unit):
        """
        Contribution Margin per Unit = Selling Price per Unit - Variable Cost per Unit
        Breakeven Units = Fixed Costs / Contribution Margin per Unit
        """
        contribution_margin = selling_price_per_unit - variable_cost_per_unit
        if contribution_margin <= 0:
            return 0.0
        return fixed_costs / contribution_margin

    # --- VAT / TAX INCLUSIVE-EXCLUSIVE ---

    @staticmethod
    def calculate_price_incl_vat(price_excl_vat, vat_percent):
        """Price incl. VAT = Price excl. VAT x (1 + VAT% / 100)"""
        return price_excl_vat * (1 + vat_percent / 100)

    @staticmethod
    def calculate_price_excl_vat(price_incl_vat, vat_percent):
        """Price excl. VAT = Price incl. VAT / (1 + VAT% / 100)"""
        if vat_percent <= -100:
            return 0.0
        return price_incl_vat / (1 + vat_percent / 100)

    # --- BULK / QUANTITY-BREAK DISCOUNT ---

    @staticmethod
    def calculate_discounted_price(base_price, discount_percent):
        """Discounted Price per Unit = Base Price x (1 - Discount% / 100)"""
        return base_price * (1 - discount_percent / 100)

    @staticmethod
    def calculate_bulk_tier_discount(quantity, tiers):
        """
        tiers: list of {'min_qty': X, 'discount_percent': Y}
        Returns the discount% of the highest tier the quantity qualifies for.
        """
        applicable_discount = 0.0
        for tier in sorted(tiers, key=lambda t: t['min_qty']):
            if quantity >= tier['min_qty']:
                applicable_discount = tier['discount_percent']
        return applicable_discount

    # --- LENGTH UNIT CONVERSION (for sqm and future length-based calculators) ---

    @staticmethod
    def convert_length_to_m(value, unit):
        """Convert a length value in the given unit to meters."""
        conversions = {'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'inch': 0.0254, 'ft': 0.3048}
        if unit not in conversions:
            raise ValueError(f"Invalid length unit: {unit}")
        return value * conversions[unit]
