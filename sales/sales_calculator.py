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
