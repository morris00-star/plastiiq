from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_home, name='sales_home'),

    # Calculation endpoints
    path('calculate-material-cost-kg/', views.calculate_material_cost_kg, name='calculate_material_cost_kg'),
    path('calculate-material-cost-meter/', views.calculate_material_cost_meter, name='calculate_material_cost_meter'),
    path('calculate-material-cost-piece/', views.calculate_material_cost_piece, name='calculate_material_cost_piece'),
    path('calculate-order-quantity-kg/', views.calculate_order_quantity_kg, name='calculate_order_quantity_kg'),
    path('calculate-order-quantity-meter/', views.calculate_order_quantity_meter,
         name='calculate_order_quantity_meter'),
    path('calculate-order-quantity-piece/', views.calculate_order_quantity_piece,
         name='calculate_order_quantity_piece'),
    path('calculate-roll-cost/', views.calculate_roll_cost, name='calculate_roll_cost'),
    path('calculate-laminated-cost/', views.calculate_laminated_cost, name='calculate_laminated_cost'),
]
